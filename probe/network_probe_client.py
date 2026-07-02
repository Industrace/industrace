#!/usr/bin/env python3
"""
Network probe runtime orchestrator for Industrace.

This module intentionally keeps orchestration/lifecycle logic while heavy
concerns are delegated to dedicated modules:
- `probe_packet_processing.py`: packet sampling, parsing pipeline, state updates
- `probe_runtime_workers.py`: heartbeat/transmission/config sync loops
- `probe_state_store.py`: local state persistence helpers
- `probe_transmission.py`: snapshot/payload builders
- `probe_metrics.py`: host/network metric calculators
- `probe_remote_config.py`: runtime-safe remote configuration application
"""

import sys
import time
import logging
import signal
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
from collections import deque

# Networking
import socket
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from scapy.all import sniff, IP

# System monitoring
import psutil

from probe_helpers import (
    combine_capture_filter,
    parse_state_datetime,
    sanitize_exception_message,
)
from probe_health import ProbeHealth
from probe_filtering import protocol_filters_from_names
from probe_models import ProbeConfiguration, NetworkConnection, NetworkDevice
from probe_packet_processing import ProbePacketProcessingMixin
from probe_metrics import get_network_metrics, get_system_metrics
from probe_remote_config import apply_remote_configuration
from probe_runtime_workers import ProbeRuntimeWorkersMixin
from probe_logging import setup_probe_logging
from probe_state_store import load_probe_state, save_probe_state
from probe_transmission import build_transmission_payload, snapshot_pending_discovery

# Logging setup (rotating file + stdout)
setup_probe_logging()
logger = logging.getLogger(__name__)

