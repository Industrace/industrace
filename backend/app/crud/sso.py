# backend/app/crud/sso.py
from typing import Optional
from sqlalchemy.orm import Session
import uuid
from app.models.tenant_sso_config import TenantSSOConfig
from app.schemas.sso import TenantSSOConfigCreate, TenantSSOConfigUpdate
from app.services.sso_encryption import encrypt_secret


def get_sso_config(
    db: Session,
    tenant_id: uuid.UUID
) -> Optional[TenantSSOConfig]:
    """Get SSO configuration for a tenant"""
    return db.query(TenantSSOConfig).filter(
        TenantSSOConfig.tenant_id == tenant_id
    ).first()


def create_sso_config(
    db: Session,
    sso_config: TenantSSOConfigCreate,
    tenant_id: uuid.UUID,
    created_by: Optional[uuid.UUID] = None
) -> TenantSSOConfig:
    """Create SSO configuration for a tenant"""
    # Check if already exists
    existing = get_sso_config(db, tenant_id)
    if existing:
        raise ValueError("SSO configuration already exists for this tenant")
    
    # Encrypt client secret
    config_data = sso_config.dict()
    client_secret = config_data.pop("client_secret")
    config_data["client_secret_encrypted"] = encrypt_secret(client_secret)
    
    db_sso_config = TenantSSOConfig(
        **config_data,
        tenant_id=tenant_id,
        created_by=created_by
    )
    db.add(db_sso_config)
    db.commit()
    db.refresh(db_sso_config)
    return db_sso_config


def update_sso_config(
    db: Session,
    tenant_id: uuid.UUID,
    sso_config_update: TenantSSOConfigUpdate
) -> Optional[TenantSSOConfig]:
    """Update SSO configuration for a tenant"""
    db_sso_config = get_sso_config(db, tenant_id)
    if not db_sso_config:
        return None
    
    update_data = sso_config_update.dict(exclude_unset=True)
    
    # Encrypt client_secret if provided AND not empty
    # If client_secret is empty string, preserve existing secret (don't update it)
    if "client_secret" in update_data:
        client_secret = update_data.pop("client_secret")
        # Only update secret if a non-empty value is provided
        if client_secret and client_secret.strip():
            update_data["client_secret_encrypted"] = encrypt_secret(client_secret)
        # If empty string, don't include in update_data (preserve existing secret)
    
    for field, value in update_data.items():
        setattr(db_sso_config, field, value)
    
    db.commit()
    db.refresh(db_sso_config)
    return db_sso_config


def delete_sso_config(
    db: Session,
    tenant_id: uuid.UUID
) -> bool:
    """Delete SSO configuration for a tenant"""
    db_sso_config = get_sso_config(db, tenant_id)
    if not db_sso_config:
        return False
    
    db.delete(db_sso_config)
    db.commit()
    return True

