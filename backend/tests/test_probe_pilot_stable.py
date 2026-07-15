"""Tests for probe statistics and discovered device matching."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.asset import Asset
from app.models.asset_interface import AssetInterface
from app.models.asset_status import AssetStatus
from app.models.asset_type import AssetType
from app.models.discovered_device import DiscoveredDevice, DeviceDiscoveryStatus
from app.models.network_probe import NetworkProbe, ProbeHeartbeat, ProbeDataTransmission
from app.schemas.network_probe import NetworkProbeCreate
from app.services.discovered_device_service import DiscoveredDeviceService
from app.services.network_probe_service import NetworkProbeService


def _probe_create(site_id):
    return NetworkProbeCreate(
        name="Probe-stats",
        site_id=site_id,
        interface_name="eth0",
        heartbeat_interval=30,
        data_transmission_interval=300,
    )


def test_get_probe_statistics_aggregates_telemetry(db_session, tenant, site):
    probe = NetworkProbeService.create_probe(db_session, tenant.id, _probe_create(site.id))
    probe.total_packets_captured = 1200
    probe.total_bytes_processed = 45000
    probe.unique_devices_seen = 3
    probe.active_connections = 7
    db_session.commit()

    now = datetime.now(timezone.utc)
    db_session.add(
        ProbeHeartbeat(
            probe_id=probe.id,
            status="healthy",
            timestamp=now - timedelta(hours=2),
            cpu_usage=20.0,
            memory_usage=40.0,
            bytes_per_second=1000.0,
            error_count=0,
        )
    )
    db_session.add(
        ProbeDataTransmission(
            probe_id=probe.id,
            transmission_type="metadata",
            data_size=256,
            protocol_breakdown={"Modbus": 5, "OPC-UA": 2},
            timestamp=now - timedelta(hours=1),
        )
    )
    db_session.commit()

    stats = NetworkProbeService.get_probe_statistics(db_session, probe.id, tenant.id, time_range="24h")
    assert stats is not None
    assert stats["probe_id"] == probe.id
    assert stats["total_packets"] == 1200
    assert stats["unique_devices"] == 3
    assert stats["protocol_distribution"]["Modbus"] == 5
    assert stats["performance_metrics"]["cpu_usage_avg"] == 20.0
    assert stats["error_rate"] == 0.0


def test_get_probe_statistics_unknown_probe(db_session, tenant):
    stats = NetworkProbeService.get_probe_statistics(db_session, uuid.uuid4(), tenant.id)
    assert stats is None


def test_find_matches_prefers_mac_over_ip(db_session, tenant, site):
    asset_type = AssetType(id=uuid.uuid4(), tenant_id=tenant.id, name="PLC")
    asset_status = AssetStatus(id=uuid.uuid4(), tenant_id=tenant.id, name="Active")
    db_session.add_all([asset_type, asset_status])
    db_session.flush()

    asset = Asset(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        site_id=site.id,
        asset_type_id=asset_type.id,
        status_id=asset_status.id,
        name="Line PLC",
    )
    db_session.add(asset)
    db_session.flush()

    db_session.add(
        AssetInterface(
            id=uuid.uuid4(),
            asset_id=asset.id,
            tenant_id=tenant.id,
            name="eth0",
            type="ethernet",
            mac_address="AA:BB:CC:DD:EE:01",
            ip_address="10.0.0.50",
        )
    )

    probe = NetworkProbeService.create_probe(db_session, tenant.id, _probe_create(site.id))
    now = datetime.now(timezone.utc)
    device = DiscoveredDevice(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        site_id=site.id,
        probe_id=probe.id,
        mac_address="AA:BB:CC:DD:EE:01",
        ip_addresses=["10.0.0.50"],
        first_seen=now,
        last_seen=now,
        status=DeviceDiscoveryStatus.DISCOVERED.value,
    )
    db_session.add(device)
    db_session.commit()

    result = DiscoveredDeviceService.find_matches_for_device(db_session, tenant.id, device.id)
    assert result is not None
    assert len(result["possible_matches"]) == 2
    assert result["best_match_type"] == "mac"
    assert result["best_match_asset_name"] == "Line PLC"


def test_find_matches_returns_none_for_missing_device(db_session, tenant):
    result = DiscoveredDeviceService.find_matches_for_device(db_session, tenant.id, uuid.uuid4())
    assert result is None
