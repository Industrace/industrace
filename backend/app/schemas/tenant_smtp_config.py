from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class TenantSMTPConfigBase(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    from_email: Optional[EmailStr] = None
    use_tls: bool = True
    provider: Optional[str] = "smtp"


class TenantSMTPConfigCreate(TenantSMTPConfigBase):
    # I campi principali sono obbligatori per la creazione
    host: str
    port: int
    username: str
    password: str
    from_email: EmailStr


class TenantSMTPConfigUpdate(TenantSMTPConfigBase):
    pass


class TenantSMTPConfigRead(TenantSMTPConfigBase):
    id: UUID
    tenant_id: UUID

    class Config:
        from_attributes = True
