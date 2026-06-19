#!/usr/bin/env python3
"""
Network Probe Client for Industrace
An "intelligent" network probe for industrial traffic analysis
a bit Bloatware but it works
"""

import os
import sys
import time
import json
import logging
import argparse
import signal
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import hashlib
import gzip
import base64
import re

# Networking
import socket
import struct
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from scapy.all import sniff, IP, TCP, UDP, ARP, ICMP, Ether, Raw

# System monitoring
import psutil
import platform

# Configuration
import configparser
from pathlib import Path

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('network_probe.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProbeConfiguration:
    """Probe configuration"""
    # Identification
    probe_id: str
    api_key: str
    server_url: str
    
    # Network configuration
    interface_name: str
    promiscuous_mode: bool = True
    capture_filter: Optional[str] = None
    max_packet_size: int = 1518
    buffer_size: int = 65536
    
    # Analysis configuration
    enabled_protocols: List[str] = None
    sampling_rate: float = 1.0
    metadata_extraction: bool = True
    payload_analysis: bool = False
    
    # Telecontrol configuration
    heartbeat_interval: int = 30
    data_transmission_interval: int = 300
    max_retry_attempts: int = 3
    
    # Security configuration
    encryption_enabled: bool = True
    ssl_verify: bool = True

    # Optional local persistence for probe restart.
    # When set, the probe loads previously discovered devices/connections and saves state periodically.
    state_file: Optional[str] = None
    
    def __post_init__(self):
        if self.enabled_protocols is None:
            self.enabled_protocols = []

@dataclass
class NetworkDevice:
    """Detected network device"""
    mac_address: str
    ip_addresses: List[str]
    first_seen: datetime
    last_seen: datetime
    protocols: List[str]
    packet_count: int
    byte_count: int
    vendor: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'mac_address': self.mac_address,
            'ip_addresses': self.ip_addresses,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'protocols': self.protocols,
            'packet_count': self.packet_count,
            'byte_count': self.byte_count,
            'vendor': self.vendor
        }

@dataclass
class NetworkConnection:
    """Detected network connection"""
    source_mac: str
    dest_mac: str
    source_ip: Optional[str]
    dest_ip: Optional[str]
    source_port: Optional[int]
    dest_port: Optional[int]
    protocol: str
    first_seen: datetime
    last_seen: datetime
    packet_count: int
    byte_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_mac': self.source_mac,
            'dest_mac': self.dest_mac,
            'source_ip': self.source_ip,
            'dest_ip': self.dest_ip,
            'source_port': self.source_port,
            'dest_port': self.dest_port,
            'protocol': self.protocol,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'packet_count': self.packet_count,
            'byte_count': self.byte_count
        }

