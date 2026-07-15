"""Minimal tests for rate limiter Redis fallback behavior."""

from app.services.rate_limiter import get_redis_client


def test_get_redis_client_returns_none_when_disabled(monkeypatch):
    monkeypatch.setattr("app.services.rate_limiter.settings.REDIS_ENABLED", False)
    assert get_redis_client() is None


def test_get_redis_client_returns_none_when_rate_limit_disabled(monkeypatch):
    monkeypatch.setattr("app.services.rate_limiter.settings.REDIS_ENABLED", True)
    monkeypatch.setattr("app.services.rate_limiter.settings.RATE_LIMIT_ENABLED", False)
    assert get_redis_client() is None
