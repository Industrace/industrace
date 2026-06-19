from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from app.schemas.validators import *


class SetupStatus(BaseModel):
    """Stato del sistema per il setup"""
    is_configured: bool
    tenant_count: int
    user_count: int
    role_count: int
    database_connected: bool
    error: Optional[str] = None


class SetupRequest(BaseModel):
    """Dati per l'inizializzazione del sistema"""
    tenant_name: str
    tenant_slug: str
    admin_name: str
    admin_email: EmailStr
    admin_password: str
    language: str = "en"
    iec62443_enabled: bool = True
    
    # Validators
    _validate_tenant_slug = validator('tenant_slug', allow_reuse=True)(validate_tenant_slug)
    _validate_admin_password = validator('admin_password', allow_reuse=True)(validate_password)


class SetupResponse(BaseModel):
    """Risposta dell'inizializzazione"""
    success: bool
    message: str
    tenant_id: str
    admin_user_id: str 