class ProtocolAnalyzer:
    """Industrial protocol analyzer"""
    
    # Known ports for industrial protocols
    INDUSTRIAL_PORTS = {
        502: 'Modbus',
        2404: 'IEC 104',
        4840: 'OPC-UA',
        44818: 'EtherNet/IP',
        47808: 'BACnet',
        20000: 'DNP3',
        3671: 'KNX',
        1883: 'MQTT',
        8883: 'MQTT',
        80: 'HTTP',
        443: 'HTTPS',
        21: 'FTP',
        22: 'SSH',
        23: 'Telnet'
    }
    
    # Firmware signatures for device recognition
    DEVICE_SIGNATURES = {
        'siemens': [b'Siemens', b'S7', b'Simatic'],
        'rockwell': [b'Rockwell', b'Allen-Bradley', b'ControlLogix'],
        'schneider': [b'Schneider', b'Modicon', b'Quantum'],
        'abb': [b'ABB', b'800xA', b'Advant'],
        'honeywell': [b'Honeywell', b'Experion', b'PKS'],
        'emerson': [b'Emerson', b'DeltaV', b'PlantWeb']
    }
    
    @staticmethod
    def _normalize_protocol_key(protocol: str) -> str:
        return protocol.upper().replace(" ", "").replace("-", "").replace("_", "")

    @staticmethod
    def _mark_industrial_protocol(analysis: Dict[str, Any], port: int) -> None:
        if port not in ProtocolAnalyzer.INDUSTRIAL_PORTS:
            return
        proto_name = ProtocolAnalyzer.INDUSTRIAL_PORTS[port]
        analysis['industrial_protocol'] = True
        analysis['industrial_info'] = {
            'port': port,
            'protocol': proto_name,
        }
        if proto_name not in analysis['protocols']:
            analysis['protocols'].append(proto_name)

    @staticmethod
    def analyze_packet(packet) -> Dict[str, Any]:
        """Analyze a packet to extract protocol information"""
        analysis = {
            'protocols': [],
            'device_info': {},
            'industrial_protocol': False
        }
        
        try:
            # Layer 2 analysis (Ethernet)
            if Ether in packet:
                analysis['protocols'].append('Ethernet')
                
                # ARP analysis
                if ARP in packet:
                    analysis['protocols'].append('ARP')
                    analysis['arp_info'] = {
                        'op': packet[ARP].op,
                        'src_ip': packet[ARP].psrc,
                        'dst_ip': packet[ARP].pdst
                    }
            
            # Layer 3 analysis (IP)
            if IP in packet:
                analysis['protocols'].append('IP')
                analysis['ip_info'] = {
                    'src_ip': packet[IP].src,
                    'dst_ip': packet[IP].dst,
                    'ttl': packet[IP].ttl,
                    'protocol': packet[IP].proto
                }
                
                # TCP analysis
                if TCP in packet:
                    analysis['protocols'].append('TCP')
                    src_port = packet[TCP].sport
                    dst_port = packet[TCP].dport
                    
                    # Check industrial ports
                    if src_port in ProtocolAnalyzer.INDUSTRIAL_PORTS:
                        ProtocolAnalyzer._mark_industrial_protocol(analysis, src_port)
                    elif dst_port in ProtocolAnalyzer.INDUSTRIAL_PORTS:
                        ProtocolAnalyzer._mark_industrial_protocol(analysis, dst_port)
                    
                    # Payload analysis for specific protocols
                    if Raw in packet:
                        payload = bytes(packet[Raw])
                        analysis.update(ProtocolAnalyzer._analyze_payload(payload))
                
                # UDP analysis
                elif UDP in packet:
                    analysis['protocols'].append('UDP')
                    src_port = packet[UDP].sport
                    dst_port = packet[UDP].dport
                    
                    # Check industrial ports
                    if src_port in ProtocolAnalyzer.INDUSTRIAL_PORTS:
                        ProtocolAnalyzer._mark_industrial_protocol(analysis, src_port)
                    elif dst_port in ProtocolAnalyzer.INDUSTRIAL_PORTS:
                        ProtocolAnalyzer._mark_industrial_protocol(analysis, dst_port)
                
                # ICMP analysis
                elif ICMP in packet:
                    analysis['protocols'].append('ICMP')
                    analysis['icmp_info'] = {
                        'type': packet[ICMP].type,
                        'code': packet[ICMP].code
                    }
        
        except Exception as e:
            logger.debug(f"Error analyzing packet: {e}")
        
        return analysis
    
    @staticmethod
    def _analyze_payload(payload: bytes) -> Dict[str, Any]:
        """Analyze the payload to identify industrial protocols"""
        analysis = {}
        
        try:
            # Modbus recognition
            # Modbus TCP frame: MBAP (7 bytes) + Unit ID (1 byte at [6]) + Function Code (1 byte at [7])
            if len(payload) >= 8:
                function_code = payload[7]
                transaction_id = struct.unpack('>H', payload[0:2])[0]
                if function_code in [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x0F, 0x10]:
                    analysis['modbus_info'] = {
                        'function_code': function_code,
                        'transaction_id': transaction_id
                    }
            
            # OPC-UA recognition
            if len(payload) >= 4 and payload[0:4] == b'HELF':
                analysis['opcua_info'] = {
                    'message_type': 'Hello'
                }
            
            # EtherNet/IP recognition
            if len(payload) >= 24 and payload[0:2] == b'\x65\x00':
                analysis['enip_info'] = {
                    'command': struct.unpack('>H', payload[16:18])[0]
                }

            # IEC 60870-5-104 APCI: start byte 0x68, length, repeated 0x68
            if len(payload) >= 6 and payload[0] == 0x68 and payload[2] == 0x68:
                apdu_length = payload[1]
                analysis['iec104_info'] = {
                    'apdu_length': apdu_length,
                }
                analysis['industrial_protocol'] = True
                if 'IEC 104' not in analysis.get('protocols', []):
                    analysis.setdefault('protocols', []).append('IEC 104')
            
            # Vendor device recognition
            for vendor, signatures in ProtocolAnalyzer.DEVICE_SIGNATURES.items():
                for signature in signatures:
                    if signature in payload:
                        analysis['device_vendor'] = vendor
                        break
                if 'device_vendor' in analysis:
                    break
        
        except Exception as e:
            logger.debug(f"Error analyzing payload: {e}")
        
        return analysis

