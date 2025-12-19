# backend/app/schemas/security_capability.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class SecurityCapabilityBase(BaseModel):
    code: str
    name: str
    category: Optional[str] = None
    applies_to_asset: bool = True
    applies_to_zone: bool = False
    applies_to_conduit: bool = True
    typical_roles: List[str] = []
    description: Optional[str] = None


class SecurityCapabilityCreate(SecurityCapabilityBase):
    pass


class SecurityCapabilityUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    applies_to_asset: Optional[bool] = None
    applies_to_zone: Optional[bool] = None
    applies_to_conduit: Optional[bool] = None
    typical_roles: Optional[List[str]] = None
    description: Optional[str] = None


class SecurityCapabilityRead(SecurityCapabilityBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

