"""Helpers for building BPF protocol filters."""

from __future__ import annotations

from typing import List


def protocol_filters_from_names(protocols: List[str]) -> List[str]:
    """Map human-friendly protocol names to BPF filter fragments."""
    filters: List[str] = []
    for protocol in protocols:
        p = str(protocol).upper().replace(" ", "").replace("-", "").replace("_", "")
        if p == "MODBUS":
            filters.append("tcp port 502")
        elif p == "IEC104":
            filters.append("tcp port 2404")
        elif p == "OPCUA":
            filters.append("tcp port 4840")
        elif p == "ETHERNET/IP":
            filters.append("tcp port 44818 or udp port 2222")
        elif p == "BACNET":
            filters.append("udp port 47808")
        elif p == "DNP3":
            filters.append("tcp port 20000")
        elif p == "KNX":
            filters.append("udp port 3671")
        elif p == "MQTT":
            filters.append("tcp port 1883 or tcp port 8883")
        elif p == "HTTP":
            filters.append("tcp port 80")
        elif p == "HTTPS":
            filters.append("tcp port 443")
    return filters
