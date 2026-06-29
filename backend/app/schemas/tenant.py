# backend/schemas/tenant.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
from typing import Optional


class TenantCreate(BaseModel):
    name: str
    slug: str


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    is_active: Optional[bool] = None


class Tenant(TenantCreate):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
