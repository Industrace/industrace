"""Tests for probe API key resolution."""
import pytest
from fastapi import HTTPException

from app.services.probe_auth import resolve_probe_api_key


def test_resolve_probe_api_key_prefers_header():
    assert resolve_probe_api_key("header-key", "query-key") == "header-key"


def test_resolve_probe_api_key_falls_back_to_query():
    assert resolve_probe_api_key(None, "query-key") == "query-key"


def test_resolve_probe_api_key_missing_raises():
    with pytest.raises(HTTPException) as exc:
        resolve_probe_api_key(None, None)
    assert exc.value.status_code == 401
