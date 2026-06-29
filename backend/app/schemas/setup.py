from pydantic import BaseModel, EmailStr
from typing import Optional
from app.schemas.schema_mixins import SetupFieldsMixin


class SetupStatus(BaseModel):
    """Stato del sistema per il setup"""
    is_configured: bool
    tenant_count: int
    user_count: int
    role_count: int
    database_connected: bool
    error: Optional[str] = None


class SetupRequest(SetupFieldsMixin, BaseModel):
    """Dati per l'inizializzazione del sistema"""
    tenant_name: str
    tenant_slug: str
    admin_name: str
    admin_email: EmailStr
    admin_password: str
    language: str = "en"
    iec62443_enabled: bool = True


class SetupResponse(BaseModel):
    """Risposta dell'inizializzazione"""
    success: bool
    message: str
    tenant_id: str
    admin_user_id: str
