# backend/app/schemas/conduit_asset.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class ConduitAssetBase(BaseModel):
    conduit_id: UUID
    asset_id: UUID
    role: str  # 'enforcement', 'monitoring', 'gateway', etc.


class ConduitAssetCreate(ConduitAssetBase):
    pass


class ConduitAssetUpdate(BaseModel):
    role: Optional[str] = None


class ConduitAssetRead(ConduitAssetBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConduitAssetWithDetails(ConduitAssetRead):
    """ConduitAsset with related Conduit and Asset details"""
    conduit: Optional[dict] = None  # Basic conduit info (id, name)
    asset: Optional[dict] = None  # Basic asset info (id, name)

