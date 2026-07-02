"""Data models for the network probe client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ProbeConfiguration:
    """Probe configuration."""

    # Identification
    probe_id: str
    api_key: str
    server_url: str

    # Network configuration
    interface_name: str
    promiscuous_mode: bool = True
    capture_filter: Optional[str] = None
    max_packet_size: int = 1518
    buffer_size: int = 65536

    # Analysis configuration
    enabled_protocols: List[str] = None
    sampling_rate: float = 1.0
    metadata_extraction: bool = True
    payload_analysis: bool = False

    # Telecontrol configuration
    heartbeat_interval: int = 30
    data_transmission_interval: int = 300
    max_retry_attempts: int = 3

    # Security configuration
    encryption_enabled: bool = True
    ssl_verify: bool = True

    # Optional local persistence for probe restart.
    state_file: Optional[str] = None

    def __post_init__(self):
        if self.enabled_protocols is None:
            self.enabled_protocols = []


@dataclass
class NetworkDevice:
    """Detected network device."""

    mac_address: str
    ip_addresses: List[str]
    first_seen: datetime
    last_seen: datetime
    protocols: List[str]
    packet_count: int
    byte_count: int
    vendor: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mac_address": self.mac_address,
            "ip_addresses": self.ip_addresses,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "protocols": self.protocols,
            "packet_count": self.packet_count,
            "byte_count": self.byte_count,
            "vendor": self.vendor,
        }


@dataclass
class NetworkConnection:
    """Detected network connection."""

    source_mac: str
    dest_mac: str
    source_ip: Optional[str]
    dest_ip: Optional[str]
    source_port: Optional[int]
    dest_port: Optional[int]
    protocol: str
    first_seen: datetime
    last_seen: datetime
    packet_count: int
    byte_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_mac": self.source_mac,
            "dest_mac": self.dest_mac,
            "source_ip": self.source_ip,
            "dest_ip": self.dest_ip,
            "source_port": self.source_port,
            "dest_port": self.dest_port,
            "protocol": self.protocol,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "packet_count": self.packet_count,
            "byte_count": self.byte_count,
        }
