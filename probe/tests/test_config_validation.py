"""Configuration validation tests."""

from __future__ import annotations

import uuid

import pytest

from network_probe_client import NetworkProbe
from probe_models import ProbeConfiguration


def _minimal_probe(**overrides):
    config = ProbeConfiguration(
        probe_id=overrides.pop("probe_id", str(uuid.uuid4())),
        api_key=overrides.pop("api_key", "test-api-key"),
        server_url=overrides.pop("server_url", "https://example.test"),
        interface_name=overrides.pop("interface_name", "eth0"),
        **overrides,
    )
    probe = object.__new__(NetworkProbe)
    probe.config = config
    return probe


def test_validate_config_rejects_non_uuid_probe_id():
    probe = _minimal_probe(probe_id="probe_001")
    with pytest.raises(ValueError, match="UUID"):
        probe._validate_config()


def test_validate_config_accepts_uuid_probe_id():
    probe = _minimal_probe(probe_id="00000000-0000-4000-8000-000000000001")
    probe._validate_config()
