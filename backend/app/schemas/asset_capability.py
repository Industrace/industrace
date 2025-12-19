# backend/app/schemas/asset_capability.py
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class AssetCapabilityBase(BaseModel):
    asset_id: UUID
    capability_id: UUID
    support_level: str  # 'supported', 'not_supported', 'unknown'
    notes: Optional[str] = None
    evidence_ref: Optional[str] = None


class AssetCapabilityCreate(AssetCapabilityBase):
    pass


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

