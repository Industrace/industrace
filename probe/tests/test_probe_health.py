"""Unit tests for probe health snapshots."""

from __future__ import annotations

from probe_health import ProbeHealth


def test_health_snapshot_marks_warning_on_errors():
    health = ProbeHealth()
    health.record_error()
    snapshot = health.snapshot(heartbeat_interval=30, network_metrics={"packets_per_second": 1.0, "active_connections": 1})
    assert snapshot.status == "warning"
    assert snapshot.error_count == 1
