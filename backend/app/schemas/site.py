# backend/schemas/site.py
from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class SiteCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Site name")
    code: str = Field(..., max_length=50, description="Site code")
    address: Optional[str] = Field(None, max_length=10000, description="Site address")
    description: Optional[str] = Field(None, max_length=10000, description="Site description")
    parent_id: Optional[uuid.UUID] = None


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    review_interval_months: Optional[int] = Field(None, ge=1, le=120, description="Review interval override in months")


class Site(SiteCreate):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    review_interval_months: Optional[int] = None
    children: list[Site] = []

    model_config = ConfigDict(from_attributes=True)
