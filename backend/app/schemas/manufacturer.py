# backend/schemas/manufacturer.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid
from app.schemas.schema_mixins import PhoneWebsiteEmailMixin


class ManufacturerBase(PhoneWebsiteEmailMixin, BaseModel):
    name: str = Field(..., max_length=255, description="Manufacturer name")
    description: Optional[str] = Field(None, max_length=10000, description="Manufacturer description")
    website: Optional[str] = Field(None, max_length=255, description="Website URL")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")


class ManufacturerCreate(ManufacturerBase):
    pass


class ManufacturerUpdate(PhoneWebsiteEmailMixin, BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class Manufacturer(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str]
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
