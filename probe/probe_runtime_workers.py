"""Worker mixin for heartbeat/transmission/configuration runtime loops."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict

from retry_policy import next_backoff_seconds

logger = logging.getLogger(__name__)


class ProbeRuntimeWorkersMixin:
    """Background worker methods extracted from the main probe orchestrator."""

    def _heartbeat_worker(self):
        """Heartbeat sender worker."""
        logger.info("Starting heartbeat worker")

        while self.running:
            try:
                if self._send_heartbeat():
                    self._heartbeat_failures = 0
                    time.sleep(self.config.heartbeat_interval)
                else:
                    self._heartbeat_failures += 1
                    if self._heartbeat_failures >= self.config.max_retry_attempts:
                        logger.warning(
                            "Heartbeat reached max_retry_attempts=%s; pausing until next interval",
                            self.config.max_retry_attempts,
                        )
                        self._heartbeat_failures = 0
                        time.sleep(self.config.heartbeat_interval)
                        continue
                    delay = next_backoff_seconds(
                        failures=self._heartbeat_failures,
                        base_seconds=2.0,
                        max_seconds=min(60.0, float(self.config.heartbeat_interval)),
                    )
                    time.sleep(delay)
            except Exception as e:
                self.health.record_error()
                logger.error(f"Error sending heartbeat: {self._sanitize_exception_message(e)}")
                self._heartbeat_failures += 1
                if self._heartbeat_failures >= self.config.max_retry_attempts:
                    self._heartbeat_failures = 0
                    time.sleep(self.config.heartbeat_interval)
                    continue
                time.sleep(next_backoff_seconds(self._heartbeat_failures, base_seconds=2.0, max_seconds=30.0))

    def _send_heartbeat(self):
        """Send heartbeat to the server."""
        try:
            system_metrics = self._get_system_metrics()
            network_metrics = self._get_network_metrics()
            health_snapshot = self.health.snapshot(
                heartbeat_interval=self.config.heartbeat_interval,
                network_metrics=network_metrics,
            )

            heartbeat_data = {
                "probe_id": self.config.probe_id,
                "status": health_snapshot.status,
                "cpu_usage": system_metrics.get("cpu_usage", 0.0),
                "memory_usage": system_metrics.get("memory_usage", 0.0),
                "disk_usage": system_metrics.get("disk_usage", 0.0),
                "packets_per_second": network_metrics.get("packets_per_second", 0.0),
                "bytes_per_second": network_metrics.get("bytes_per_second", 0.0),
                "active_connections": network_metrics.get("active_connections", 0),
                "error_count": health_snapshot.error_count,
                "warning_count": health_snapshot.warning_count,
            }
            dropped = int(getattr(self, "_payload_buffer_dropped_count", 0) or 0)
            if dropped > 0:
                heartbeat_data["last_error_message"] = f"payload_buffer_dropped={dropped}"

            response = self.http.post(
                f"{self.config.server_url}/api/network-probes/heartbeat",
                headers=self._probe_request_headers(),
                json=heartbeat_data,
                timeout=10,
                verify=self.config.ssl_verify,
            )

            if self._handle_probe_http_status(response, "Heartbeat"):
                self.health.record_heartbeat_success()
                logger.debug("Heartbeat sent successfully")
                return True
            if response.status_code == 429:
                self.health.record_warning()
            return False

        except Exception as e:
            self.health.record_error()
            logger.error(f"Error sending heartbeat: {self._sanitize_exception_message(e)}")
            return False

    def _transmission_worker(self):
        """Data transmission worker."""
        logger.info("Starting data transmission worker")

        while self.running:
            try:
                if self._send_data_transmission():
                    self._transmission_failures = 0
                    self._transmission_wake.wait(timeout=self.config.data_transmission_interval)
                    self._transmission_wake.clear()
                else:
                    self._transmission_failures += 1
                    if self._transmission_failures >= self.config.max_retry_attempts:
                        logger.warning(
                            "Data transmission reached max_retry_attempts=%s; pausing until next interval",
                            self.config.max_retry_attempts,
                        )
                        self._transmission_failures = 0
                        time.sleep(self.config.data_transmission_interval)
                        continue
                    max_backoff = min(120.0, float(max(15, self.config.data_transmission_interval)))
                    time.sleep(
                        next_backoff_seconds(
                            failures=self._transmission_failures,
                            base_seconds=5.0,
                            max_seconds=max_backoff,
                        )
                    )
            except Exception as e:
                self.health.record_error()
                logger.error(f"Error transmitting data: {self._sanitize_exception_message(e)}")
                self._transmission_failures += 1
                if self._transmission_failures >= self.config.max_retry_attempts:
                    self._transmission_failures = 0
                    time.sleep(self.config.data_transmission_interval)
                    continue
                time.sleep(next_backoff_seconds(self._transmission_failures, base_seconds=5.0, max_seconds=120.0))

    def _configuration_worker(self):
        """Worker to synchronize configuration from backend."""
        logger.info("Starting configuration sync worker")

        while self.running:
            try:
                self._sync_remote_configuration()
            except Exception as e:
                logger.error(f"Error syncing remote configuration: {self._sanitize_exception_message(e)}")
            time.sleep(30)

    def _sync_remote_configuration(self):
        """Fetch and apply the remote configuration if updated."""
        try:
            response = self.http.get(
                f"{self.config.server_url}/api/network-probes/configuration/{self.config.probe_id}",
                headers=self._probe_request_headers(),
                timeout=10,
                verify=self.config.ssl_verify,
            )

            if response.status_code == 200:
                payload = response.json() or {}
                marker = payload.get("last_update") or payload.get("version")
                config_payload = payload.get("configuration") or {}

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
        """Send data transmission to the server."""
        try:
            pending_devices, protocol_breakdown, new_connections_detected, acknowledged_macs = (
                self._snapshot_discovery_state()
            )
            if not pending_devices and new_connections_detected <= 0:
                logger.debug("Skipping empty data transmission snapshot")
                return True

            transmission_data = self._build_transmission_payload(
                pending_devices=pending_devices,
                protocol_breakdown=protocol_breakdown,
                new_connections_detected=new_connections_detected,
            )
            response = self._post_data_transmission(transmission_data)

            if self._handle_probe_http_status(response, "Data transmission"):
                logger.info(
                    "Data transmission sent successfully (%s devices, %s new connections)",
                    len(pending_devices),
                    new_connections_detected,
                )
                self._last_successful_transmission_at = datetime.now().isoformat()
                self._last_transmission_sent_ts = time.time()
                with self.data_buffer_lock:
                    self.data_buffer.clear()
                with self.data_lock:
                    for mac in acknowledged_macs:
                        self._pending_device_macs.discard(mac)
                    self._pending_new_connections = 0
                self._maybe_save_state(best_effort=True)
                return True
            if response.status_code == 429:
                self.health.record_warning()
            return False

        except Exception as e:
            self.health.record_error()
            logger.error(f"Error transmitting data: {self._sanitize_exception_message(e)}")
            return False
