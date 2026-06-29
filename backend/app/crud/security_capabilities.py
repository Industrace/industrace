# backend/app/crud/security_capabilities.py
"""
CRUD operations for SecurityCapability
System-wide reference data (no tenant_id)
"""
from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
from app.models.security_capability import SecurityCapability
from app.schemas.security_capability import SecurityCapabilityCreate, SecurityCapabilityUpdate


def get_security_capability(
    db: Session,
    capability_id: uuid.UUID
) -> Optional[SecurityCapability]:
    """Get a single SecurityCapability by ID"""
    return db.query(SecurityCapability).filter(SecurityCapability.id == capability_id).first()


def get_security_capability_by_code(
    db: Session,
    code: str
) -> Optional[SecurityCapability]:
    """Get a SecurityCapability by code"""
    return db.query(SecurityCapability).filter(SecurityCapability.code == code).first()


def get_security_capabilities(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[SecurityCapability]:
    """Get all SecurityCapabilities"""
    return db.query(SecurityCapability).offset(skip).limit(limit).all()


def create_security_capability(
    db: Session,
    capability_in: SecurityCapabilityCreate
) -> SecurityCapability:
    """Create a new SecurityCapability"""
    db_capability = SecurityCapability(**capability_in.model_dump())
    db.add(db_capability)
    db.commit()
    db.refresh(db_capability)
    return db_capability


def update_security_capability(
    db: Session,
    capability_id: uuid.UUID,
    capability_in: SecurityCapabilityUpdate
) -> Optional[SecurityCapability]:
    """Update a SecurityCapability"""
    db_capability = get_security_capability(db, capability_id)
    if not db_capability:
        return None
    
    update_data = capability_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_capability, field, value)
    
    db.commit()
    db.refresh(db_capability)
    return db_capability


def delete_security_capability(
    db: Session,
    capability_id: uuid.UUID
) -> bool:
    """Delete a SecurityCapability"""
    db_capability = get_security_capability(db, capability_id)
    if not db_capability:
        return False
    
    db.delete(db_capability)
    db.commit()
    return True

