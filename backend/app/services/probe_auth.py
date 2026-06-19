"""Authentication helpers for network probe API endpoints."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Header, HTTPException, Query, Request, status

from app.config import settings
from app.services.log_sanitizer import redact_sensitive_text

logger = logging.getLogger(__name__)


def resolve_probe_api_key(
    header_value: Optional[str],
    query_value: Optional[str],
) -> str:
    """
    Prefer X-API-Key header; query param is supported temporarily for backward compatibility.
    """
    if header_value and header_value.strip():
        return header_value.strip()
    if query_value and query_value.strip():
        logger.warning(
            "Probe API key passed via query parameter is deprecated; use %s header",
            settings.API_KEY_HEADER,
        )
        return query_value.strip()
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="API key mancante (header %s)" % settings.API_KEY_HEADER,
    )


def log_probe_auth_failure(reason: str, *, request: Optional[Request] = None) -> None:
    """Log probe auth failures without leaking credentials."""
    client = request.client.host if request and request.client else "unknown"
    logger.warning(
        "Probe authentication failed: %s (client=%s)",
        redact_sensitive_text(reason),
        client,
    )


async def get_probe_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    api_key: Optional[str] = Query(None, include_in_schema=False),
) -> str:
    """FastAPI dependency: extract probe API key from header or legacy query param."""
    return resolve_probe_api_key(x_api_key, api_key)
