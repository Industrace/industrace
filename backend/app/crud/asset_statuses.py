from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.models import AssetStatus
from app.schemas.asset_status import AssetStatusCreate, AssetStatusUpdate


def create_asset_status(
    db: Session, status_in: AssetStatusCreate, tenant_id: uuid.UUID
) -> AssetStatus:
    """Create a new asset status"""
    status = AssetStatus(**status_in.model_dump(), tenant_id=tenant_id)
    db.add(status)
    db.commit()
    db.refresh(status)
    return status


def get_asset_status(
    db: Session, status_id: uuid.UUID, tenant_id: uuid.UUID
) -> Optional[AssetStatus]:
    """Retrieve an asset status by ID"""
    return (
        db.query(AssetStatus)
        .filter(AssetStatus.id == status_id, AssetStatus.tenant_id == tenant_id)
        .first()
    )


def list_asset_statuses(
    db: Session, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[AssetStatus]:
    """List all asset statuses of a tenant with pagination"""
    return (
        db.query(AssetStatus)
        .filter(AssetStatus.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_asset_status(
    db: Session, status: AssetStatus, update_data: AssetStatusUpdate
) -> AssetStatus:
    """Update an existing asset status"""
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(status, key, value)
    db.commit()
    db.refresh(status)
    return status


def delete_asset_status(db: Session, status: AssetStatus) -> None:
    """Delete an asset status"""
    db.delete(status)
    db.commit()
