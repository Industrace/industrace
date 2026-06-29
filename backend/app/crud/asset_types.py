# backend/crud/asset_types.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import AssetType
from app.schemas import AssetType as AssetTypeBase, AssetTypeCreate, AssetTypeUpdate
import uuid
from typing import List, Optional


def get_asset_type(db: Session, asset_type_id: uuid.UUID) -> Optional[AssetTypeBase]:
    """Retrieve an asset type by ID"""
    return db.query(AssetType).filter(AssetType.id == asset_type_id).first()


def get_asset_types(
    db: Session, tenant_id: Optional[uuid.UUID] = None, skip: int = 0, limit: int = 100
):
    """List all asset types of a tenant with pagination"""
    from sqlalchemy import func
    from app.models import Asset

    query = db.query(AssetType)
    if tenant_id:
        query = query.filter(
            or_(AssetType.tenant_id == tenant_id, AssetType.tenant_id.is_(None))
        )
    else:
        query = query.filter(AssetType.tenant_id.is_(None))
    asset_types = query.offset(skip).limit(limit).all()
    # Calculate the asset count for each type
    result = []
    for at in asset_types:
        asset_count = db.query(func.count(Asset.id)).filter(
            Asset.asset_type_id == at.id
        )
        if tenant_id:
            asset_count = asset_count.filter(Asset.tenant_id == tenant_id)
        asset_count = asset_count.scalar()
        at_dict = at.__dict__.copy()
        at_dict["asset_count"] = asset_count
        result.append(at_dict)
    return result


def get_asset_types_by_category(
    db: Session, category: str, tenant_id: Optional[uuid.UUID] = None
) -> List[AssetTypeBase]:
    """Retrieve all asset types by category"""
    query = db.query(AssetType).filter(AssetType.category == category)
    if tenant_id:
        query = query.filter(
            or_(AssetType.tenant_id == tenant_id, AssetType.tenant_id.is_(None))
        )
    else:
        query = query.filter(AssetType.tenant_id.is_(None))
    return query.all()


def create_asset_type(
    db: Session, asset_type: AssetTypeCreate, tenant_id: Optional[uuid.UUID] = None
) -> AssetType:
    """Create a new asset type"""
    db_asset_type = AssetType(
        tenant_id=tenant_id, **asset_type.model_dump(exclude_unset=True)
    )
    db.add(db_asset_type)
    db.commit()
    db.refresh(db_asset_type)
    return db_asset_type


def update_asset_type(
    db: Session, asset_type_id: uuid.UUID, asset_type_update: AssetTypeUpdate
) -> Optional[AssetType]:
    """Update an existing asset type"""
    db_asset_type = db.query(AssetType).filter(AssetType.id == asset_type_id).first()
    if db_asset_type:
        for key, value in asset_type_update.model_dump(exclude_unset=True).items():
            setattr(db_asset_type, key, value)
        db.commit()
        db.refresh(db_asset_type)
    return db_asset_type


def delete_asset_type(db: Session, asset_type_id: uuid.UUID) -> bool:
    """Delete an asset type"""
    db_asset_type = db.query(AssetType).filter(AssetType.id == asset_type_id).first()
    if db_asset_type:
        db.delete(db_asset_type)
        db.commit()
        return True
    return False
