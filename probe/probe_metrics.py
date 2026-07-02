"""System/network metrics helpers for the probe runtime."""

from __future__ import annotations

import platform
from datetime import datetime
from typing import Any, Deque, Dict

import psutil


def get_system_metrics() -> Dict[str, Any]:
    """Collect host-level metrics for heartbeat payloads."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_usage": cpu_percent,
        "memory_usage": memory.percent,
        "disk_usage": disk.percent,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
    }


def get_network_metrics(
    traffic_buckets: Deque,
    rate_window_seconds: int,
    connections: Dict[str, Any],
    devices: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute sliding-window throughput and active entity counts."""
    packets_window = sum(bucket[1] for bucket in traffic_buckets)
    bytes_window = sum(bucket[2] for bucket in traffic_buckets)

    now = datetime.now()
    active_connections = len(
        [conn for conn in connections.values() if (now - conn.last_seen).total_seconds() < 300]
    )
    unique_devices = len(devices)

    window = max(1, int(rate_window_seconds))
    return {
        "packets_per_second": packets_window / window,
        "bytes_per_second": bytes_window / window,
        "active_connections": active_connections,
        "unique_devices": unique_devices,
    }
