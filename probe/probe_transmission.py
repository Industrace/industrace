"""Snapshot/payload builders for probe data transmission."""

from __future__ import annotations

import json
from typing import Dict, List, Tuple

from probe_models import NetworkDevice


def snapshot_pending_discovery(
    devices: Dict[str, NetworkDevice],
    pending_device_macs: set[str],
    pending_new_connections: int,
) -> Tuple[List[Dict[str, object]], Dict[str, int], int, List[str]]:
    """Build a transmission snapshot from pending dirty entities."""
    acknowledged_macs = [mac for mac in pending_device_macs if mac in devices]
    pending_devices: List[Dict[str, object]] = []

    for mac in acknowledged_macs:
        device = devices.get(mac)
        if not device:
            continue
        pending_devices.append(
            {
                "mac_address": device.mac_address,
                "ip_addresses": list(device.ip_addresses or []),
                "protocols": list(device.protocols or []),
                "packet_count": device.packet_count,
                "vendor": device.vendor,
                "first_seen": device.first_seen.isoformat(),
                "last_seen": device.last_seen.isoformat(),
            }
        )

    protocol_breakdown: Dict[str, int] = {}
    for device_payload in pending_devices:
        packet_count = int(device_payload.get("packet_count") or 0)
        for protocol in device_payload.get("protocols") or []:
            protocol_breakdown[protocol] = protocol_breakdown.get(protocol, 0) + packet_count

    return pending_devices, protocol_breakdown, pending_new_connections, acknowledged_macs


def build_transmission_payload(
    probe_id: str,
    pending_devices: List[Dict[str, object]],
    protocol_breakdown: Dict[str, int],
    new_connections_detected: int,
) -> Dict[str, object]:
    """Serialize transmission payload as JSON-compatible dict."""
    transmission_data: Dict[str, object] = {
        "probe_id": probe_id,
        "transmission_type": "metadata",
        "data_size": 0,
        "new_devices_discovered": len(pending_devices),
        "new_connections_detected": new_connections_detected,
        "protocol_breakdown": protocol_breakdown,
        "discovered_devices": pending_devices,
        "status": "success",
        "encryption_used": False,
    }
    raw_json = json.dumps(transmission_data)
    transmission_data["data_size"] = len(raw_json)
    return transmission_data
