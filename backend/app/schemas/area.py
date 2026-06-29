from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
import uuid

from app.schemas.site import Site


class AreaBase(BaseModel):
    name: str = Field(..., max_length=255, description="Area name")
    code: str = Field(..., max_length=50, description="Area code")
    typology: Optional[str] = Field(None, max_length=100, description="Area typology")
    notes: Optional[str] = Field(None, description="Area notes")


class AreaCreate(AreaBase):
    site_id: uuid.UUID = Field(..., description="Site ID")


class AreaUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Area name")
    code: Optional[str] = Field(None, max_length=50, description="Area code")
    typology: Optional[str] = Field(None, max_length=100, description="Area typology")
    notes: Optional[str] = Field(None, description="Area notes")
    site_id: Optional[uuid.UUID] = Field(None, description="Site ID")


class AreaRead(AreaBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    site_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    site: Optional[Site] = None

    model_config = ConfigDict(from_attributes=True)


class AreaList(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    typology: Optional[str]
    site_id: uuid.UUID
    site_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 