class NetworkProbe:
    """Main network probe"""
    
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
        
        # Data transmission buffer
        self.data_buffer = deque(maxlen=1000)
        
        # Threading
        self.sniffing_thread = None
        self.heartbeat_thread = None
        self.transmission_thread = None
        self.configuration_thread = None
        self._consecutive_auth_failures = 0
        
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
        
        # Wait for thread completion
        if self.sniffing_thread:
            self.sniffing_thread.join(timeout=5)
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        if self.transmission_thread:
            self.transmission_thread.join(timeout=5)
        if self.configuration_thread:
            self.configuration_thread.join(timeout=5)
        
        logger.info("Probe stopped")

    def _sanitize_exception_message(self, exc: Exception) -> str:
        """
        Avoid leaking sensitive data (e.g. API keys) in logs.
        """
        try:
            msg = str(exc)
        except Exception:
            msg = repr(exc)

        try:
            msg = re.sub(r"api_key=[^&\\s]+", "api_key=***", msg)
        except Exception:
            pass

        # Extra safety: if the exact key appears in the message, replace it.
        api_key = getattr(self.config, "api_key", None)
        if api_key and api_key in msg:
            msg = msg.replace(api_key, "***")
        return msg

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

    def _recompute_capture_filter_locked(self):
        """
        Recompute self.config.capture_filter from user/protocol parts.
        Caller should hold config_lock if concurrent updates are possible.
        """
        if self._user_capture_filter and self._protocol_capture_filter:
            self.config.capture_filter = f"({self._user_capture_filter}) and ({self._protocol_capture_filter})"
        elif self._protocol_capture_filter:
            self.config.capture_filter = self._protocol_capture_filter
        else:
            self.config.capture_filter = self._user_capture_filter

    def _parse_state_datetime(self, value: Any) -> datetime:
        if not value:
            return datetime.now()
        if isinstance(value, datetime):
            dt = value
        else:
            # Support both naive ISO timestamps and ISO with timezone (e.g. "+00:00" or "Z").
            s = str(value)
            if s.endswith("Z"):
                s = s.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)

        # Ensure we end up with a naive datetime so subtraction with datetime.now() works.
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    def _load_state_from_disk(self, best_effort: bool = True):
        state_file = getattr(self.config, "state_file", None)
        if not state_file:
            return

        try:
            path = Path(state_file)
            if not path.exists():
                return

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f) or {}

            devices_data = data.get("devices") or {}
            connections_data = data.get("connections") or {}

            now = datetime.now()
            with self.data_lock:
                self.devices = {}
                for mac, d in devices_data.items():
                    try:
                        self.devices[mac] = NetworkDevice(
                            mac_address=str(d.get("mac_address") or mac),
                            ip_addresses=list(d.get("ip_addresses") or []),
                            first_seen=self._parse_state_datetime(d.get("first_seen") or now.isoformat()),
                            last_seen=self._parse_state_datetime(d.get("last_seen") or now.isoformat()),
                            protocols=list(d.get("protocols") or []),
                            packet_count=int(d.get("packet_count") or 0),
                            byte_count=int(d.get("byte_count") or 0),
                            vendor=d.get("vendor"),
                        )
                    except Exception:
                        # Skip malformed device entries.
                        continue

                self.connections = {}
                for conn_key, d in connections_data.items():
                    try:
                        self.connections[conn_key] = NetworkConnection(
                            source_mac=str(d.get("source_mac") or ""),
                            dest_mac=str(d.get("dest_mac") or ""),
                            source_ip=d.get("source_ip"),
                            dest_ip=d.get("dest_ip"),
                            source_port=d.get("source_port"),
                            dest_port=d.get("dest_port"),
                            protocol=str(d.get("protocol") or "Unknown"),
                            first_seen=self._parse_state_datetime(d.get("first_seen") or now.isoformat()),
                            last_seen=self._parse_state_datetime(d.get("last_seen") or now.isoformat()),
                            packet_count=int(d.get("packet_count") or 0),
                            byte_count=int(d.get("byte_count") or 0),
                        )
                    except Exception:
                        continue
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
                devices_payload = {mac: dev.to_dict() for mac, dev in self.devices.items()}
                connections_payload = {k: c.to_dict() for k, c in self.connections.items()}

            payload = {
                "version": 1,
                "saved_at": datetime.now().isoformat(),
                "devices": devices_payload,
                "connections": connections_payload,
            }

            path = Path(state_file)
            path.parent.mkdir(parents=True, exist_ok=True)

            tmp_path = str(path) + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)

            os.replace(tmp_path, str(path))
        except Exception as e:
            if best_effort:
                logger.debug(f"Best-effort state save failed: {self._sanitize_exception_message(e)}")
                return
            raise
    
    def _validate_config(self):
        """Validate configuration"""
        if not self.config.probe_id:
            raise ValueError("Probe ID not specified")
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
                logger.error(f"Error during sniffing: {e}")
                time.sleep(2)
    
    def set_subnet_filter(self, subnets: List[str]):
        """Set a filter for specific subnets"""
        if not subnets:
            self._user_capture_filter = None
            self._recompute_capture_filter_locked()
            logger.info("Subnet filter removed - capturing all traffic")
            return
        
        # Build a BPF filter for subnets
        filter_parts = []
        for subnet in subnets:
            if '/' in subnet:
                # CIDR format: 192.168.1.0/24
                filter_parts.append(f"net {subnet}")
            else:
                # Single IP: 192.168.1.1
                filter_parts.append(f"host {subnet}")
        
        self._user_capture_filter = " or ".join(filter_parts)
        self._recompute_capture_filter_locked()
        logger.info(f"Subnet filter set: {self.config.capture_filter}")
    
    def add_protocol_filter(self, protocols: List[str]):
        """Add filters for specific protocols"""
        if not protocols:
            return
        
        protocol_filters = []
        for protocol in protocols:
            key = ProtocolAnalyzer._normalize_protocol_key(protocol)
            if key == 'MODBUS':
                protocol_filters.append("tcp port 502")
            elif key == 'IEC104':
                protocol_filters.append("tcp port 2404")
            elif key == 'OPCUA':
                protocol_filters.append("tcp port 4840")
            elif key == 'ETHERNET/IP':
                protocol_filters.append("tcp port 44818 or udp port 2222")
            elif key == 'BACNET':
                protocol_filters.append("udp port 47808")
            elif key == 'DNP3':
                protocol_filters.append("tcp port 20000")
            elif key == 'KNX':
                protocol_filters.append("udp port 3671")
            elif key == 'MQTT':
                protocol_filters.append("tcp port 1883 or tcp port 8883")
        
        if protocol_filters:
            protocol_filter = " or ".join(protocol_filters)
            self._protocol_capture_filter = protocol_filter
            self._recompute_capture_filter_locked()
            logger.info(f"Protocol filter added: {self.config.capture_filter}")
    
    def _packet_handler(self, packet):
        """Handle each captured packet"""
        try:
            # Lightweight logging: every 10k packets
            if self.stats['packets_captured'] and self.stats['packets_captured'] % 10000 == 0:
                logger.info(f"Processed packets: {self.stats['packets_captured']}")
            
            # Sampling when enabled
            if self._sampling_rate < 1.0:
                # Use a deterministic hash based on packet fields
                # to avoid Python's randomized hash() behavior between runs.
                try:
                    src_mac = packet[Ether].src if Ether in packet else ""
                    dst_mac = packet[Ether].dst if Ether in packet else ""
                    src_ip = packet[IP].src if IP in packet else ""
                    dst_ip = packet[IP].dst if IP in packet else ""

                    if TCP in packet:
                        l4_proto = "TCP"
                        sport = packet[TCP].sport
                        dport = packet[TCP].dport
                    elif UDP in packet:
                        l4_proto = "UDP"
                        sport = packet[UDP].sport
                        dport = packet[UDP].dport
                    else:
                        l4_proto = "OTHER"
                        sport = ""
                        dport = ""

                    ip_proto = packet[IP].proto if IP in packet else ""
                    pkt_len = len(packet)
                    sample_key = f"{src_mac}|{dst_mac}|{src_ip}|{dst_ip}|{l4_proto}|{ip_proto}|{sport}|{dport}|{pkt_len}"

                    digest = hashlib.md5(sample_key.encode("utf-8")).digest()
                    value = int.from_bytes(digest[:4], "big")

                    buckets = 10000
                    threshold = int(self._sampling_rate * buckets)
                    if (value % buckets) >= threshold:
                        return
                except Exception:
                    # If anything goes wrong while sampling, do not drop the packet.
                    pass
            
            # Update statistics
            bytes_delta = len(packet[IP]) if IP in packet else 0
            self._stats_batch_packets += 1
            self._stats_batch_bytes += bytes_delta

            now_ts = time.time()
            if (
                self._stats_batch_packets >= self._stats_flush_batch_size
                or (now_ts - self._last_stats_flush_ts) >= self._stats_flush_max_seconds
            ):
                with self.stats_lock:
                    self.stats['packets_captured'] += self._stats_batch_packets
                    self.stats['bytes_processed'] += self._stats_batch_bytes
                self._stats_batch_packets = 0
                self._stats_batch_bytes = 0
                self._last_stats_flush_ts = now_ts

            # Update sliding-window buckets for real-time throughput.
            now_sec = int(time.time())
            with self.rate_lock:
                if not self._traffic_buckets or self._traffic_buckets[-1][0] != now_sec:
                    self._traffic_buckets.append([now_sec, 0, 0])
                self._traffic_buckets[-1][1] += 1
                self._traffic_buckets[-1][2] += bytes_delta

                cutoff = now_sec - self._rate_window_seconds + 1
                while self._traffic_buckets and self._traffic_buckets[0][0] < cutoff:
                    self._traffic_buckets.popleft()
            
            # Analyze packet
            if self.config.metadata_extraction:
                analysis = ProtocolAnalyzer.analyze_packet(packet)
                self._process_packet_analysis(packet, analysis)
            
            # Extract payload if enabled
            if self.config.payload_analysis and Raw in packet:
                self._process_payload(packet)

            # Periodically prune inactive connections.
            # This runs best-effort and avoids unbounded growth.
            self._maybe_prune_connections()
        
        except Exception as e:
            logger.debug(f"Error handling packet: {e}")
    
    def _process_packet_analysis(self, packet, analysis: Dict[str, Any]):
        """Process packet analysis results"""
        try:
            # Extract base information
            if Ether in packet:
                src_mac = packet[Ether].src
                dst_mac = packet[Ether].dst
                
                # Update devices
                src_ip = packet[IP].src if IP in packet else None
                dst_ip = packet[IP].dst if IP in packet else None
                self._update_device(src_mac, src_ip, packet, analysis)
                self._update_device(dst_mac, dst_ip, packet, analysis)
                
                # Update connections
                self._update_connection(src_mac, dst_mac, packet, analysis)
        
        except Exception as e:
            logger.debug(f"Error processing packet analysis: {e}")
    
    def _update_device(self, mac: str, ip: Optional[str], packet, analysis: Dict[str, Any]):
        """Update information for a device"""
        with self.data_lock:
            if mac not in self.devices:
                logger.debug(f"Creating new device with MAC {mac}")
                self.devices[mac] = NetworkDevice(
                    mac_address=mac,
                    ip_addresses=[],
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    protocols=[],
                    packet_count=0,
                    byte_count=0
                )
                with self.stats_lock:
                    self.stats['devices_discovered'] += 1
            
            device = self.devices[mac]
            device.last_seen = datetime.now()
            device.packet_count += 1
            
            # Add IP if present (mapped from src/dst MAC)
            if ip and ip not in device.ip_addresses:
                device.ip_addresses.append(ip)

            if IP in packet:
                device.byte_count += len(packet[IP])
            
            # Add protocols
            for protocol in analysis.get('protocols', []):
                if protocol not in device.protocols:
                    device.protocols.append(protocol)
            
            # Add vendor if identified
            if 'device_vendor' in analysis:
                device.vendor = analysis['device_vendor']
    
    def _update_connection(self, src_mac: str, dst_mac: str, packet, analysis: Dict[str, Any]):
        """Update information for a connection (directional flow key)."""
        with self.data_lock:
            # Determine L4 protocol and ports for a more accurate connection key.
            if TCP in packet:
                proto = "TCP"
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
            elif UDP in packet:
                proto = "UDP"
                src_port = packet[UDP].sport
                dst_port = packet[UDP].dport
            elif ICMP in packet:
                proto = "ICMP"
                src_port = None
                dst_port = None
            else:
                proto = "OTHER"
                src_port = None
                dst_port = None

            # Use direction + L4 tuple in the key to avoid collapsing different flows.
            conn_key = f"{src_mac}->{dst_mac}|{proto}|{src_port if src_port is not None else ''}|{dst_port if dst_port is not None else ''}"

            if conn_key not in self.connections:
                self.connections[conn_key] = NetworkConnection(
                    source_mac=src_mac,
                    dest_mac=dst_mac,
                    source_ip=None,
                    dest_ip=None,
                    source_port=src_port,
                    dest_port=dst_port,
                    protocol=proto,
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    packet_count=0,
                    byte_count=0,
                )
                with self.stats_lock:
                    self.stats['connections_detected'] += 1

            conn = self.connections[conn_key]
            conn.last_seen = datetime.now()
            conn.packet_count += 1
            conn.protocol = proto
            conn.source_port = src_port
            conn.dest_port = dst_port

            # Update IP association if we can map IPs to known devices.
            if IP in packet:
                src_device = self.devices.get(src_mac)
                dst_device = self.devices.get(dst_mac)
                src_ip = packet[IP].src
                dst_ip = packet[IP].dst

                if src_device and src_ip in (src_device.ip_addresses or []):
                    conn.source_ip = src_ip
                if dst_device and dst_ip in (dst_device.ip_addresses or []):
                    conn.dest_ip = dst_ip

                conn.byte_count += len(packet[IP])
    
    def _process_payload(self, packet):
        """Process the packet payload"""
        try:
            if Raw in packet:
                payload = bytes(packet[Raw])
                
                # Compress and store in the buffer
                compressed = gzip.compress(payload)
                encoded = base64.b64encode(compressed).decode('utf-8')
                
                payload_info = {
                    'timestamp': datetime.now().isoformat(),
                    'src_mac': packet[Ether].src if Ether in packet else None,
                    'dst_mac': packet[Ether].dst if Ether in packet else None,
                    'payload': encoded,
                    'original_size': len(payload),
                    'compressed_size': len(compressed)
                }
                
                with self.data_buffer_lock:
                    self.data_buffer.append(payload_info)
        
        except Exception as e:
            logger.debug(f"Error processing payload: {e}")
    
    def _heartbeat_worker(self):
        """Heartbeat sender worker"""
        logger.info("Starting heartbeat worker")
        
        while self.running:
            try:
                self._send_heartbeat()
                time.sleep(self.config.heartbeat_interval)
            except Exception as e:
                logger.error(f"Error sending heartbeat: {self._sanitize_exception_message(e)}")
                time.sleep(5)  # More frequent retry on error
    
    def _send_heartbeat(self):
        """Send heartbeat to the server"""
        try:
            # Compute metrics once to avoid blocking multiple times.
            system_metrics = self._get_system_metrics()
            network_metrics = self._get_network_metrics()

            # Prepare heartbeat data
            heartbeat_data = {
                'probe_id': self.config.probe_id,
                'status': 'healthy',
                'cpu_usage': system_metrics.get('cpu_usage', 0.0),
                'memory_usage': system_metrics.get('memory_usage', 0.0),
                'disk_usage': system_metrics.get('disk_usage', 0.0),
                'packets_per_second': network_metrics.get('packets_per_second', 0.0),
                'bytes_per_second': network_metrics.get('bytes_per_second', 0.0),
                'active_connections': network_metrics.get('active_connections', 0),
                'error_count': 0,
                'warning_count': 0
            }
            
            # Send to the server
            response = self.http.post(
                f"{self.config.server_url}/api/network-probes/heartbeat",
                headers=self._probe_request_headers(),
                json=heartbeat_data,
                timeout=10,
                verify=self.config.ssl_verify
            )
            
            if self._handle_probe_http_status(response, "Heartbeat"):
                logger.debug("Heartbeat sent successfully")
            elif response.status_code == 429:
                time.sleep(min(60, self.config.heartbeat_interval))
        
        except Exception as e:
            logger.error(f"Error sending heartbeat: {self._sanitize_exception_message(e)}")
    
    def _transmission_worker(self):
        """Data transmission worker"""
        logger.info("Starting data transmission worker")
        
        while self.running:
            try:
                self._send_data_transmission()
                time.sleep(self.config.data_transmission_interval)
            except Exception as e:
                logger.error(f"Error transmitting data: {self._sanitize_exception_message(e)}")
                time.sleep(30)  # More frequent retry on error

    def _configuration_worker(self):
        """
        Worker to synchronize configuration from the backend.
        Enables a first fleet-management approach: the probe adopts parameters
        set in the console without requiring a new deployment.
        """
        logger.info("Starting configuration sync worker")

        while self.running:
            try:
                self._sync_remote_configuration()
            except Exception as e:
                logger.error(f"Error syncing remote configuration: {self._sanitize_exception_message(e)}")

            # Moderate polling; in the future it may become configurable
            time.sleep(30)

    def _sync_remote_configuration(self):
        """Fetch and apply the remote configuration if updated."""
        try:
            response = self.http.get(
                f"{self.config.server_url}/api/network-probes/configuration/{self.config.probe_id}",
                headers=self._probe_request_headers(),
                timeout=10,
                verify=self.config.ssl_verify
            )

            if response.status_code == 200:
                payload = response.json() or {}
                marker = payload.get("last_update") or payload.get("version")
                config_payload = payload.get("configuration") or {}

                # Avoid re-applying the same configuration repeatedly
                if marker and marker == self.last_remote_config_marker:
                    return

                changed = self._apply_remote_configuration(config_payload)
                self.last_remote_config_marker = marker

                if changed:
                    logger.info(f"Remote configuration applied ({len(changed)} fields): {', '.join(changed)}")
            elif response.status_code == 401:
                self._consecutive_auth_failures += 1
                logger.warning(
                    "Remote configuration unauthorized (invalid or de-authorized API key); failures=%s",
                    self._consecutive_auth_failures,
                )
                if self._consecutive_auth_failures >= 2:
                    logger.error("Persistent probe auth failure — stopping client")
                    self.stop()
            else:
                logger.warning(f"Remote configuration sync failed: HTTP {response.status_code}")
        except Exception as e:
            logger.debug(f"Error fetching remote configuration: {self._sanitize_exception_message(e)}")

    def _apply_remote_configuration(self, cfg: Dict[str, Any]) -> List[str]:
        """
        Apply runtime-safe parameters provided by the backend.
        Returns the list of fields that were actually modified.
        """
        changed_fields: List[str] = []

        def to_int(v, default):
            try:
                return int(v)
            except Exception:
                return default

        def to_float(v, default):
            try:
                return float(v)
            except Exception:
                return default

        def to_bool(v, default):
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                return v.lower() in ("1", "true", "yes", "on")
            return default

        with self.config_lock:
            # Sniffing/runtime parameters
            if "interface_name" in cfg and cfg["interface_name"] and cfg["interface_name"] != self.config.interface_name:
                self.config.interface_name = str(cfg["interface_name"])
                changed_fields.append("interface_name")

            if "promiscuous_mode" in cfg:
                new_val = to_bool(cfg["promiscuous_mode"], self.config.promiscuous_mode)
                if new_val != self.config.promiscuous_mode:
                    self.config.promiscuous_mode = new_val
                    changed_fields.append("promiscuous_mode")

            if "capture_filter" in cfg:
                new_val = cfg["capture_filter"] or None
                if new_val != self._protocol_capture_filter:
                    self._protocol_capture_filter = new_val
                    changed_fields.append("capture_filter")
                    self._recompute_capture_filter_locked()

            # Analysis/telecontrol parameters
            if "sampling_rate" in cfg:
                new_val = max(0.01, min(1.0, to_float(cfg["sampling_rate"], self.config.sampling_rate)))
                if new_val != self.config.sampling_rate:
                    self.config.sampling_rate = new_val
                    self._sampling_rate = new_val
                    changed_fields.append("sampling_rate")

            if "metadata_extraction" in cfg:
                new_val = to_bool(cfg["metadata_extraction"], self.config.metadata_extraction)
                if new_val != self.config.metadata_extraction:
                    self.config.metadata_extraction = new_val
                    changed_fields.append("metadata_extraction")

            if "payload_analysis" in cfg:
                new_val = to_bool(cfg["payload_analysis"], self.config.payload_analysis)
                if new_val != self.config.payload_analysis:
                    self.config.payload_analysis = new_val
                    changed_fields.append("payload_analysis")

            if "heartbeat_interval" in cfg:
                new_val = max(10, min(300, to_int(cfg["heartbeat_interval"], self.config.heartbeat_interval)))
                if new_val != self.config.heartbeat_interval:
                    self.config.heartbeat_interval = new_val
                    changed_fields.append("heartbeat_interval")

            if "data_transmission_interval" in cfg:
                new_val = max(15, min(3600, to_int(cfg["data_transmission_interval"], self.config.data_transmission_interval)))
                if new_val != self.config.data_transmission_interval:
                    self.config.data_transmission_interval = new_val
                    changed_fields.append("data_transmission_interval")

            if "max_retry_attempts" in cfg:
                new_val = max(1, min(10, to_int(cfg["max_retry_attempts"], self.config.max_retry_attempts)))
                if new_val != self.config.max_retry_attempts:
                    self.config.max_retry_attempts = new_val
                    changed_fields.append("max_retry_attempts")

            # Optional: adopt enabled protocols from the console, converted to a BPF filter
            if "enabled_protocols" in cfg and isinstance(cfg["enabled_protocols"], list):
                new_protocols = [str(p) for p in cfg["enabled_protocols"] if str(p).strip()]
                if new_protocols != self.config.enabled_protocols:
                    self.config.enabled_protocols = new_protocols
                    changed_fields.append("enabled_protocols")
                    self._rebuild_protocol_capture_filter_unlocked(new_protocols)

        return changed_fields

    def _rebuild_protocol_capture_filter_unlocked(self, protocols: List[str]):
        """
        Rebuilds the capture_filter based on the protocol list.
        Preconditions: called under config_lock.
        """
        if not protocols:
            return

        protocol_filters = []
        for protocol in protocols:
            p = ProtocolAnalyzer._normalize_protocol_key(protocol)
            if p == "MODBUS":
                protocol_filters.append("tcp port 502")
            elif p == "IEC104":
                protocol_filters.append("tcp port 2404")
            elif p == "OPCUA":
                protocol_filters.append("tcp port 4840")
            elif p == "ETHERNET/IP":
                protocol_filters.append("tcp port 44818 or udp port 2222")
            elif p == "BACNET":
                protocol_filters.append("udp port 47808")
            elif p == "DNP3":
                protocol_filters.append("tcp port 20000")
            elif p == "KNX":
                protocol_filters.append("udp port 3671")
            elif p == "MQTT":
                protocol_filters.append("tcp port 1883 or tcp port 8883")
            elif p == "HTTP":
                protocol_filters.append("tcp port 80")
            elif p == "HTTPS":
                protocol_filters.append("tcp port 443")

        if protocol_filters:
            self._protocol_capture_filter = " or ".join(protocol_filters)
        else:
            # If protocols were provided but none matched known cases,
            # clear the protocol-derived filter but keep the user-defined one.
            self._protocol_capture_filter = None

        self._recompute_capture_filter_locked()

    def _snapshot_discovery_state(self):
        """
        Build an in-memory snapshot of discovery state to report.
        Kept separate from serialization/HTTP to avoid holding locks during network calls.
        """
        with self.data_lock:
            current_time = datetime.now()

            recent_devices = []
            for device in self.devices.values():
                if (current_time - device.last_seen).total_seconds() < 300:
                    recent_devices.append({
                        'mac_address': device.mac_address,
                        'ip_addresses': list(device.ip_addresses or []),
                        'protocols': list(device.protocols or []),
                        'packet_count': device.packet_count,
                        'vendor': device.vendor,
                        'first_seen': device.first_seen.isoformat(),
                        'last_seen': device.last_seen.isoformat(),
                    })

            protocol_breakdown = {}
            for device in self.devices.values():
                for protocol in device.protocols or []:
                    protocol_breakdown[protocol] = protocol_breakdown.get(protocol, 0) + device.packet_count

            new_connections_detected = len([
                c
                for c in self.connections.values()
                if (current_time - c.last_seen).total_seconds() < 300
            ])

        return recent_devices, protocol_breakdown, new_connections_detected

    def _build_transmission_payload(
        self,
        recent_devices: List[Dict[str, Any]],
        protocol_breakdown: Dict[str, int],
        new_connections_detected: int,
    ) -> Dict[str, Any]:
        """Serialize the transmission payload (JSON over HTTPS; TLS provides transport security)."""
        transmission_data: Dict[str, Any] = {
            'probe_id': self.config.probe_id,
            'transmission_type': 'metadata',
            'data_size': 0,
            'new_devices_discovered': len(recent_devices),
            'new_connections_detected': new_connections_detected,
            'protocol_breakdown': protocol_breakdown,
            # Used by backend upsert.
            'discovered_devices': recent_devices,
            'status': 'success',
            'encryption_used': False,
        }

        raw_json = json.dumps(transmission_data)
        transmission_data["data_size"] = len(raw_json)
        return transmission_data

    def _post_data_transmission(self, transmission_data: Dict[str, Any]):
        """Send a prepared payload to the backend."""
        return self.http.post(
            f"{self.config.server_url}/api/network-probes/data-transmission",
            headers=self._probe_request_headers(),
            json=transmission_data,
            timeout=30,
            verify=self.config.ssl_verify,
        )
    
    def _send_data_transmission(self):
        """Send data transmission to the server"""
        try:
            recent_devices, protocol_breakdown, new_connections_detected = self._snapshot_discovery_state()
            transmission_data = self._build_transmission_payload(
                recent_devices=recent_devices,
                protocol_breakdown=protocol_breakdown,
                new_connections_detected=new_connections_detected,
            )
            response = self._post_data_transmission(transmission_data)

            if self._handle_probe_http_status(response, "Data transmission"):
                logger.info("Data transmission sent successfully")
                # Clear the buffer after successful transmission.
                # data_buffer is only used for optional payload storage,
                # so losing some entries during race conditions is acceptable.
                with self.data_buffer_lock:
                    self.data_buffer.clear()
                # Best-effort persistence to reduce "new devices" flood on restart.
                self._maybe_save_state(best_effort=True)
            elif response.status_code == 429:
                time.sleep(120)
        
        except Exception as e:
            logger.error(f"Error transmitting data: {self._sanitize_exception_message(e)}")

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
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'platform': platform.platform(),
                'python_version': platform.python_version()
            }
        except Exception as e:
            logger.debug(f"Error retrieving system metrics: {e}")
            return {}
    
    def _get_network_metrics(self) -> Dict[str, Any]:
        """Retrieve network metrics"""
        try:
            # Rates over a sliding window (avoid cumulative averages).
            with self.rate_lock:
                packets_window = sum(b[1] for b in self._traffic_buckets)
                bytes_window = sum(b[2] for b in self._traffic_buckets)

            # Active connections / unique devices snapshot.
            now = datetime.now()
            with self.data_lock:
                active_connections = len([
                    conn for conn in self.connections.values()
                    if (now - conn.last_seen).total_seconds() < 300
                ])
                unique_devices = len(self.devices)

            window = max(1, int(self._rate_window_seconds))
            return {
                'packets_per_second': packets_window / window,
                'bytes_per_second': bytes_window / window,
                'active_connections': active_connections,
                'unique_devices': unique_devices,
            }
        except Exception as e:
            logger.debug(f"Error retrieving network metrics: {e}")
            return {}
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

