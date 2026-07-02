"""Pytest configuration for probe client unit tests."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace


def _install_scapy_stub() -> None:
    """Allow unit tests without a native Scapy install."""
    if "scapy.all" in sys.modules:
        return

    scapy = ModuleType("scapy")
    scapy_all = ModuleType("scapy.all")
    for name in ("ARP", "Ether", "ICMP", "IP", "Raw", "TCP", "UDP", "sniff"):
        setattr(scapy_all, name, SimpleNamespace())
    scapy.all = scapy_all
    sys.modules["scapy"] = scapy
    sys.modules["scapy.all"] = scapy_all


_install_scapy_stub()

PROBE_ROOT = Path(__file__).resolve().parents[1]
if str(PROBE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROBE_ROOT))
