# backend/app/schemas/sr_capability.py
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SRCapabilityBase(BaseModel):
    sr_id: UUID
    capability_id: UUID
    importance: str  # 'primary', 'supporting'


class SRCapabilityCreate(SRCapabilityBase):
    pass


class SRCapabilityUpdate(BaseModel):
    importance: Optional[str] = None


class SRCapabilityRead(SRCapabilityBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SRCapabilityWithDetails(SRCapabilityRead):
    """SRCapability with related SecurityRequirement and SecurityCapability details"""
    security_requirement: Optional[dict] = None  # Basic SR info (id, requirement_id, title)
    capability: Optional[dict] = None  # Basic capability info (id, code, description)

