# backend/schemas/asset_type.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class AssetTypeBase(BaseModel):
    name: str = Field(..., max_length=100, description="Asset type name")
    description: Optional[str] = Field(None, max_length=255, description="Asset type description")
    purdue_level: Optional[float] = Field(None, description="Purdue level (0-4)")  # valori 0-4, anche 1.5


class AssetTypeCreate(AssetTypeBase):
    purdue_level: Optional[float] = None


class AssetTypeUpdate(AssetTypeBase):
    purdue_level: Optional[float] = None


class AssetType(AssetTypeBase):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    icon: Optional[str] = None
    color: str = "#6366f1"
    created_at: datetime
    asset_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
