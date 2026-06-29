# backend/schemas/location.py

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
import uuid
from .site import Site


class LocationFloorplanBase(BaseModel):
    id: uuid.UUID
    location_id: uuid.UUID
    file_path: str


class LocationFloorplanCreate(LocationFloorplanBase):
    tenant_id: uuid.UUID


class LocationFloorplanRead(LocationFloorplanBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PositionUpdate(BaseModel):
    map_x: float
    map_y: float


class LocationCreate(BaseModel):
    site_id: uuid.UUID
    area_id: Optional[uuid.UUID] = None
    name: str = Field(..., max_length=255, description="Location name")
    code: Optional[str] = Field(None, max_length=50, description="Location code")
    description: str = Field(..., max_length=10000, description="Location description")
    notes: Optional[str] = Field(None, max_length=10000, description="Notes")


class LocationUpdate(BaseModel):
    site_id: Optional[uuid.UUID] = None
    area_id: Optional[uuid.UUID] = None
    name: Optional[str] = Field(None, max_length=255, description="Location name")
    code: Optional[str] = Field(None, max_length=50, description="Location code")
    description: Optional[str] = Field(None, max_length=10000, description="Location description")
    notes: Optional[str] = Field(None, max_length=10000, description="Notes")


class Location(LocationCreate):
    id: uuid.UUID
    tenant_id: uuid.UUID
    updated_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LocationRead(LocationCreate):
    id: uuid.UUID
    tenant_id: uuid.UUID
    updated_at: Optional[datetime] = None
    created_at: datetime
    floorplan: Optional[LocationFloorplanRead] = None
    site: Optional[Site] = None
    area_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
