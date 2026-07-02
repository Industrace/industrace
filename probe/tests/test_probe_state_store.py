"""Unit tests for probe state persistence."""

from __future__ import annotations

from datetime import datetime

from probe_models import NetworkConnection, NetworkDevice
from probe_state_store import load_probe_state, save_probe_state


def _parse_dt(value):
    return datetime.fromisoformat(str(value))


def test_state_roundtrip_includes_pending(tmp_path):
    state_file = str(tmp_path / "probe_state.json")
    now = datetime(2026, 1, 1, 12, 0, 0)
    devices = {
        "aa:bb:cc:dd:ee:01": NetworkDevice(
            mac_address="aa:bb:cc:dd:ee:01",
            ip_addresses=["10.0.0.1"],
            first_seen=now,
            last_seen=now,
            protocols=["Modbus"],
            packet_count=3,
            byte_count=300,
        )
    }
    connections = {
        "aa:bb:cc:dd:ee:01->aa:bb:cc:dd:ee:02": NetworkConnection(
            source_mac="aa:bb:cc:dd:ee:01",
            dest_mac="aa:bb:cc:dd:ee:02",
            source_ip="10.0.0.1",
            dest_ip="10.0.0.2",
            source_port=502,
            dest_port=12345,
            protocol="Modbus",
            first_seen=now,
            last_seen=now,
            packet_count=1,
            byte_count=100,
        )
    }
    pending = {"aa:bb:cc:dd:ee:01"}

    save_probe_state(
        state_file=state_file,
        devices=devices,
        connections=connections,
        pending_device_macs=pending,
        pending_new_connections=2,
        last_successful_transmission_at="2026-01-01T11:00:00",
    )

    loaded = load_probe_state(state_file, parse_datetime=_parse_dt)
    assert loaded.devices["aa:bb:cc:dd:ee:01"].packet_count == 3
    assert loaded.connections["aa:bb:cc:dd:ee:01->aa:bb:cc:dd:ee:02"].protocol == "Modbus"
    assert loaded.pending_device_macs == pending
    assert loaded.pending_new_connections == 2
    assert loaded.last_successful_transmission_at == "2026-01-01T11:00:00"


def test_v1_state_requeues_all_devices(tmp_path):
    state_file = tmp_path / "probe_state.json"
    state_file.write_text(
        """
        {
          "devices": {
            "aa:bb:cc:dd:ee:ff": {
              "mac_address": "aa:bb:cc:dd:ee:ff",
              "ip_addresses": ["192.168.1.10"],
              "first_seen": "2026-01-01T10:00:00",
              "last_seen": "2026-01-01T10:05:00",
              "protocols": ["TCP"],
              "packet_count": 1,
              "byte_count": 64
            }
          },
          "connections": {}
        }
        """,
        encoding="utf-8",
    )

    loaded = load_probe_state(str(state_file), parse_datetime=_parse_dt)
    assert loaded.pending_device_macs == {"aa:bb:cc:dd:ee:ff"}
