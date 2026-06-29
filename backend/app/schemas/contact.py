from pydantic import BaseModel, EmailStr, field_serializer, Field, ConfigDict
from typing import Optional, List, Any
import uuid
from datetime import datetime


class ContactBase(BaseModel):
    first_name: str = Field(..., max_length=100, description="First name")
    last_name: str = Field(..., max_length=100, description="Last name")
    phone1: Optional[str] = Field(None, max_length=50, description="Primary phone")
    phone2: Optional[str] = Field(None, max_length=50, description="Secondary phone")
    email: Optional[EmailStr] = Field(None, description="Email address")
    notes: Optional[str] = Field(None, max_length=10000, description="Notes")
    type: Optional[str] = Field(None, max_length=50, description="Contact type")


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone1: Optional[str] = None
    phone2: Optional[str] = None
    email: Optional[EmailStr] = None
    notes: Optional[str] = None
    type: Optional[str] = None


class Contact(ContactBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    sites: List[Any] = []
    locations: List[Any] = []
    suppliers: List[Any] = []
    assets: List[Any] = []

    @field_serializer("sites", mode="plain")
    def serialize_sites(self, sites: Any):
        return [s.id if hasattr(s, "id") else s for s in sites]

    @field_serializer("locations", mode="plain")
    def serialize_locations(self, locations: Any):
        return [l.id if hasattr(l, "id") else l for l in locations]

    @field_serializer("suppliers", mode="plain")
    def serialize_suppliers(self, suppliers: Any):
        return [s.id if hasattr(s, "id") else s for s in suppliers]

    @field_serializer("assets", mode="plain")
    def serialize_assets(self, assets: Any):
        return [a.id if hasattr(a, "id") else a for a in assets]

    model_config = ConfigDict(from_attributes=True)
