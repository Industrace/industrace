"""Runtime health counters for the network probe."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class HealthSnapshot:
    """Immutable health view used for heartbeat serialization."""

    status: str
    error_count: int
    warning_count: int


class ProbeHealth:
    """Track lightweight runtime signals to report probe health."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._error_count = 0
        self._warning_count = 0
        self._last_packet_ts = 0.0
        self._last_successful_heartbeat_ts = 0.0

    def record_packet_seen(self) -> None:
        with self._lock:
            self._last_packet_ts = time.time()

    def record_error(self) -> None:
        with self._lock:
            self._error_count += 1

    def record_warning(self) -> None:
        with self._lock:
            self._warning_count += 1

    def record_heartbeat_success(self) -> None:
        with self._lock:
            self._last_successful_heartbeat_ts = time.time()

    def snapshot(self, heartbeat_interval: int, network_metrics: Dict[str, float]) -> HealthSnapshot:
        with self._lock:
            error_count = self._error_count
            warning_count = self._warning_count
            last_packet_ts = self._last_packet_ts

        packets_per_second = float(network_metrics.get("packets_per_second", 0.0) or 0.0)
        active_connections = int(network_metrics.get("active_connections", 0) or 0)
        status = "healthy"

        if error_count > 0:
            status = "warning"

        now = time.time()
        stale_packet_seconds = max(60, int(heartbeat_interval) * 3)
        if last_packet_ts > 0 and (now - last_packet_ts) > stale_packet_seconds:
            warning_count += 1
            status = "warning"

        if packets_per_second <= 0.0 and active_connections <= 0 and error_count > 0:
            status = "error"

        return HealthSnapshot(
            status=status,
            error_count=error_count,
            warning_count=warning_count,
        )
