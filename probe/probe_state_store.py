"""Persistence helpers for probe in-memory discovery state."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from probe_models import NetworkConnection, NetworkDevice


@dataclass
class ProbePersistedState:
    """Snapshot of probe discovery state restored from disk."""

    devices: Dict[str, NetworkDevice]
    connections: Dict[str, NetworkConnection]
    pending_device_macs: Set[str]
    pending_new_connections: int
    last_successful_transmission_at: Optional[str]


def _parse_devices(
    devices_data: Dict[str, Any],
    parse_datetime: Callable[[Any], datetime],
    now: datetime,
) -> Dict[str, NetworkDevice]:
    devices: Dict[str, NetworkDevice] = {}
    for mac, d in devices_data.items():
        try:
            devices[mac] = NetworkDevice(
                mac_address=str(d.get("mac_address") or mac),
                ip_addresses=list(d.get("ip_addresses") or []),
                first_seen=parse_datetime(d.get("first_seen") or now.isoformat()),
                last_seen=parse_datetime(d.get("last_seen") or now.isoformat()),
                protocols=list(d.get("protocols") or []),
                packet_count=int(d.get("packet_count") or 0),
                byte_count=int(d.get("byte_count") or 0),
                vendor=d.get("vendor"),
            )
        except Exception:
            continue
    return devices


def _parse_connections(
    connections_data: Dict[str, Any],
    parse_datetime: Callable[[Any], datetime],
    now: datetime,
) -> Dict[str, NetworkConnection]:
    connections: Dict[str, NetworkConnection] = {}
    for conn_key, d in connections_data.items():
        try:
            connections[conn_key] = NetworkConnection(
                source_mac=str(d.get("source_mac") or ""),
                dest_mac=str(d.get("dest_mac") or ""),
                source_ip=d.get("source_ip"),
                dest_ip=d.get("dest_ip"),
                source_port=d.get("source_port"),
                dest_port=d.get("dest_port"),
                protocol=str(d.get("protocol") or "Unknown"),
                first_seen=parse_datetime(d.get("first_seen") or now.isoformat()),
                last_seen=parse_datetime(d.get("last_seen") or now.isoformat()),
                packet_count=int(d.get("packet_count") or 0),
                byte_count=int(d.get("byte_count") or 0),
            )
        except Exception:
            continue
    return connections


def load_probe_state(
    state_file: str,
    parse_datetime: Callable[[Any], datetime],
) -> ProbePersistedState:
    """Load persisted devices, connections, and pending delivery metadata."""
    path = Path(state_file)
    if not path.exists():
        return ProbePersistedState({}, {}, set(), 0, None)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f) or {}

    now = datetime.now()
    devices = _parse_devices(data.get("devices") or {}, parse_datetime, now)
    connections = _parse_connections(data.get("connections") or {}, parse_datetime, now)

    raw_pending = data.get("pending_device_macs")
    if isinstance(raw_pending, list):
        pending_device_macs = {str(mac) for mac in raw_pending if str(mac) in devices}
    else:
        # v1 state files: re-queue all known devices so nothing is lost after restart.
        pending_device_macs = set(devices.keys())

    pending_new_connections = int(data.get("pending_new_connections") or 0)
    last_successful_transmission_at = data.get("last_successful_transmission_at")

    return ProbePersistedState(
        devices=devices,
        connections=connections,
        pending_device_macs=pending_device_macs,
        pending_new_connections=pending_new_connections,
        last_successful_transmission_at=last_successful_transmission_at,
    )


def save_probe_state(
    state_file: str,
    devices: Dict[str, NetworkDevice],
    connections: Dict[str, NetworkConnection],
    pending_device_macs: Set[str],
    pending_new_connections: int,
    last_successful_transmission_at: Optional[str] = None,
) -> None:
    """Persist discovery state and pending delivery metadata atomically."""
    payload = {
        "version": 2,
        "saved_at": datetime.now().isoformat(),
        "devices": {mac: dev.to_dict() for mac, dev in devices.items()},
        "connections": {k: conn.to_dict() for k, conn in connections.items()},
        "pending_device_macs": sorted(pending_device_macs),
        "pending_new_connections": pending_new_connections,
        "last_successful_transmission_at": last_successful_transmission_at,
    }

    path = Path(state_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = str(path) + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp_path, str(path))


# Backward-compatible helpers for callers expecting the old tuple API.
def load_probe_state_legacy(
    state_file: str,
    parse_datetime: Callable[[Any], datetime],
) -> Tuple[Dict[str, NetworkDevice], Dict[str, NetworkConnection]]:
    state = load_probe_state(state_file, parse_datetime)
    return state.devices, state.connections