def load_config(config_file: str) -> ProbeConfiguration:
    """Load configuration from a file"""
    config = configparser.ConfigParser()
    config.read(config_file)
    
    if 'main' not in config:
        raise ValueError("Missing required [main] section in config file")

    main_section = config['main']

    network_section = config['network'] if 'network' in config else {}
    analysis_section = config['analysis'] if 'analysis' in config else {}
    telecontrol_section = config['telecontrol'] if 'telecontrol' in config else {}
    security_section = config['security'] if 'security' in config else {}

    probe_id = main_section.get('probe_id', '')
    api_key = main_section.get('api_key', '')
    server_url = main_section.get('server_url', '')
    if not probe_id:
        raise ValueError("Missing required config value: [main] probe_id")
    if not api_key:
        raise ValueError("Missing required config value: [main] api_key")
    if not server_url:
        raise ValueError("Missing required config value: [main] server_url")

    interface_name = network_section.get('interface_name', 'eth0')
    promiscuous_mode = config.getboolean('network', 'promiscuous_mode', fallback=True) if 'network' in config else True
    capture_filter = config.get('network', 'capture_filter', fallback=None) if 'network' in config else None
    max_packet_size = config.getint('network', 'max_packet_size', fallback=1518) if 'network' in config else 1518
    buffer_size = config.getint('network', 'buffer_size', fallback=65536) if 'network' in config else 65536

    enabled_protocols_raw = analysis_section.get('enabled_protocols', '') if 'analysis' in config else ''
    # Normalize whitespace to avoid non-matching protocol names (e.g., " Modbus").
    enabled_protocols = [p.strip() for p in enabled_protocols_raw.split(',') if p.strip()] if enabled_protocols_raw else []

    sampling_rate = config.getfloat('analysis', 'sampling_rate', fallback=1.0) if 'analysis' in config else 1.0
    metadata_extraction = config.getboolean('analysis', 'metadata_extraction', fallback=True) if 'analysis' in config else True
    payload_analysis = config.getboolean('analysis', 'payload_analysis', fallback=False) if 'analysis' in config else False

    heartbeat_interval = config.getint('telecontrol', 'heartbeat_interval', fallback=30) if 'telecontrol' in config else 30
    data_transmission_interval = config.getint('telecontrol', 'data_transmission_interval', fallback=300) if 'telecontrol' in config else 300
    max_retry_attempts = config.getint('telecontrol', 'max_retry_attempts', fallback=3) if 'telecontrol' in config else 3

    encryption_enabled = config.getboolean('security', 'encryption_enabled', fallback=True) if 'security' in config else True
    ssl_verify = config.getboolean('security', 'ssl_verify', fallback=True) if 'security' in config else True

    state_file = str(Path(config_file).with_name(f"{Path(config_file).stem}_state.json"))
    
    return ProbeConfiguration(
        probe_id=probe_id,
        api_key=api_key,
        server_url=server_url,
        interface_name=interface_name,
        promiscuous_mode=promiscuous_mode,
        capture_filter=capture_filter,
        max_packet_size=max_packet_size,
        buffer_size=buffer_size,
        enabled_protocols=enabled_protocols,
        sampling_rate=sampling_rate,
        metadata_extraction=metadata_extraction,
        payload_analysis=payload_analysis,
        heartbeat_interval=heartbeat_interval,
        data_transmission_interval=data_transmission_interval,
        max_retry_attempts=max_retry_attempts,
        encryption_enabled=encryption_enabled,
        ssl_verify=ssl_verify,
        state_file=state_file,
    )

