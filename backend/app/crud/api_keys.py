# backend/crud/api_keys.py
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import json
from datetime import datetime
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyUpdate
from app.services.api_auth import generate_api_key, hash_api_key


def create_api_key(
    db: Session, api_key_data: ApiKeyCreate, tenant_id: uuid.UUID, created_by: uuid.UUID
) -> tuple[ApiKey, str]:
    """Create a new API Key and return both the object and the raw key"""
    # Generate the key
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)

    # Create the API Key object
    db_api_key = ApiKey(
        tenant_id=tenant_id,
        name=api_key_data.name,
        key_hash=key_hash,
        scopes=json.dumps(api_key_data.scopes),
        rate_limit=api_key_data.rate_limit,
        expires_at=api_key_data.expires_at,
        created_by=created_by,
    )

    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)

    return db_api_key, raw_key


def get_api_key(
    db: Session, api_key_id: uuid.UUID, tenant_id: uuid.UUID
) -> Optional[ApiKey]:
    """Retrieve an API Key by ID and tenant"""
    return (
        db.query(ApiKey)
        .filter(ApiKey.id == api_key_id, ApiKey.tenant_id == tenant_id)
        .first()
    )


def get_api_keys_by_tenant(
    db: Session, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[ApiKey]:
    """Retrieve all API Keys for a tenant"""
    return (
        db.query(ApiKey)
        .filter(ApiKey.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_api_key(
    db: Session,
    api_key_id: uuid.UUID,
    tenant_id: uuid.UUID,
    api_key_update: ApiKeyUpdate,
) -> Optional[ApiKey]:
    """Update an API Key"""
    api_key = get_api_key(db, api_key_id, tenant_id)
    if not api_key:
        return None

    update_data = api_key_update.model_dump(exclude_unset=True)

    # Handle scopes as JSON
    if "scopes" in update_data:
        update_data["scopes"] = json.dumps(update_data["scopes"])

    for field, value in update_data.items():
        setattr(api_key, field, value)

    db.commit()
    db.refresh(api_key)
    return api_key


def delete_api_key(db: Session, api_key_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
    """Delete an API Key"""
    api_key = get_api_key(db, api_key_id, tenant_id)
    if not api_key:
        return False

    db.delete(api_key)
    db.commit()
    return True


def deactivate_api_key(
    db: Session, api_key_id: uuid.UUID, tenant_id: uuid.UUID
) -> Optional[ApiKey]:
    """Deactivate an API Key"""
    api_key = get_api_key(db, api_key_id, tenant_id)
    if not api_key:
        return None

    api_key.is_active = False
    db.commit()
    db.refresh(api_key)
    return api_key


def activate_api_key(
    db: Session, api_key_id: uuid.UUID, tenant_id: uuid.UUID
) -> Optional[ApiKey]:
    """Reactivate an API Key"""
    api_key = get_api_key(db, api_key_id, tenant_id)
    if not api_key:
        return None

    api_key.is_active = True
    db.commit()
    db.refresh(api_key)
    return api_key


def get_api_key_by_hash(db: Session, key_hash: str) -> Optional[ApiKey]:
    """Retrieve an API Key by hash"""
    return db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()


def get_expired_api_keys(db: Session) -> List[ApiKey]:
    """Retrieve all expired API Keys"""
    return (
        db.query(ApiKey)
        .filter(ApiKey.expires_at < datetime.utcnow(), ApiKey.is_active == True)
        .all()
    )


def cleanup_expired_api_keys(db: Session) -> int:
    """Deactivate all expired API Keys"""
    expired_keys = get_expired_api_keys(db)
    count = 0

    for key in expired_keys:
        key.is_active = False
        count += 1

    db.commit()
    return count