class NetworkProbe(ProbeRuntimeWorkersMixin, ProbePacketProcessingMixin):
    """Main probe coordinator (threads, IO, and shared runtime state)."""
    
    def __init__(self, config: ProbeConfiguration):
        self.config = config
        self.running = False
        self.stats = {
            'packets_captured': 0,
            'bytes_processed': 0,
            'devices_discovered': 0,
            'connections_detected': 0,
            'start_time': datetime.now()
        }

        # Batch counters to reduce synchronization overhead.
        # Only the sniffing thread updates these; other threads read aggregated values.
        self.stats_lock = threading.Lock()
        self._stats_batch_packets = 0
        self._stats_batch_bytes = 0
        self._stats_flush_batch_size = 2000
        self._stats_flush_max_seconds = 2.0
        self._last_stats_flush_ts = time.time()

        # Sampling rate snapshot (updated under config_lock on remote config changes).
        self._sampling_rate = self.config.sampling_rate

        # Sliding-window counters for near-real-time rates.
        # We keep 1-second buckets and compute averages over the last window.
        self._rate_window_seconds = 60
        # Safety: even if trimming fails for any reason, maxlen prevents unbounded growth.
        self._traffic_buckets = deque(maxlen=self._rate_window_seconds + 2)  # [epoch_sec, packets, bytes]
        self.rate_lock = threading.Lock()

        # Connection pruning to avoid unbounded growth (high-traffic / many ephemeral ports).
        self._connection_ttl_seconds = 15 * 60  # 15 minutes
        self._connection_prune_interval_seconds = 60  # prune at most once per minute
        self._last_connection_prune_ts = 0.0
        
        # Storage for devices and connections
        self.devices: Dict[str, NetworkDevice] = {}
        self.connections: Dict[str, NetworkConnection] = {}
        self._pending_device_macs = set()
        self._pending_new_connections = 0
        
        # Data transmission buffer
        self.data_buffer = deque(maxlen=1000)
        self._payload_buffer_dropped_count = 0
        
        # Threading
        self.sniffing_thread = None
        self.heartbeat_thread = None
        self.transmission_thread = None
        self.configuration_thread = None
        self._consecutive_auth_failures = 0
        self._heartbeat_failures = 0
        self._transmission_failures = 0
        self._transmission_wake = threading.Event()
        self.health = ProbeHealth()
        
        # Thread-safety lock
        self.data_lock = threading.Lock()
        self.config_lock = threading.Lock()
        self.data_buffer_lock = threading.Lock()

        # Separate capture filters: user-defined (e.g. subnet) and protocol-derived (remote).
        # We treat the initial config.capture_filter as the user-defined/base filter.
        self._user_capture_filter = self.config.capture_filter or None
        if self._user_capture_filter is not None and not str(self._user_capture_filter).strip():
            self._user_capture_filter = None
        self._protocol_capture_filter = None
        self._recompute_capture_filter_locked()

        # Local persistence (best-effort) to reduce "flood" after restarts.
        self._state_io_lock = threading.Lock()
        self._last_state_save_ts = 0.0
        self._state_save_interval_seconds = 60.0

        # Marker/version of the last applied remote configuration
        self.last_remote_config_marker = None
        self._last_successful_transmission_at: Optional[str] = None
        self._last_transmission_sent_ts = 0.0

        # HTTP session with retries for transient failures
        self.http = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST"),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.http.mount("http://", adapter)
        self.http.mount("https://", adapter)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def start(self):
        """Start the probe"""
        logger.info("Starting network probe...")
        
        try:
            # Validate configuration
            self._validate_config()

            # Best-effort: load persisted state (if enabled via config/state file).
            self._load_state_from_disk(best_effort=True)
            
            # Start main threads
            self.running = True
            
            # Sniffing thread
            self.sniffing_thread = threading.Thread(target=self._sniffing_worker, daemon=True)
            self.sniffing_thread.start()
            
            # Heartbeat thread
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
            self.heartbeat_thread.start()
            
            # Data transmission thread
            self.transmission_thread = threading.Thread(target=self._transmission_worker, daemon=True)
            self.transmission_thread.start()

            # Configuration sync thread (fleet-style)
            self.configuration_thread = threading.Thread(target=self._configuration_worker, daemon=True)
            self.configuration_thread.start()
            
            logger.info("Probe started successfully")
            
            # Main loop
            while self.running:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting the probe: {e}")
            self.stop()
    
    def stop(self):
        """Stop the probe"""
        logger.info("Stopping probe...")
        self.running = False

        # A worker can trigger stop() (e.g. auth failure path). Never join the
        # current thread, otherwise Python raises `RuntimeError`.
        current_thread = threading.current_thread()
        managed_threads = [
            self.sniffing_thread,
            self.heartbeat_thread,
            self.transmission_thread,
            self.configuration_thread,
        ]
        for thread in managed_threads:
            if thread and thread is not current_thread and thread.is_alive():
                thread.join(timeout=5)
        
        logger.info("Probe stopped")

    def _sanitize_exception_message(self, exc: Exception) -> str:
        """Avoid leaking sensitive data (e.g. API keys) in logs."""
        return sanitize_exception_message(exc, api_key=getattr(self.config, "api_key", None))

    def _probe_request_headers(self) -> Dict[str, str]:
        return {"X-API-Key": self.config.api_key}

    def _handle_probe_http_status(self, response, label: str) -> bool:
        if response.status_code == 200:
            self._consecutive_auth_failures = 0
            return True
        if response.status_code == 401:
            self._consecutive_auth_failures += 1
            logger.warning(
                "%s unauthorized (invalid or de-authorized API key); failures=%s",
                label,
                self._consecutive_auth_failures,
            )
            if self._consecutive_auth_failures >= 2:
                logger.error("Persistent probe auth failure — stopping client")
                self.stop()
            return False
        if response.status_code == 429:
            logger.warning("%s rate limited (HTTP 429)", label)
            return False
        logger.warning("%s failed: HTTP %s", label, response.status_code)
        return False

    def _signal_pending_delivery(self) -> None:
        """Wake the transmission worker when new discovery data is pending."""
        cooldown = float(self.config.data_transmission_interval)
        if time.time() - self._last_transmission_sent_ts < cooldown:
            return
        self._transmission_wake.set()

    def _recompute_capture_filter_locked(self):
        """
        Recompute self.config.capture_filter from user/protocol parts.
        Caller should hold config_lock if concurrent updates are possible.
        """
        self.config.capture_filter = combine_capture_filter(
            self._user_capture_filter,
            self._protocol_capture_filter,
        )

    def _parse_state_datetime(self, value: Any) -> datetime:
        return parse_state_datetime(value)

    def _load_state_from_disk(self, best_effort: bool = True):
        state_file = getattr(self.config, "state_file", None)
        if not state_file:
            return

        try:
            state = load_probe_state(
                state_file=state_file,
                parse_datetime=self._parse_state_datetime,
            )
            with self.data_lock:
                self.devices = state.devices
                self.connections = state.connections
                self._pending_device_macs = set(state.pending_device_macs)
                self._pending_new_connections = state.pending_new_connections
            self._last_successful_transmission_at = state.last_successful_transmission_at
        except Exception as e:
            if best_effort:
                logger.debug(f"Best-effort state load failed: {self._sanitize_exception_message(e)}")
                return
            raise

    def _maybe_save_state(self, best_effort: bool = True):
        state_file = getattr(self.config, "state_file", None)
        if not state_file:
            return

        now_ts = time.time()
        if now_ts - self._last_state_save_ts < self._state_save_interval_seconds:
            return

        self._last_state_save_ts = now_ts
        self._save_state_to_disk(best_effort=best_effort)

    def _save_state_to_disk(self, best_effort: bool = True):
        state_file = getattr(self.config, "state_file", None)
        if not state_file:
            return

        try:
            with self.data_lock:
                devices_copy = dict(self.devices)
                connections_copy = dict(self.connections)
                pending_macs_copy = set(self._pending_device_macs)
                pending_connections_copy = self._pending_new_connections
            save_probe_state(
                state_file=state_file,
                devices=devices_copy,
                connections=connections_copy,
                pending_device_macs=pending_macs_copy,
                pending_new_connections=pending_connections_copy,
                last_successful_transmission_at=self._last_successful_transmission_at,
            )
        except Exception as e:
            if best_effort:
                logger.debug(f"Best-effort state save failed: {self._sanitize_exception_message(e)}")
                return
            raise
    
    def _validate_config(self):
        """Validate configuration"""
        if not self.config.probe_id:
            raise ValueError("Probe ID not specified")
        try:
            uuid.UUID(str(self.config.probe_id))
        except ValueError as exc:
            raise ValueError("Probe ID must be a valid UUID string") from exc
        if not self.config.api_key:
            raise ValueError("API key not specified")
        if not self.config.server_url:
            raise ValueError("Server URL not specified")
        
        # Automatically detect the interface if not provided
        if not self.config.interface_name:
            self.config.interface_name = self._detect_network_interface()
            logger.info(f"Automatically detected interface: {self.config.interface_name}")
    
    def _detect_network_interface(self):
        """Automatically detect the primary network interface"""
        try:
            interfaces = psutil.net_if_addrs()
            for interface, addrs in interfaces.items():
                # Skip loopback and virtual interfaces
                if interface.startswith('lo') or interface.startswith('docker') or interface.startswith('br-'):
                    continue
                
                # Find interfaces with IP addresses
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                        logger.info(f"Detected interface: {interface} with IP {addr.address}")
                        return interface
            
            # Fallback to common interfaces
            for interface in ['ens224', 'eth0', 'enp0s3', 'wlan0']:
                if interface in interfaces:
                    logger.info(f"Using fallback interface: {interface}")
                    return interface
            
            return 'eth0'  # Last fallback
            
        except Exception as e:
            logger.warning(f"Error detecting interface: {e}")
            return 'eth0'
    
    def _sniffing_worker(self):
        """Packet sniffing worker"""
        logger.info(f"Starting packet sniffing on interface {self.config.interface_name}")
        last_sniff_cfg = None

        # Loop with timeout to allow clean stop and retry on errors
        while self.running:
            try:
                with self.config_lock:
                    iface = self.config.interface_name
                    filter_str = self.config.capture_filter if self.config.capture_filter else None
                    promisc = self.config.promiscuous_mode

                sniff_cfg = (iface, filter_str, promisc)
                if sniff_cfg != last_sniff_cfg:
                    logger.info(
                        f"Updated sniff configuration: iface={iface}, promisc={promisc}, "
                        f"filter={'<none>' if not filter_str else filter_str}"
                    )
                    last_sniff_cfg = sniff_cfg

                sniff(
                    iface=iface,
                    prn=self._packet_handler,
                    store=False,
                    filter=filter_str,
                    promisc=promisc,
                    timeout=10,
                )
            except Exception as e:
                self.health.record_error()
                logger.error(f"Error during sniffing: {e}")
                time.sleep(2)
    
    def set_subnet_filter(self, subnets: List[str]):
        """Set a filter for specific subnets"""
        with self.config_lock:
            if not subnets:
                self._user_capture_filter = None
                self._recompute_capture_filter_locked()
                logger.info("Subnet filter removed - capturing all traffic")
                return

            filter_parts = []
            for subnet in subnets:
                if '/' in subnet:
                    filter_parts.append(f"net {subnet}")
                else:
                    filter_parts.append(f"host {subnet}")

            self._user_capture_filter = " or ".join(filter_parts)
            self._recompute_capture_filter_locked()
        logger.info(f"Subnet filter set: {self.config.capture_filter}")
    
    def add_protocol_filter(self, protocols: List[str]):
        """Add protocol-derived BPF filters to the active capture filter."""
        if not protocols:
            return
        with self.config_lock:
            protocol_filters = protocol_filters_from_names(protocols)
            if protocol_filters:
                protocol_filter = " or ".join(protocol_filters)
                self._protocol_capture_filter = protocol_filter
                self._recompute_capture_filter_locked()
        logger.info(f"Protocol filter added: {self.config.capture_filter}")
    
    def _apply_remote_configuration(self, cfg: Dict[str, Any]) -> List[str]:
        """
        Apply runtime-safe parameters provided by the backend.
        Returns the list of fields that were actually modified.
        """
        with self.config_lock:
            changed_fields, new_protocol_filter = apply_remote_configuration(
                cfg=cfg,
                config=self.config,
                protocol_capture_filter=self._protocol_capture_filter,
                set_sampling_rate=lambda v: setattr(self, "_sampling_rate", v),
                rebuild_protocol_capture_filter=self._rebuild_protocol_capture_filter_unlocked,
            )
            if new_protocol_filter != self._protocol_capture_filter:
                self._protocol_capture_filter = new_protocol_filter
                self._recompute_capture_filter_locked()

            return changed_fields

    def _rebuild_protocol_capture_filter_unlocked(self, protocols: List[str]):
        """
        Rebuilds the capture_filter based on the protocol list.
        Preconditions: called under config_lock.
        """
        if not protocols:
            return

        protocol_filters = protocol_filters_from_names(protocols)

        if protocol_filters:
            self._protocol_capture_filter = " or ".join(protocol_filters)
        else:
            # If protocols were provided but none matched known cases,
            # clear the protocol-derived filter but keep the user-defined one.
            self._protocol_capture_filter = None

        self._recompute_capture_filter_locked()

    def _snapshot_discovery_state(self):
        """
        Build a reliable snapshot of discovery state to report.
        We send "dirty" devices tracked since the last successful transmission to
        avoid silent loss when retries are delayed.
        """
        with self.data_lock:
            return snapshot_pending_discovery(
                devices=self.devices,
                pending_device_macs=self._pending_device_macs,
                pending_new_connections=self._pending_new_connections,
            )

    def _build_transmission_payload(
        self,
        pending_devices: List[Dict[str, Any]],
        protocol_breakdown: Dict[str, int],
        new_connections_detected: int,
    ) -> Dict[str, Any]:
        """Serialize the transmission payload (JSON over HTTPS; TLS provides transport security)."""
        return build_transmission_payload(
            probe_id=self.config.probe_id,
            pending_devices=pending_devices,
            protocol_breakdown=protocol_breakdown,
            new_connections_detected=new_connections_detected,
        )

    def _maybe_prune_connections(self):
        """
        Best-effort cleanup of inactive connections.
        Helps limit memory growth when connection keys include ports/protocols.
        """
        now_ts = time.time()
        if now_ts - self._last_connection_prune_ts < self._connection_prune_interval_seconds:
            return

        self._last_connection_prune_ts = now_ts
        cutoff = datetime.now()
        threshold_seconds = self._connection_ttl_seconds

        with self.data_lock:
            to_delete = [
                key
                for key, conn in self.connections.items()
                if (cutoff - conn.last_seen).total_seconds() > threshold_seconds
            ]
            for key in to_delete:
                self.connections.pop(key, None)
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Retrieve system metrics"""
        try:
            return get_system_metrics()
        except Exception as e:
            logger.debug(f"Error retrieving system metrics: {e}")
            return {}
    
    def _get_network_metrics(self) -> Dict[str, Any]:
        """Retrieve network metrics"""
        try:
            with self.rate_lock:
                traffic_buckets = list(self._traffic_buckets)
            with self.data_lock:
                connections_copy = dict(self.connections)
                devices_copy = dict(self.devices)

            return get_network_metrics(
                traffic_buckets=traffic_buckets,
                rate_window_seconds=self._rate_window_seconds,
                connections=connections_copy,
                devices=devices_copy,
            )
        except Exception as e:
            logger.debug(f"Error retrieving network metrics: {e}")
            return {}
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

def load_config(config_file: str) -> ProbeConfiguration:
    """Compatibility wrapper for external imports."""
    from probe_cli import load_config as _load_config

    return _load_config(config_file)


def create_default_config(config_file: str):
    """Compatibility wrapper for external imports."""
    from probe_cli import create_default_config as _create_default_config

    return _create_default_config(config_file)


def main():
    """Compatibility CLI wrapper."""
    from probe_cli import main as _main

    return _main()


if __name__ == '__main__':
    main()
