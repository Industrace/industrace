"""Tests for NetworkProbeService."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.network_probe import NetworkProbe, ProbeHeartbeat
from app.schemas.network_probe import (
    NetworkProbeCreate,
    ProbeHeartbeatCreate,
    ProbeDataTransmissionCreate,
)
from app.services.network_probe_service import NetworkProbeService


def _probe_create(site_id):
    return NetworkProbeCreate(
        name="Probe-1",
        site_id=site_id,
        interface_name="eth0",
        heartbeat_interval=30,
        data_transmission_interval=300,
    )


def test_create_probe_returns_api_key(db_session, tenant, site):
    probe = NetworkProbeService.create_probe(db_session, tenant.id, _probe_create(site.id))
    assert probe.id is not None
    assert probe.api_key
    assert len(probe.api_key) >= 32
    assert probe.status == "inactive"


def test_register_heartbeat_sets_active(db_session, tenant, site):
    probe = NetworkProbeService.create_probe(db_session, tenant.id, _probe_create(site.id))
    hb = NetworkProbeService.register_heartbeat(
        db_session,
        probe.api_key,
        ProbeHeartbeatCreate(status="healthy", probe_id=probe.id),
    )
    assert hb is not None
    db_session.refresh(probe)
    assert probe.status == "active"
    assert probe.last_heartbeat is not None


def test_register_heartbeat_invalid_key(db_session):
    result = NetworkProbeService.register_heartbeat(
        db_session,
        "invalid-key",
        ProbeHeartbeatCreate(status="healthy", probe_id=uuid.uuid4()),
    )
    assert result is None


def _transmission_payload(probe_id, devices=None):
    return ProbeDataTransmissionCreate(
        probe_id=probe_id,
        transmission_type="metadata",
        data_size=128,
        discovered_devices=devices or [],
    )


def test_data_transmission_upsert_devices(db_session, tenant, site):
    probe = NetworkProbeService.create_probe(db_session, tenant.id, _probe_create(site.id))
    tx = NetworkProbeService.register_data_transmission(
        db_session,
        probe.api_key,
        _transmission_payload(
            probe.id,
            [
                {
                    "mac_address": "aa:bb:cc:dd:ee:01",
                    "ip_addresses": ["10.0.0.1"],
                    "hostname": "device-a",
                }
            ],
        ),
    )
    assert tx is not None
    count = NetworkProbeService.upsert_discovered_devices(
        db_session,
        probe,
        [{"mac_address": "aa:bb:cc:dd:ee:01", "ip_addresses": ["10.0.0.2"]}],
    )
    assert count == 1
    db_session.refresh(probe)
    assert probe.unique_devices_seen == 1


def test_mac_dedup_normalization(db_session, tenant, site):
    probe = NetworkProbeService.create_probe(db_session, tenant.id, _probe_create(site.id))
    devices = [
        {"mac_address": "AA-BB-CC-DD-EE-FF", "ip_addresses": ["10.0.0.5"]},
        {"mac_address": "aa:bb:cc:dd:ee:ff", "ip_addresses": ["10.0.0.6"]},
    ]
    processed = NetworkProbeService.upsert_discovered_devices(db_session, probe, devices)
    assert processed == 2
    db_session.commit()
    from app.models.discovered_device import DiscoveredDevice

    rows = (
        db_session.query(DiscoveredDevice)
        .filter(DiscoveredDevice.probe_id == probe.id)
        .all()
    )
    assert len(rows) == 1
    assert rows[0].mac_address == "AA:BB:CC:DD:EE:FF"


def test_deauthorize_regenerates_key(db_session, tenant, site):
    probe = NetworkProbeService.create_probe(db_session, tenant.id, _probe_create(site.id))
    old_key = probe.api_key
    updated = NetworkProbeService.deauthorize_probe(db_session, probe.id, tenant.id)
    assert updated is not None
    assert updated.api_key != old_key
    assert updated.status == "inactive"
    assert NetworkProbeService.register_heartbeat(
        db_session,
        old_key,
        ProbeHeartbeatCreate(status="healthy", probe_id=probe.id),
    ) is None


def test_refresh_stale_probe_statuses(db_session, tenant, site):
    probe = NetworkProbeService.create_probe(db_session, tenant.id, _probe_create(site.id))
    probe.status = "active"
    probe.last_heartbeat = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.commit()

    updated = NetworkProbeService.refresh_stale_probe_statuses(db_session, tenant_id=tenant.id, stale_seconds=300)
    assert updated == 1
    db_session.refresh(probe)
    assert probe.status == "inactive"


def test_purge_old_probe_telemetry(db_session, tenant, site):
    probe = NetworkProbeService.create_probe(db_session, tenant.id, _probe_create(site.id))
    old_hb = ProbeHeartbeat(
        probe_id=probe.id,
        status="healthy",
        timestamp=datetime.now(timezone.utc) - timedelta(days=120),
    )
    db_session.add(old_hb)
    db_session.commit()

    result = NetworkProbeService.purge_old_probe_telemetry(db_session, retention_days=90)
    assert result["deleted_heartbeats"] >= 1


def test_get_probe_by_api_key(db_session, tenant, site):
    probe = NetworkProbeService.create_probe(db_session, tenant.id, _probe_create(site.id))
    found = NetworkProbeService.get_probe_by_api_key(db_session, probe.api_key)
    assert found is not None
    assert found.id == probe.id


def test_overview_counts(db_session, tenant, site):
    NetworkProbeService.create_probe(db_session, tenant.id, _probe_create(site.id))
    overview = NetworkProbeService.get_tenant_probes_overview(db_session, tenant.id)
    assert overview["total_probes"] == 1
    assert overview["active_probes"] == 0


def test_delete_probe(db_session, tenant, site):
    probe = NetworkProbeService.create_probe(db_session, tenant.id, _probe_create(site.id))
    ok = NetworkProbeService.delete_probe(db_session, probe.id, tenant.id)
    assert ok is True
    assert NetworkProbeService.get_probe_by_id(db_session, probe.id, tenant.id) is None
