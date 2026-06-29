from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.area import AreaCreate, AreaUpdate, AreaRead, AreaList
from app.crud import areas as crud_areas
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.services.audit_decorator import audit_log_action
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode

router = APIRouter(
    prefix="/areas",
    tags=["areas"],
    dependencies=[Depends(require_section_access("areas"))],
)


@router.post("", response_model=AreaRead)
@audit_log_action("create", "Area")
def create_area(
    area_in: AreaCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new area"""
    return crud_areas.create_area(db, area_in, current_user.tenant_id)


@router.get("", response_model=List[AreaList])
def list_areas(
    skip: int = 0,
    limit: int = 100,
    site_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all areas for the current tenant"""
    areas = crud_areas.get_areas(db, current_user.tenant_id, skip, limit, site_id)
    
    # Convert to AreaList format with site name
    result = []
    for area in areas:
        result.append(AreaList(
            id=area.id,
            name=area.name,
            code=area.code,
            typology=area.typology,
            site_id=area.site_id,
            site_name=area.site.name if area.site else None,
            created_at=area.created_at,
            updated_at=area.updated_at
        ))
    
    return result


@router.get("/{area_id}", response_model=AreaRead)
def get_area(
    area_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get area by ID"""
    area = crud_areas.get_area(db, area_id, current_user.tenant_id)
    if not area:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.AREA_NOT_FOUND)
    return area


@router.put("/{area_id}", response_model=AreaRead)
@audit_log_action("update", "Area")
def update_area(
    area_id: uuid.UUID,
    area_update: AreaUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update area"""
    area = crud_areas.update_area(db, area_id, area_update, current_user.tenant_id)
    if not area:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.AREA_NOT_FOUND)
    return area


@router.delete("/{area_id}")
@audit_log_action("soft_delete", "Area")
def delete_area(
    area_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft delete area"""
    success = crud_areas.delete_area(db, area_id, current_user.tenant_id)
    if not success:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.AREA_NOT_FOUND)
    return {"detail": "Area moved to trash"}


@router.get("/trash", response_model=List[AreaList])
def list_areas_trash(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all deleted areas for the current tenant"""
    areas = crud_areas.get_areas_trash(db, current_user.tenant_id, skip, limit)
    
    # Convert to AreaList format with site name
    result = []
    for area in areas:
        result.append(AreaList(
            id=area.id,
            name=area.name,
            code=area.code,
            typology=area.typology,
            site_id=area.site_id,
            site_name=area.site.name if area.site else None,
            created_at=area.created_at,
            updated_at=area.updated_at
        ))
    
    return result


@router.patch("/{area_id}/restore")
@audit_log_action("restore", "Area")
def restore_area(
    area_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Restore area from trash"""
    success = crud_areas.restore_area(db, area_id, current_user.tenant_id)
    if not success:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.AREA_NOT_FOUND)
    return {"detail": "Area restored"}


@router.delete("/{area_id}/hard")
@audit_log_action("hard_delete", "Area")
def hard_delete_area(
    area_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hard delete area (permanently remove from trash)"""
    success = crud_areas.hard_delete_area(db, area_id, current_user.tenant_id)
    if not success:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.AREA_NOT_FOUND)
    return {"detail": "Area permanently deleted"}


@router.delete("/trash/empty")
@audit_log_action("empty_trash", "Area")
def empty_areas_trash(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Empty areas trash (permanently delete all areas in trash)"""
    areas = crud_areas.get_areas_trash(db, current_user.tenant_id, skip=0, limit=1000)
    count = 0
    for area in areas:
        crud_areas.hard_delete_area(db, area.id, current_user.tenant_id)
        count += 1
    return {"detail": f"Trash emptied: {count} areas deleted"}


@router.get("/site/{site_id}", response_model=List[AreaList])
def get_areas_by_site(
    site_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all areas for a specific site"""
    areas = crud_areas.get_areas_by_site(db, site_id, current_user.tenant_id)
    
    # Convert to AreaList format
    result = []
    for area in areas:
        result.append(AreaList(
            id=area.id,
            name=area.name,
            code=area.code,
            typology=area.typology,
            site_id=area.site_id,
            site_name=area.site.name if area.site else None,
            created_at=area.created_at,
            updated_at=area.updated_at
        ))
    
    return result 