def create_default_config(config_file: str):
    """Create a default configuration file"""
    config = configparser.ConfigParser()
    
    config['main'] = {
        'probe_id': 'probe_001',
        'api_key': 'your_api_key_here',
        'server_url': 'https://your-server.com'
    }
    
    config['network'] = {
        'interface_name': 'eth0',
        'promiscuous_mode': 'true',
        'capture_filter': '',
        'max_packet_size': '1518',
        'buffer_size': '65536'
    }
    
    config['analysis'] = {
        'enabled_protocols': 'Modbus,IEC 104,OPC-UA,EtherNet/IP,BACnet',
        'sampling_rate': '1.0',
        'metadata_extraction': 'true',
        'payload_analysis': 'false'
    }
    
    config['telecontrol'] = {
        'heartbeat_interval': '30',
        'data_transmission_interval': '300',
        'max_retry_attempts': '3'
    }
    
    config['security'] = {
        'encryption_enabled': 'true',
        'ssl_verify': 'true'
    }
    
    with open(config_file, 'w') as f:
        config.write(f)
    
    print(f"Configuration file created: {config_file}")
    print("Edit this file with your settings before starting the probe")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Network Probe Client for IndustracePRO')
    parser.add_argument('-c', '--config', default='probe.conf', help='Configuration file')
    parser.add_argument('--create-config', action='store_true', help='Create default configuration file')
    parser.add_argument('--interface', help='Network interface to monitor')
    parser.add_argument('--server', help='IndustracePRO server URL')
    parser.add_argument('--api-key', help='API key for authentication')
    parser.add_argument('--probe-id', help='Unique probe ID')
    
    args = parser.parse_args()
    
    # Create a default configuration if requested
    if args.create_config:
        create_default_config(args.config)
        return
    
    # Load configuration
    if not os.path.exists(args.config):
        print(f"Configuration file {args.config} not found")
        print("Use --create-config to create a default configuration file")
        return
    
    try:
        config = load_config(args.config)
        
        # Override with command-line arguments
        if args.interface:
            config.interface_name = args.interface
        if args.server:
            config.server_url = args.server
        if args.api_key:
            config.api_key = args.api_key
        if args.probe_id:
            config.probe_id = args.probe_id
        
        # Create and start the probe
        probe = NetworkProbe(config)
        
        # Apply dynamic filters if configured
        if config.enabled_protocols:
            probe.add_protocol_filter(config.enabled_protocols)
            logger.info(f"Applied protocol filters: {config.enabled_protocols}")
        
        probe.start()
        
    except KeyboardInterrupt:
        print("\nShutdown requested by the user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
