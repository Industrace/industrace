# backend/app/schemas/asset_capability.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class AssetCapabilityBase(BaseModel):
    asset_id: UUID
    capability_id: UUID
    support_level: str  # 'supported', 'not_supported', 'unknown'
    notes: Optional[str] = None
    evidence_ref: Optional[str] = None


class AssetCapabilityCreate(BaseModel):
    capability_id: UUID
    support_level: str  # 'supported', 'not_supported', 'unknown'
    notes: Optional[str] = None
    evidence_ref: Optional[str] = None


class AssetCapabilityUpdate(BaseModel):
    support_level: Optional[str] = None
    notes: Optional[str] = None
    evidence_ref: Optional[str] = None


class AssetCapabilityRead(AssetCapabilityBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetCapabilityWithDetails(AssetCapabilityRead):
    """AssetCapability with related Asset and SecurityCapability details"""
    capability: Optional[dict] = None  # Basic capability info (id, code, description)


class SecurityCapabilityInfo(BaseModel):
    """Basic SecurityCapability information"""
    id: UUID
    code: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    typical_roles: Optional[List[str]] = None


class AssetCapabilityResponse(BaseModel):
    """Response model for asset capabilities with full details"""
    id: Optional[UUID] = None  # None if not explicit (available/inferred)
    capability_id: UUID
    capability: SecurityCapabilityInfo
    support_level: str  # 'supported', 'not_supported', 'unknown', 'available'
    source: str  # 'explicit', 'inferred', 'available'
    inference_confidence: Optional[float] = None  # 0.0-1.0, only for inferred capabilities
    notes: Optional[str] = None
    evidence_ref: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BulkCapabilityItem(BaseModel):
    """Single capability item for bulk update"""
    capability_id: UUID
    support_level: str
    notes: Optional[str] = None
    evidence_ref: Optional[str] = None


class BulkCapabilityUpdate(BaseModel):
    """Request model for bulk capability update"""
    capabilities: List[BulkCapabilityItem]


class BulkCapabilityResponse(BaseModel):
    """Response model for bulk capability update"""
    created: int
    updated: int
    total: int

