# backend/app/crud/asset_zone_memberships.py
"""
CRUD operations for AssetZoneMembership
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
from app.models.asset_zone_membership import AssetZoneMembership
from app.schemas.asset_zone_membership import AssetZoneMembershipCreate, AssetZoneMembershipUpdate


def get_asset_zone_membership(
    db: Session,
    membership_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> Optional[AssetZoneMembership]:
    """Get a single AssetZoneMembership by ID"""
    return (
        db.query(AssetZoneMembership)
        .filter(
            AssetZoneMembership.id == membership_id,
            AssetZoneMembership.tenant_id == tenant_id,
            AssetZoneMembership.deleted_at.is_(None)
        )
        .first()
    )


def get_asset_zone_memberships(
    db: Session,
    tenant_id: uuid.UUID,
    asset_id: Optional[uuid.UUID] = None,
    security_zone_id: Optional[uuid.UUID] = None,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[AssetZoneMembership]:
    """Get AssetZoneMemberships with optional filters"""
    query = (
        db.query(AssetZoneMembership)
        .filter(
            AssetZoneMembership.tenant_id == tenant_id,
            AssetZoneMembership.deleted_at.is_(None)
        )
    )
    
    if asset_id:
        query = query.filter(AssetZoneMembership.asset_id == asset_id)
    
    if security_zone_id:
        query = query.filter(AssetZoneMembership.security_zone_id == security_zone_id)
    
    if role:
        query = query.filter(AssetZoneMembership.role == role)
    
    return query.offset(skip).limit(limit).all()


def get_asset_zone_memberships_by_asset(
    db: Session,
    asset_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> List[AssetZoneMembership]:
    """Get all zone memberships for an asset"""
    return (
        db.query(AssetZoneMembership)
        .filter(
            AssetZoneMembership.asset_id == asset_id,
            AssetZoneMembership.tenant_id == tenant_id,
            AssetZoneMembership.deleted_at.is_(None)
        )
        .all()
    )


def get_asset_zone_memberships_by_zone(
    db: Session,
    security_zone_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> List[AssetZoneMembership]:
    """Get all asset memberships for a security zone"""
    return (
        db.query(AssetZoneMembership)
        .filter(
            AssetZoneMembership.security_zone_id == security_zone_id,
            AssetZoneMembership.tenant_id == tenant_id,
            AssetZoneMembership.deleted_at.is_(None)
        )
        .all()
    )


def create_asset_zone_membership(
    db: Session,
    membership_in: AssetZoneMembershipCreate,
    tenant_id: uuid.UUID
) -> AssetZoneMembership:
    """Create a new AssetZoneMembership"""
    # Get all fields, including None values
    membership_dict = membership_in.model_dump()
    
    # Ensure security_zone_id is present and not None (should be set by router)
    if membership_dict.get('security_zone_id') is None:
        raise ValueError("security_zone_id is required for AssetZoneMembership")
    
    # Ensure asset_id is present
    asset_id = membership_dict.get('asset_id')
    if asset_id is None:
        raise ValueError("asset_id is required for AssetZoneMembership")
    
    # Convert asset_id to UUID if it's a string
    if isinstance(asset_id, str):
        try:
            asset_id = uuid.UUID(asset_id)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid asset_id format: {asset_id}. Error: {str(e)}")
    
    # Ensure role is present
    if not membership_dict.get('role'):
        raise ValueError("role is required for AssetZoneMembership")
    
    # Remove None values for optional fields only (not for required ones)
    optional_fields = ['interface_scope', 'sl_target', 'notes']
    for field in optional_fields:
        if field in membership_dict and membership_dict[field] is None:
            del membership_dict[field]
    
    # Create the membership record
    try:
        db_membership = AssetZoneMembership(
            tenant_id=tenant_id,
            asset_id=asset_id,
            security_zone_id=membership_dict['security_zone_id'],
            role=membership_dict['role'],
            interface_scope=membership_dict.get('interface_scope'),
            sl_target=membership_dict.get('sl_target'),
            notes=membership_dict.get('notes')
        )
        db.add(db_membership)
        db.commit()
        db.refresh(db_membership)
        return db_membership
    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        raise ValueError(f"Error creating AssetZoneMembership: {str(e)}\nDetails: {error_details}")


def update_asset_zone_membership(
    db: Session,
    membership_id: uuid.UUID,
    membership_in: AssetZoneMembershipUpdate,
    tenant_id: uuid.UUID
) -> Optional[AssetZoneMembership]:
    """Update an AssetZoneMembership"""
    db_membership = get_asset_zone_membership(db, membership_id, tenant_id)
    if not db_membership:
        return None
    
    update_data = membership_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_membership, field, value)
    
    db.commit()
    db.refresh(db_membership)
    return db_membership


def delete_asset_zone_membership(
    db: Session,
    membership_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> bool:
    """Soft delete an AssetZoneMembership"""
    db_membership = get_asset_zone_membership(db, membership_id, tenant_id)
    if not db_membership:
        return False
    
    from datetime import datetime
    db_membership.deleted_at = datetime.utcnow()
    db.commit()
    return True


def check_membership_exists(
    db: Session,
    asset_id: uuid.UUID,
    security_zone_id: uuid.UUID,
    role: str,
    tenant_id: uuid.UUID,
    exclude_id: Optional[uuid.UUID] = None
) -> bool:
    """Check if a membership with the same asset, zone, and role already exists"""
    query = (
        db.query(AssetZoneMembership)
        .filter(
            AssetZoneMembership.asset_id == asset_id,
            AssetZoneMembership.security_zone_id == security_zone_id,
            AssetZoneMembership.role == role,
            AssetZoneMembership.tenant_id == tenant_id,
            AssetZoneMembership.deleted_at.is_(None)
        )
    )
    
    if exclude_id:
        query = query.filter(AssetZoneMembership.id != exclude_id)
    
    return query.first() is not None

