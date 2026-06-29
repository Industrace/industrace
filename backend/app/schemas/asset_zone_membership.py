# backend/app/schemas/asset_zone_membership.py
"""
Pydantic schemas for AssetZoneMembership
"""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid


class AssetZoneMembershipBase(BaseModel):
    """Base schema for AssetZoneMembership"""
    asset_id: uuid.UUID
    security_zone_id: uuid.UUID
    role: str = Field(..., max_length=100, description="Role in the zone (e.g., 'operator_interface', 'data_publisher')")
    interface_scope: Optional[str] = Field(None, max_length=255, description="Which interface of the asset belongs to this zone")
    sl_target: Optional[int] = Field(None, ge=1, le=4, description="Security Level Target override (1-4)")
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AssetZoneMembershipCreate(BaseModel):
    """Schema for creating a new AssetZoneMembership (security_zone_id can come from URL)"""
    asset_id: uuid.UUID
    security_zone_id: Optional[uuid.UUID] = None  # Can be set from URL parameter
    role: str = Field(..., max_length=100, description="Role in the zone (e.g., 'operator_interface', 'data_publisher')")
    interface_scope: Optional[str] = Field(None, max_length=255, description="Which interface of the asset belongs to this zone")
    sl_target: Optional[int] = Field(None, ge=1, le=4, description="Security Level Target override (1-4)")
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AssetZoneMembershipUpdate(BaseModel):
    """Schema for updating an AssetZoneMembership"""
    role: Optional[str] = Field(None, max_length=100)
    interface_scope: Optional[str] = Field(None, max_length=255)
    sl_target: Optional[int] = Field(None, ge=1, le=4)
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AssetZoneMembershipRead(AssetZoneMembershipBase):
    """Schema for reading AssetZoneMembership with relationships"""
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    # Relationships (opzionali, possono essere None se non eager loaded)
    # These are excluded from ORM validation and handled manually
    asset: Optional[dict] = None  # Asset summary
    security_zone: Optional[dict] = None  # SecurityZone summary

    model_config = ConfigDict(from_attributes=True)

