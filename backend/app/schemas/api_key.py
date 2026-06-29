# backend/schemas/api_key.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid


class ApiKeyBase(BaseModel):
    name: str = Field(..., description="API Key name")
    scopes: List[str] = Field(default=["read"], description="API Key scopes")
    rate_limit: str = Field(
        default="100/hour", description="Rate limit for the API Key"
    )
    expires_at: Optional[datetime] = Field(
        None, description="API Key expiration date"
    )


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    scopes: Optional[List[str]] = None
    rate_limit: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class ApiKeyRead(ApiKeyBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    created_by: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key: str  
    scopes: List[str]
    rate_limit: str
    expires_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiKeyUsage(BaseModel):
    api_key_id: uuid.UUID
    endpoint: str
    method: str
    ip_address: str
    user_agent: Optional[str]
    response_time: float
    status_code: int
    timestamp: datetime
