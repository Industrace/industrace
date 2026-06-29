import uuid
from typing import List
from datetime import datetime
import csv
from fastapi import UploadFile, File, Body
from fastapi.responses import StreamingResponse
from io import StringIO
import pandas as pd
from sqlalchemy.exc import IntegrityError

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Location, Site
from app.schemas import Location as LocationSchema, LocationCreate, LocationRead
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.crud import locations as crud_locations
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.audit_decorator import audit_log_action
from app.schemas.contact import Contact as ContactSchema
from app.schemas.location import LocationUpdate

router = APIRouter(
    prefix="/locations",
    tags=["locations"],
    dependencies=[Depends(require_section_access("locations"))],
)


@router.get("/trash", response_model=List[LocationRead])
def list_locations_trash(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Location)
        .filter(
            Location.tenant_id == current_user.tenant_id, Location.deleted_at != None
        )
        .all()
    )


@router.post("/bulk-update")
def bulk_update_locations(
    ids: List[uuid.UUID] = Body(...),
    fields: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = []
    errors = []
    for location_id in ids:
        location = (
            db.query(Location)
            .filter(
                Location.id == location_id,
                Location.tenant_id == current_user.tenant_id,
                Location.deleted_at == None,
            )
            .first()
        )
        if not location:
            errors.append({"id": str(location_id), "error": "Location not found"})
            continue
        for key, value in fields.items():
            if hasattr(location, key):
                setattr(location, key, value)
        db.commit()
        updated.append(str(location_id))
    return {"updated": updated, "errors": errors}


@router.post("", response_model=LocationSchema)
@audit_log_action("create", "Location", model_class=Location)
def create_location(
    location: LocationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud_locations.create_location(db, location, current_user.tenant_id)


@router.get("", response_model=List[LocationRead])
def list_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    locations = crud_locations.get_locations(db, current_user.tenant_id, skip, limit)
    
    # Costruisci manualmente la risposta con il nome dell'area
    result = []
    for location in locations:
        location_data = {
            "id": location.id,
            "tenant_id": location.tenant_id,
            "site_id": location.site_id,
            "area_id": location.area_id,
            "name": location.name,
            "code": location.code,
            "description": location.description,
            "notes": location.notes,
            "created_at": location.created_at,
            "updated_at": location.updated_at,
            "floorplan": location.floorplan,
            "site": location.site,
            "area_name": location.area.name if location.area else None
        }
        result.append(location_data)
    
    return result


@router.put("/{location_id}", response_model=LocationSchema)
@audit_log_action("update", "Location", model_class=Location)
def update_location(
    location_id: uuid.UUID,
    location: LocationUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_location = crud_locations.get_location(db, location_id)
    if not db_location or db_location.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.LOCATION_NOT_FOUND
        )
    # Update only provided fields
    update_data = location.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_location, key, value)
    db.commit()
    db.refresh(db_location)
    return db_location


@router.delete("/{location_id}")
@audit_log_action("soft_delete", "Location", model_class=Location)
def soft_delete_location(
    location_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_location = (
        db.query(Location)
        .filter(
            Location.id == location_id,
            Location.tenant_id == current_user.tenant_id,
            Location.deleted_at == None,
        )
        .first()
    )
    if not db_location:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.LOCATION_NOT_FOUND
        )
    db_location.deleted_at = datetime.utcnow()
    db.commit()


@router.delete("/{location_id}/contacts/{contact_id}", status_code=204)
def delete_location_contact(
    location_id: uuid.UUID,
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    location = (
        db.query(Location)
        .filter(
            Location.id == location_id, Location.tenant_id == current_user.tenant_id
        )
        .first()
    )
    if not location:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.LOCATION_NOT_FOUND
        )
    location.contacts = [c for c in location.contacts if c.id != contact_id]
    db.commit()
    return None


@router.get("/{location_id}/contacts", response_model=List[ContactSchema])
def list_location_contacts(
    location_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    location = (
        db.query(Location)
        .filter(
            Location.id == location_id, Location.tenant_id == current_user.tenant_id
        )
        .first()
    )
    if not location:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.LOCATION_NOT_FOUND
        )
    return [ContactSchema.model_validate(c) for c in location.contacts]


@router.put("/{location_id}/contacts", response_model=List[ContactSchema])
def update_location_contacts(
    location_id: uuid.UUID,
    contact_ids: List[uuid.UUID],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.crud.locations import set_location_contacts

    location = set_location_contacts(
        db, location_id, contact_ids, current_user.tenant_id
    )
    if not location:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.LOCATION_NOT_FOUND
        )
    return [ContactSchema.model_validate(c) for c in location.contacts]


@router.patch("/{location_id}/restore")
@audit_log_action("restore", "Location", model_class=Location)
def restore_location(
    location_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_location = (
        db.query(Location)
        .filter(
            Location.id == location_id,
            Location.tenant_id == current_user.tenant_id,
            Location.deleted_at != None,
        )
        .first()
    )
    if not db_location:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.LOCATION_NOT_FOUND
        )
    db_location.deleted_at = None
    db.commit()


@router.delete("/{location_id}/hard")
@audit_log_action("hard_delete", "Location", model_class=Location)
def hard_delete_location(
    location_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_location = (
        db.query(Location)
        .filter(
            Location.id == location_id,
            Location.tenant_id == current_user.tenant_id,
            Location.deleted_at != None,
        )
        .first()
    )
    if not db_location:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.LOCATION_NOT_FOUND
        )
    db.delete(db_location)
    db.commit()


@router.get("/{location_id}", response_model=LocationRead)
def get_location(
    location_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    location = (
        db.query(Location)
        .filter(
            Location.id == location_id,
            Location.tenant_id == current_user.tenant_id,
            Location.deleted_at == None,
        )
        .first()
    )
    if not location:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.LOCATION_NOT_FOUND
        )
    return location
