from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from app.models.discovered_device import DeviceDiscoveryStatus


class DiscoveredDeviceBase(BaseModel):
    mac_address: str = Field(..., min_length=11, max_length=17)
    ip_addresses: List[str] = Field(default_factory=list)
    hostname: Optional[str] = Field(None, max_length=255)
    vendor: Optional[str] = Field(None, max_length=100)
    device_type: Optional[str] = Field(None, max_length=100)
    protocols: List[str] = Field(default_factory=list)
    firmware_version: Optional[str] = Field(None, max_length=100)
    first_seen: datetime
    last_seen: datetime
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    auto_import_enabled: bool = False


class DiscoveredDeviceCreate(DiscoveredDeviceBase):
    site_id: uuid.UUID
    probe_id: uuid.UUID


class DiscoveredDeviceUpdate(BaseModel):
    status: Optional[DeviceDiscoveryStatus] = None
    matched_asset_id: Optional[uuid.UUID] = None
    match_confidence: Optional[int] = Field(None, ge=0, le=100)
    match_reason: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    auto_import_enabled: Optional[bool] = None


class DiscoveredDeviceRead(DiscoveredDeviceBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    site_id: uuid.UUID
    probe_id: uuid.UUID
    discovery_count: int
    confidence_score: int
    status: DeviceDiscoveryStatus
    matched_asset_id: Optional[uuid.UUID] = None
    match_confidence: int
    match_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DiscoveredDeviceMatchCandidate(BaseModel):
    asset_id: uuid.UUID
    asset_name: str
    match_type: str
    matched_mac: Optional[str] = None
    matched_ip: Optional[str] = None


class DiscoveredDeviceReadEnriched(DiscoveredDeviceRead):
    best_match_asset_id: Optional[uuid.UUID] = None
    best_match_asset_name: Optional[str] = None
    best_match_type: Optional[str] = None
    possible_matches: List[DiscoveredDeviceMatchCandidate] = Field(default_factory=list)


class DiscoveredDeviceOnboardRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    tag: Optional[str] = Field(None, max_length=100)


class DiscoveredDeviceOnboardResponse(BaseModel):
    discovered_device_id: uuid.UUID
    asset_id: uuid.UUID
    asset_name: str


class DiscoveredDeviceStats(BaseModel):
    total_discovered: int
    pending_review: int
    auto_imported: int
    conflicts: int
    by_status: Dict[str, int]


class DeviceMatchingRequest(BaseModel):
    action: str = Field(..., pattern="^(import|assign|ignore)$")
    asset_id: Optional[uuid.UUID] = None


class DeviceMatchingResponse(BaseModel):
    device_id: uuid.UUID
    status: DeviceDiscoveryStatus
    matched_asset_id: Optional[uuid.UUID] = None
    match_confidence: int = 0
    match_reason: Optional[str] = None
