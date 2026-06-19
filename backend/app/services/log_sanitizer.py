"""Utilities to redact sensitive values from log messages."""
from __future__ import annotations

import re
from typing import Any


_API_KEY_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s&,\"'}{]+"),
    re.compile(r'(?i)(api[_-]?key\s*[:=]\s*["\'])[^"\']+'),
    re.compile(r"(?i)(X-API-Key:\s*)\S+"),
    re.compile(r"(?i)(api_key=)[^&\s]+"),
)


def redact_sensitive_text(text: str) -> str:
    if not text:
        return text
    redacted = text
    for pattern in _API_KEY_PATTERNS:
        redacted = pattern.sub(r"\1***", redacted)
    return redacted


def redact_sensitive_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value
