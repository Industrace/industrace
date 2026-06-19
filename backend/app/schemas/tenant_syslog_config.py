from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class TenantSyslogConfigBase(BaseModel):
    host: Optional[str] = None
    port: int = Field(default=514, ge=1, le=65535)
    protocol: str = Field(default="udp", pattern="^(udp|tcp)$")
    facility: int = Field(default=16, ge=0, le=23)
    enabled: bool = False


class TenantSyslogConfigCreate(TenantSyslogConfigBase):
    pass


class TenantSyslogConfigUpdate(TenantSyslogConfigBase):
    host: Optional[str] = None
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    protocol: Optional[str] = None  # udp | tcp, validated in router
    facility: Optional[int] = Field(default=None, ge=0, le=23)
    enabled: Optional[bool] = None


class TenantSyslogConfigRead(TenantSyslogConfigBase):
    id: UUID
    tenant_id: UUID

    class Config:
        from_attributes = True
