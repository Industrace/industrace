"""MAC address normalization utilities."""
from __future__ import annotations

import re
from typing import Optional

_MAC_HEX_RE = re.compile(r"^[0-9A-F]{12}$")


def normalize_mac_address(mac: Optional[str]) -> Optional[str]:
    """
    Canonical form: uppercase hex pairs separated by colons (AA:BB:CC:DD:EE:FF).
    Returns None if the input cannot be normalized to 12 hex digits.
    """
    if not mac:
        return None
    hex_only = re.sub(r"[^0-9A-Fa-f]", "", mac.strip())
    if len(hex_only) != 12:
        return None
    hex_only = hex_only.upper()
    if not _MAC_HEX_RE.match(hex_only):
        return None
    return ":".join(hex_only[i : i + 2] for i in range(0, 12, 2))
