# backend/app/crud/asset_capabilities.py
"""
CRUD operations for AssetCapability
"""
from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
from app.models.asset_capability import AssetCapability
from app.schemas.asset_capability import AssetCapabilityCreate, AssetCapabilityUpdate, AssetCapabilityBase


def get_asset_capability(
    db: Session,
    capability_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> Optional[AssetCapability]:
    """Get a single AssetCapability by ID"""
    return (
        db.query(AssetCapability)
        .filter(
            AssetCapability.id == capability_id,
            AssetCapability.tenant_id == tenant_id
        )
        .first()
    )


def get_asset_capabilities(
    db: Session,
    tenant_id: uuid.UUID,
    asset_id: Optional[uuid.UUID] = None,
    capability_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100
) -> List[AssetCapability]:
    """Get AssetCapabilities with optional filters"""
    query = db.query(AssetCapability).filter(AssetCapability.tenant_id == tenant_id)
    
    if asset_id:
        query = query.filter(AssetCapability.asset_id == asset_id)
    
    if capability_id:
        query = query.filter(AssetCapability.capability_id == capability_id)
    
    return query.offset(skip).limit(limit).all()


def get_asset_capabilities_by_asset(
    db: Session,
    asset_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> List[AssetCapability]:
    """Get all capabilities for an asset"""
    return (
        db.query(AssetCapability)
        .filter(
            AssetCapability.asset_id == asset_id,
            AssetCapability.tenant_id == tenant_id
        )
        .all()
    )


def create_asset_capability(
    db: Session,
    capability_in: AssetCapabilityBase,
    tenant_id: uuid.UUID
) -> AssetCapability:
    """Create a new AssetCapability"""
    db_capability = AssetCapability(
        tenant_id=tenant_id,
        **capability_in.model_dump()
    )
    db.add(db_capability)
    db.commit()
    db.refresh(db_capability)
    return db_capability


def update_asset_capability(
    db: Session,
    capability_id: uuid.UUID,
    capability_in: AssetCapabilityUpdate,
    tenant_id: uuid.UUID
) -> Optional[AssetCapability]:
    """Update an AssetCapability"""
    db_capability = get_asset_capability(db, capability_id, tenant_id)
    if not db_capability:
        return None
    
    update_data = capability_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_capability, field, value)
    
    db.commit()
    db.refresh(db_capability)
    return db_capability


def delete_asset_capability(
    db: Session,
    capability_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> bool:
    """Delete an AssetCapability"""
    db_capability = get_asset_capability(db, capability_id, tenant_id)
    if not db_capability:
        return False
    
    db.delete(db_capability)
    db.commit()
    return True

