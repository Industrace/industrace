from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
import uuid

from app.models.area import Area
from app.schemas.area import AreaCreate, AreaUpdate


def create_area(db: Session, area_in: AreaCreate, tenant_id: uuid.UUID) -> Area:
    """Create a new area"""
    area_data = area_in.model_dump()
    area_data["tenant_id"] = tenant_id
    
    db_area = Area(**area_data)
    db.add(db_area)
    db.commit()
    db.refresh(db_area)
    return db_area


def get_area(db: Session, area_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Area]:
    """Get area by ID for specific tenant (excluding deleted)"""
    return db.query(Area).filter(
        and_(Area.id == area_id, Area.tenant_id == tenant_id, Area.deleted_at == None)
    ).first()


def get_areas(
    db: Session, 
    tenant_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 100,
    site_id: Optional[uuid.UUID] = None
) -> List[Area]:
    """Get list of areas for specific tenant (excluding deleted)"""
    query = db.query(Area).options(joinedload(Area.site)).filter(
        Area.tenant_id == tenant_id,
        Area.deleted_at == None
    )
    
    if site_id:
        query = query.filter(Area.site_id == site_id)
    
    return query.offset(skip).limit(limit).all()


def update_area(
    db: Session, 
    area_id: uuid.UUID, 
    area_update: AreaUpdate, 
    tenant_id: uuid.UUID
) -> Optional[Area]:
    """Update area"""
    db_area = get_area(db, area_id, tenant_id)
    if not db_area:
        return None
    
    update_data = area_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_area, field, value)
    
    db.commit()
    db.refresh(db_area)
    return db_area


def delete_area(db: Session, area_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
    """Soft delete area"""
    db_area = get_area(db, area_id, tenant_id)
    if not db_area:
        return False
    
    from datetime import datetime
    db_area.deleted_at = datetime.utcnow()
    db.commit()
    return True


def get_areas_trash(
    db: Session, 
    tenant_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 100
) -> List[Area]:
    """Get list of deleted areas for specific tenant"""
    query = db.query(Area).options(joinedload(Area.site)).filter(
        Area.tenant_id == tenant_id,
        Area.deleted_at != None
    )
    
    return query.offset(skip).limit(limit).all()


def restore_area(db: Session, area_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
    """Restore area from trash"""
    db_area = db.query(Area).filter(
        and_(Area.id == area_id, Area.tenant_id == tenant_id, Area.deleted_at != None)
    ).first()
    if not db_area:
        return False
    
    db_area.deleted_at = None
    db.commit()
    return True


def hard_delete_area(db: Session, area_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
    """Hard delete area (permanently remove from trash)"""
    db_area = db.query(Area).filter(
        and_(Area.id == area_id, Area.tenant_id == tenant_id, Area.deleted_at != None)
    ).first()
    if not db_area:
        return False
    
    db.delete(db_area)
    db.commit()
    return True


def get_areas_by_site(db: Session, site_id: uuid.UUID, tenant_id: uuid.UUID) -> List[Area]:
    """Get all areas for a specific site (excluding deleted)"""
    return db.query(Area).filter(
        and_(
            Area.site_id == site_id, 
            Area.tenant_id == tenant_id,
            Area.deleted_at == None
        )
    ).all()


def area_exists(db: Session, area_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
    """Check if area exists for specific tenant"""
    return db.query(Area).filter(
        and_(Area.id == area_id, Area.tenant_id == tenant_id)
    ).first() is not None 