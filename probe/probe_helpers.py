"""Small reusable helpers for the network probe client.

This module intentionally contains only pure/small utilities so the main
`network_probe_client.py` file can stay focused on orchestration.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional


def sanitize_exception_message(exc: Exception, api_key: Optional[str] = None) -> str:
    """Return a log-safe exception message with sensitive tokens masked."""
    try:
        msg = str(exc)
    except Exception:
        msg = repr(exc)

    try:
        msg = re.sub(r"api_key=[^&\\s]+", "api_key=***", msg)
    except Exception:
        pass

    if api_key and api_key in msg:
        msg = msg.replace(api_key, "***")
    return msg


def parse_state_datetime(value: Any) -> datetime:
    """Parse persisted probe timestamps into naive UTC datetimes."""
    if not value:
        return datetime.now()

    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value)
        if raw.endswith("Z"):
            raw = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)

    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def combine_capture_filter(
    user_capture_filter: Optional[str],
    protocol_capture_filter: Optional[str],
) -> Optional[str]:
    """Combine user and protocol BPF filters into a single expression."""
    if user_capture_filter and protocol_capture_filter:
        return f"({user_capture_filter}) and ({protocol_capture_filter})"
    if protocol_capture_filter:
        return protocol_capture_filter
    return user_capture_filter


def mac_from_ip(ip: str) -> str:
    """Derive a stable locally-administered MAC from an IPv4 address.

    Used when capture returns L3-only frames (common on macOS loopback).
    """
    parts = str(ip).split(".")
    if len(parts) != 4:
        return "02:00:00:00:00:00"
    try:
        return f"02:00:00:{int(parts[1]):02x}:{int(parts[2]):02x}:{int(parts[3]):02x}"
    except ValueError:
        return "02:00:00:00:00:00"
