from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class NetworkProbeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    probe_type: str = Field(default="network", pattern="^(network|wireless|industrial)$")

    interface_name: str = Field(..., min_length=1, max_length=100)
    interface_ip: Optional[str] = None
    mirror_port: Optional[str] = None

    promiscuous_mode: bool = True
    capture_filter: Optional[str] = None
    max_packet_size: int = Field(default=1518, ge=64, le=65535)
    buffer_size: int = Field(default=65536, ge=1024, le=1048576)

    enabled_protocols: Optional[List[str]] = None
    sampling_rate: float = Field(default=1.0, ge=0.01, le=1.0)
    metadata_extraction: bool = True
    payload_analysis: bool = False

    heartbeat_interval: int = Field(default=30, ge=10, le=300)
    data_transmission_interval: int = Field(default=300, ge=60, le=3600)
    max_retry_attempts: int = Field(default=3, ge=1, le=10)

    encryption_enabled: bool = True
    ssl_verify: bool = True

    location_info: Optional[Dict[str, Any]] = None
    hardware_info: Optional[Dict[str, Any]] = None
    software_version: Optional[str] = None


class NetworkProbeCreate(NetworkProbeBase):
    site_id: uuid.UUID


class NetworkProbeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    probe_type: Optional[str] = Field(None, pattern="^(network|wireless|industrial)$")

    interface_name: Optional[str] = Field(None, min_length=1, max_length=100)
    interface_ip: Optional[str] = None
    mirror_port: Optional[str] = None

    promiscuous_mode: Optional[bool] = None
    capture_filter: Optional[str] = None
    max_packet_size: Optional[int] = Field(None, ge=64, le=65535)
    buffer_size: Optional[int] = Field(None, ge=1024, le=1048576)

    enabled_protocols: Optional[List[str]] = None
    sampling_rate: Optional[float] = Field(None, ge=0.01, le=1.0)
    metadata_extraction: Optional[bool] = None
    payload_analysis: Optional[bool] = None

    heartbeat_interval: Optional[int] = Field(None, ge=10, le=300)
    data_transmission_interval: Optional[int] = Field(None, ge=60, le=3600)
    max_retry_attempts: Optional[int] = Field(None, ge=1, le=10)

    encryption_enabled: Optional[bool] = None
    ssl_verify: Optional[bool] = None

    location_info: Optional[Dict[str, Any]] = None
    hardware_info: Optional[Dict[str, Any]] = None
    software_version: Optional[str] = None


class NetworkProbeRead(NetworkProbeBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    site_id: uuid.UUID
    status: str
    last_heartbeat: Optional[datetime] = None
    last_data_received: Optional[datetime] = None
    total_packets_captured: int
    total_bytes_processed: int
    active_connections: int
    unique_devices_seen: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_config_update: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NetworkProbeCreateResponse(NetworkProbeRead):
    api_key: str

    model_config = ConfigDict(from_attributes=True)


class ProbeHeartbeatBase(BaseModel):
    status: str = Field(..., pattern="^(healthy|warning|error)$")
    cpu_usage: Optional[float] = Field(None, ge=0.0, le=100.0)
    memory_usage: Optional[float] = Field(None, ge=0.0, le=100.0)
    disk_usage: Optional[float] = Field(None, ge=0.0, le=100.0)
    network_throughput: Optional[float] = Field(None, ge=0.0)
    packets_per_second: Optional[float] = Field(None, ge=0.0)
    bytes_per_second: Optional[float] = Field(None, ge=0.0)
    active_connections: Optional[int] = Field(None, ge=0)
    error_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)
    last_error_message: Optional[str] = None


class ProbeHeartbeatCreate(ProbeHeartbeatBase):
    probe_id: uuid.UUID


class ProbeDataTransmissionBase(BaseModel):
    transmission_type: str = Field(..., pattern="^(metadata|statistics|alert)$")
    data_size: int = Field(..., ge=0)
    compression_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    encryption_used: bool = True
    new_devices_discovered: int = Field(default=0, ge=0)
    new_connections_detected: int = Field(default=0, ge=0)
    protocol_breakdown: Optional[Dict[str, Any]] = None
    discovered_devices: Optional[List[Dict[str, Any]]] = None
    status: str = Field(default="success", pattern="^(success|failed|partial)$")
    error_message: Optional[str] = None
    retry_count: int = Field(default=0, ge=0)


class ProbeDataTransmissionCreate(ProbeDataTransmissionBase):
    probe_id: uuid.UUID


class ProbeStatusResponse(BaseModel):
    probe_id: uuid.UUID
    name: str
    status: str
    last_heartbeat: Optional[datetime] = None
    last_data_received: Optional[datetime] = None
    uptime_seconds: Optional[int] = None
    health_score: Optional[float] = None
    current_metrics: Optional[Dict[str, Any]] = None


class ProbeConfigurationResponse(BaseModel):
    probe_id: uuid.UUID
    configuration: Dict[str, Any]
    last_update: datetime
    version: str


class ProbeStatisticsResponse(BaseModel):
    probe_id: uuid.UUID
    time_range: str
    total_packets: int
    total_bytes: int
    unique_devices: int
    active_connections: int
    protocol_distribution: Dict[str, int]
    traffic_volume: Dict[str, float]
    error_rate: float
    performance_metrics: Dict[str, float]
