"""Tests for deep health checks (database, Redis)."""

from contextlib import contextmanager
from unittest.mock import MagicMock

from sqlalchemy.exc import OperationalError

from app.services import health_check as health


def test_check_database_ok():
    result = health.check_database()
    assert result["status"] == "ok"
    assert "latency_ms" in result


def test_check_database_error(monkeypatch):
    @contextmanager
    def _failing_connect():
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))
        yield  # pragma: no cover

    fake_engine = MagicMock()
    fake_engine.connect = _failing_connect
    monkeypatch.setattr(health, "engine", fake_engine)

    result = health.check_database()
    assert result["status"] == "error"
    assert "detail" in result


def test_check_redis_disabled(monkeypatch):
    monkeypatch.setattr(health.settings, "REDIS_ENABLED", False)
    result = health.check_redis()
    assert result["status"] == "disabled"


def test_check_redis_unavailable(monkeypatch):
    monkeypatch.setattr(health.settings, "REDIS_ENABLED", True)
    monkeypatch.setattr(health.settings, "REDIS_URL", "redis://127.0.0.1:6399/0")

    result = health.check_redis()
    assert result["status"] == "unavailable"


def test_build_health_payload_healthy(monkeypatch):
    monkeypatch.setattr(health, "check_database", lambda: {"status": "ok", "latency_ms": 1.0})
    monkeypatch.setattr(
        health,
        "check_redis",
        lambda: {"status": "disabled", "detail": "REDIS_ENABLED is false"},
    )
    monkeypatch.setattr(health.settings, "REDIS_ENABLED", False)

    payload, status_code = health.build_health_payload()
    assert status_code == 200
    assert payload["status"] == "healthy"
    assert payload["checks"]["database"]["status"] == "ok"


def test_build_health_payload_degraded(monkeypatch):
    monkeypatch.setattr(health, "check_database", lambda: {"status": "ok", "latency_ms": 1.0})
    monkeypatch.setattr(
        health,
        "check_redis",
        lambda: {"status": "unavailable", "detail": "connection refused"},
    )
    monkeypatch.setattr(health.settings, "REDIS_ENABLED", True)

    payload, status_code = health.build_health_payload()
    assert status_code == 200
    assert payload["status"] == "degraded"
    assert payload["checks"]["redis"]["status"] == "unavailable"


def test_build_health_payload_unhealthy(monkeypatch):
    monkeypatch.setattr(
        health,
        "check_database",
        lambda: {"status": "error", "detail": "connection refused"},
    )
    monkeypatch.setattr(health, "check_redis", lambda: {"status": "disabled"})

    payload, status_code = health.build_health_payload()
    assert status_code == 503
    assert payload["status"] == "unhealthy"
