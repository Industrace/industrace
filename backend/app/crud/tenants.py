# backend/crud/tenants.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
from app.models import Tenant, Site, AssetType, Asset, AssetConnection
from app.schemas.tenant import TenantCreate, TenantUpdate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_tenant(db: Session, tenant_id: uuid.UUID) -> Optional[Tenant]:
    """Retrieve a tenant by ID"""
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def get_tenant_by_slug(db: Session, slug: str) -> Optional[Tenant]:
    """Retrieve a tenant by slug"""
    return db.query(Tenant).filter(Tenant.slug == slug).first()


def get_tenants(db: Session, skip: int = 0, limit: int = 100) -> List[Tenant]:
    """List all tenants with pagination"""
    return db.query(Tenant).offset(skip).limit(limit).all()


def create_tenant(db: Session, tenant: TenantCreate) -> Tenant:
    """Create a new tenant"""
    db_tenant = Tenant(**tenant.model_dump())
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant


def update_tenant(
    db: Session, tenant_id: uuid.UUID, tenant_update: TenantUpdate
) -> Optional[Tenant]:
    """Update an existing tenant"""
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if db_tenant:
        for key, value in tenant_update.model_dump(exclude_unset=True).items():
            setattr(db_tenant, key, value)
        db.commit()
        db.refresh(db_tenant)
    return db_tenant


def delete_tenant(db: Session, tenant_id: uuid.UUID) -> bool:
    """Delete a tenant"""
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if db_tenant:
        db.delete(db_tenant)
        db.commit()
        return True
    return False


def get_tenant_statistics(db: Session, tenant_id: uuid.UUID) -> dict:
    """Get the statistics of a tenant"""
    stats = {
        "total_sites": db.query(Site).filter(Site.tenant_id == tenant_id).count(),
        "total_assets": db.query(Asset).filter(Asset.tenant_id == tenant_id).count(),
        "total_connections": db.query(AssetConnection)
        .filter(AssetConnection.tenant_id == tenant_id)
        .count(),
        "assets_by_status": {},
        "assets_by_type": {},
    }

    # Asset by status
    status_counts = (
        db.query(Asset.status, func.count(Asset.id))
        .filter(Asset.tenant_id == tenant_id)
        .group_by(Asset.status)
        .all()
    )

    stats["assets_by_status"] = {status: count for status, count in status_counts}

    # Asset by type
    type_counts = (
        db.query(AssetType.name, func.count(Asset.id))
        .join(Asset, Asset.asset_type_id == AssetType.id)
        .filter(Asset.tenant_id == tenant_id)
        .group_by(AssetType.name)
        .all()
    )

    stats["assets_by_type"] = {type_name: count for type_name, count in type_counts}

    return stats
