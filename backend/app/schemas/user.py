# backend/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import uuid
from typing import Optional
from .role import RoleRead
from .tenant import Tenant
from .tenant_features import TenantFeaturesRead


class UserCreate(BaseModel):
    name: str = Field(..., max_length=255, description="User name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=255, description="Password (minimum 8 characters, 12+ recommended with complexity requirements)")
    role_id: uuid.UUID
    is_active: Optional[bool] = True
    password_change_required: Optional[bool] = False  # If True, allows weak password (user must change on first login)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class UserRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: EmailStr
    name: str
    full_name: Optional[str] = None  # Alias for name, populated from name in endpoint
    role_id: Optional[uuid.UUID] = None
    role: Optional[RoleRead] = None
    tenant: Optional[Tenant] = None
    is_active: bool
    notifications_enabled: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    password_change_required: Optional[bool] = False
    features: Optional[TenantFeaturesRead] = None

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
