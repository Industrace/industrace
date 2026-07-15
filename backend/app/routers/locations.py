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
from app.models import User, Location, Site, Area
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


@router.get("/export")
def export_locations_csv(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    locations = (
        db.query(Location)
        .filter(
            Location.tenant_id == current_user.tenant_id,
            Location.deleted_at == None,
        )
        .all()
    )
    site_map = {
        s.id: s.code
        for s in db.query(Site)
        .filter(Site.tenant_id == current_user.tenant_id, Site.deleted_at == None)
        .all()
    }
    area_map = {
        a.id: a.name
        for a in db.query(Area)
        .filter(Area.tenant_id == current_user.tenant_id, Area.deleted_at == None)
        .all()
    }

    def iter_csv():
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["site_code", "name", "code", "description", "area", "notes"]
        )
        for loc in locations:
            writer.writerow(
                [
                    site_map.get(loc.site_id, ""),
                    loc.name or "",
                    loc.code or "",
                    loc.description or "",
                    area_map.get(loc.area_id, "") if loc.area_id else "",
                    loc.notes or "",
                ]
            )
        output.seek(0)
        yield output.read()

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=locations.csv"},
    )


def _resolve_location_import_row(row, db, tenant_id):
    site_code = row.get("site_code")
    name = row.get("name")
    code = row.get("code")
    missing = []
    if site_code is None or str(site_code).strip() == "":
        missing.append("site_code")
    if name is None or str(name).strip() == "":
        missing.append("name")
    if missing:
        return None, f"Missing required fields: {', '.join(missing)}"

    site = (
        db.query(Site)
        .filter(
            Site.tenant_id == tenant_id,
            Site.code == str(site_code).strip(),
            Site.deleted_at == None,
        )
        .first()
    )
    if not site:
        return None, f"Site not found for code: {site_code}"

    area_id = None
    area_name = row.get("area")
    if area_name is not None and str(area_name).strip() != "":
        area = (
            db.query(Area)
            .filter(
                Area.tenant_id == tenant_id,
                Area.site_id == site.id,
                Area.name == str(area_name).strip(),
                Area.deleted_at == None,
            )
            .first()
        )
        if not area:
            return None, f"Area not found: {area_name} (site {site_code})"
        area_id = area.id

    description = row.get("description")
    if description is None or str(description).strip() == "":
        description = ""

    payload = {
        "site_id": site.id,
        "area_id": area_id,
        "name": str(name).strip(),
        "code": str(code).strip() if code is not None and str(code).strip() != "" else None,
        "description": str(description),
        "notes": row.get("notes"),
    }
    return payload, None


@router.post("/import/xlsx/preview")
def import_locations_xlsx_preview(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file.file, dtype=str)
            df = df.where(pd.notnull(df), None)
        else:
            df = pd.read_excel(file.file)
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}

    to_create, to_update, errors = [], [], []
    for idx, row in df.iterrows():
        payload, err = _resolve_location_import_row(row, db, current_user.tenant_id)
        if err:
            errors.append({"row": int(idx) + 2, "error": err})
            continue

        lookup = None
        if payload["code"]:
            lookup = (
                db.query(Location)
                .filter(
                    Location.tenant_id == current_user.tenant_id,
                    Location.code == payload["code"],
                    Location.deleted_at == None,
                )
                .first()
            )
        if not lookup:
            lookup = (
                db.query(Location)
                .filter(
                    Location.tenant_id == current_user.tenant_id,
                    Location.site_id == payload["site_id"],
                    Location.name == payload["name"],
                    Location.deleted_at == None,
                )
                .first()
            )

        if lookup:
            diff = {}
            for field in ["name", "code", "description", "notes", "area_id"]:
                new = payload[field]
                old = getattr(lookup, field)
                if str(old or "") != str(new or ""):
                    diff[field] = {"old": old, "new": new}
            if diff:
                to_update.append({"code": payload["code"] or lookup.code, "name": payload["name"], "diff": diff})
        else:
            to_create.append(
                {
                    "site_code": row.get("site_code"),
                    "name": payload["name"],
                    "code": payload["code"],
                    "description": payload["description"],
                    "area": row.get("area"),
                    "notes": payload["notes"],
                }
            )
    return {"to_create": to_create, "to_update": to_update, "errors": errors}


@router.post("/import/xlsx/confirm")
def import_locations_xlsx_confirm(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file.file, dtype=str)
            df = df.where(pd.notnull(df), None)
        else:
            df = pd.read_excel(file.file)
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}

    created, updated, errors = [], [], []
    for idx, row in df.iterrows():
        payload, err = _resolve_location_import_row(row, db, current_user.tenant_id)
        if err:
            errors.append({"row": int(idx) + 2, "error": err})
            continue

        lookup = None
        if payload["code"]:
            lookup = (
                db.query(Location)
                .filter(
                    Location.tenant_id == current_user.tenant_id,
                    Location.code == payload["code"],
                    Location.deleted_at == None,
                )
                .first()
            )
        if not lookup:
            lookup = (
                db.query(Location)
                .filter(
                    Location.tenant_id == current_user.tenant_id,
                    Location.site_id == payload["site_id"],
                    Location.name == payload["name"],
                    Location.deleted_at == None,
                )
                .first()
            )

        try:
            if lookup:
                for field in ["site_id", "area_id", "name", "code", "description", "notes"]:
                    setattr(lookup, field, payload[field])
                db.commit()
                updated.append(payload["name"])
            else:
                loc = Location(tenant_id=current_user.tenant_id, **payload)
                db.add(loc)
                db.commit()
                created.append(payload["name"])
        except IntegrityError as e:
            db.rollback()
            errors.append({"row": int(idx) + 2, "error": str(e)})

    return {"created": created, "updated": updated, "errors": errors}


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
