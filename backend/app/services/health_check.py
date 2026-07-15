"""Deep health checks for operational dependencies (database, Redis)."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import engine

APP_RELEASE_VERSION = "2.1.1"


def check_database() -> dict[str, Any]:
    """Verify database connectivity with a lightweight query."""
    started = time.perf_counter()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return {"status": "ok", "latency_ms": latency_ms}
    except SQLAlchemyError as exc:
        return {"status": "error", "detail": str(exc)}


def check_redis() -> dict[str, Any]:
    """Verify Redis connectivity used for SSO OAuth state storage."""
    if not settings.REDIS_ENABLED:
        return {"status": "disabled", "detail": "REDIS_ENABLED is false"}

    try:
        from redis import Redis
    except ImportError:
        return {"status": "unavailable", "detail": "redis package not installed"}

    started = time.perf_counter()
    try:
        client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True,
        )
        client.ping()
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "status": "ok",
            "latency_ms": latency_ms,
            "purpose": "sso_oauth_state",
        }
    except Exception as exc:
        return {"status": "unavailable", "detail": str(exc)}


def build_health_payload() -> tuple[dict[str, Any], int]:
    """Build the /health response body and HTTP status code."""
    database = check_database()
    redis = check_redis()

    checks = {
        "database": database,
        "redis": redis,
    }

    if database["status"] == "error":
        overall_status = "unhealthy"
        status_code = 503
    elif settings.REDIS_ENABLED and redis["status"] == "unavailable":
        overall_status = "degraded"
        status_code = 200
    else:
        overall_status = "healthy"
        status_code = 200

    payload = {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": APP_RELEASE_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": checks,
    }
    return payload, status_code
