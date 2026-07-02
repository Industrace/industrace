"""Unit tests for discovery transmission snapshot builders."""

from __future__ import annotations

from datetime import datetime

from probe_models import NetworkDevice
from probe_transmission import build_transmission_payload, snapshot_pending_discovery


def test_snapshot_only_includes_pending_devices():
    now = datetime(2026, 1, 1, 12, 0, 0)
    devices = {
        "aa:bb:cc:dd:ee:01": NetworkDevice(
            mac_address="aa:bb:cc:dd:ee:01",
            ip_addresses=["10.0.0.1"],
            first_seen=now,
            last_seen=now,
            protocols=["Modbus"],
            packet_count=5,
            byte_count=500,
        ),
        "aa:bb:cc:dd:ee:02": NetworkDevice(
            mac_address="aa:bb:cc:dd:ee:02",
            ip_addresses=["10.0.0.2"],
            first_seen=now,
            last_seen=now,
            protocols=["TCP"],
            packet_count=1,
            byte_count=64,
        ),
    }

    pending_devices, breakdown, new_connections, acknowledged = snapshot_pending_discovery(
        devices=devices,
        pending_device_macs={"aa:bb:cc:dd:ee:01"},
        pending_new_connections=3,
    )

    assert len(pending_devices) == 1
    assert pending_devices[0]["mac_address"] == "aa:bb:cc:dd:ee:01"
    assert breakdown["Modbus"] == 5
    assert new_connections == 3
    assert acknowledged == ["aa:bb:cc:dd:ee:01"]


def test_build_transmission_payload_sets_data_size():
    payload = build_transmission_payload(
        probe_id="00000000-0000-4000-8000-000000000001",
        pending_devices=[{"mac_address": "aa:bb:cc:dd:ee:01", "protocols": [], "packet_count": 1}],
        protocol_breakdown={},
        new_connections_detected=0,
    )
    assert payload["probe_id"] == "00000000-0000-4000-8000-000000000001"
    assert payload["data_size"] > 0
