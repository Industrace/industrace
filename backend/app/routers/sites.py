import uuid
from typing import List
from datetime import datetime
import csv
from io import StringIO
import pandas as pd
from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.crud import sites as crud_sites
from app.services.audit_decorator import audit_log_action
from app.database import get_db
from app.models import User, Site
from app.schemas import Site as SiteSchema, SiteCreate, SiteUpdate
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.schemas.contact import Contact as ContactSchema
from app.crud import sites as crud_sites

router = APIRouter(
    prefix="/sites",
    tags=["sites"],
    dependencies=[Depends(require_section_access("sites"))],
)


@router.post("", response_model=SiteSchema)
@audit_log_action("create", "Site", model_class=Site)
def create_site(
    site: SiteCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_site = Site(tenant_id=current_user.tenant_id, **site.model_dump())
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site


@router.get("", response_model=List[SiteSchema])
def list_sites(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    # print(f"DEBUG: Listing active sites for tenant {current_user.tenant_id}")
    sites = (
        db.query(Site)
        .filter(Site.tenant_id == current_user.tenant_id, Site.deleted_at == None)
        .all()
    )
    # print(f"DEBUG: Found {len(sites)} active sites")
    for site in sites:
        # print(f"DEBUG: Active site: {site.id} - {site.name} - deleted_at: {site.deleted_at}")
        pass
    return sites


@router.get("/trash", response_model=List[SiteSchema])
def list_sites_trash(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    # print(f"DEBUG: Listing trash sites for tenant {current_user.tenant_id}")
    sites = (
        db.query(Site)
        .filter(Site.tenant_id == current_user.tenant_id, Site.deleted_at != None)
        .all()
    )
    # print(f"DEBUG: Found {len(sites)} sites in trash")
    for site in sites:
        # print(f"DEBUG: Trash site: {site.id} - {site.name} - deleted_at: {site.deleted_at}")
        pass
    return sites


@router.delete("/trash/empty")
@audit_log_action("empty_trash", "Site", model_class=Site)
def empty_sites_trash(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    sites = (
        db.query(Site)
        .filter(Site.tenant_id == current_user.tenant_id, Site.deleted_at != None)
        .all()
    )
    count = 0
    for site in sites:
        db.delete(site)
        count += 1
    db.commit()
    return {"detail": f"Trash emptied: {count} sites deleted"}


@router.get("/export")
def export_sites_csv(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    sites = (
        db.query(Site)
        .filter(Site.tenant_id == current_user.tenant_id, Site.deleted_at == None)
        .all()
    )
    code_map = {s.id: s.code for s in sites}

    def iter_csv():
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["name", "code", "address", "description", "parent_code"])
        for site in sites:
            parent_code = code_map.get(site.parent_id, "") if site.parent_id else ""
            writer.writerow(
                [
                    site.name or "",
                    site.code or "",
                    site.address or "",
                    site.description or "",
                    parent_code,
                ]
            )
        output.seek(0)
        yield output.read()

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sites.csv"},
    )


def _resolve_site_import_row(row, db, tenant_id):
    name = row.get("name")
    code = row.get("code")
    missing = []
    if name is None or str(name).strip() == "":
        missing.append("name")
    if code is None or str(code).strip() == "":
        missing.append("code")
    if missing:
        return None, f"Missing required fields: {', '.join(missing)}"

    parent_id = None
    parent_code = row.get("parent_code")
    if parent_code is not None and str(parent_code).strip() != "":
        parent = (
            db.query(Site)
            .filter(
                Site.tenant_id == tenant_id,
                Site.code == str(parent_code).strip(),
                Site.deleted_at == None,
            )
            .first()
        )
        if not parent:
            return None, f"Parent site not found for code: {parent_code}"
        parent_id = parent.id

    return {
        "name": str(name).strip(),
        "code": str(code).strip(),
        "address": row.get("address"),
        "description": row.get("description"),
        "parent_id": parent_id,
    }, None


@router.post("/import/xlsx/preview")
def import_sites_xlsx_preview(
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
        payload, err = _resolve_site_import_row(row, db, current_user.tenant_id)
        if err:
            errors.append({"row": int(idx) + 2, "error": err})
            continue

        site = (
            db.query(Site)
            .filter(
                Site.tenant_id == current_user.tenant_id,
                Site.code == payload["code"],
            )
            .first()
        )
        if site and site.deleted_at is None:
            diff = {}
            for field in ["name", "address", "description", "parent_id"]:
                new = payload[field]
                old = getattr(site, field)
                if str(old or "") != str(new or ""):
                    diff[field] = {"old": old, "new": new}
            if diff:
                to_update.append({"code": payload["code"], "diff": diff})
        elif not site or site.deleted_at is not None:
            to_create.append({
                "name": payload["name"],
                "code": payload["code"],
                "address": payload.get("address"),
                "description": payload.get("description"),
                "parent_code": row.get("parent_code"),
            })
    return {"to_create": to_create, "to_update": to_update, "errors": errors}


@router.post("/import/xlsx/confirm")
def import_sites_xlsx_confirm(
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
        payload, err = _resolve_site_import_row(row, db, current_user.tenant_id)
        if err:
            errors.append({"row": int(idx) + 2, "error": err})
            continue

        site = (
            db.query(Site)
            .filter(
                Site.tenant_id == current_user.tenant_id,
                Site.code == payload["code"],
            )
            .first()
        )
        try:
            if site and site.deleted_at is None:
                for field in ["name", "address", "description", "parent_id"]:
                    setattr(site, field, payload[field])
                db.commit()
                updated.append(payload["code"])
            else:
                if site and site.deleted_at is not None:
                    site.deleted_at = None
                    for field in ["name", "address", "description", "parent_id"]:
                        setattr(site, field, payload[field])
                    db.commit()
                    updated.append(payload["code"])
                else:
                    db_site = Site(tenant_id=current_user.tenant_id, **payload)
                    db.add(db_site)
                    db.commit()
                    created.append(payload["code"])
        except IntegrityError as e:
            db.rollback()
            errors.append({"row": int(idx) + 2, "error": str(e)})

    return {"created": created, "updated": updated, "errors": errors}


@router.get("/{site_id}", response_model=SiteSchema)
def get_site(
    site_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    site = (
        db.query(Site)
        .filter(
            Site.id == site_id,
            Site.tenant_id == current_user.tenant_id,
            Site.deleted_at == None,
        )
        .first()
    )
    if not site:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.SITE_NOT_FOUND)
    return site


@router.put("/{site_id}", response_model=SiteSchema)
@audit_log_action("update", "Site", model_class=Site)
def update_site(
    site_id: uuid.UUID,
    site: SiteUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_site = (
        db.query(Site)
        .filter(Site.id == site_id, Site.tenant_id == current_user.tenant_id)
        .first()
    )
    if not db_site:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.SITE_NOT_FOUND)

    site_data = site.model_dump(exclude_unset=True)  # aggiorna solo campi forniti
    for key, value in site_data.items():
        setattr(db_site, key, value)

    db.commit()
    db.refresh(db_site)
    return db_site


@router.delete("/{site_id}")
@audit_log_action("soft_delete", "Site", model_class=Site)
def soft_delete_site(
    site_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # print(f"DEBUG: Attempting to soft delete site {site_id}")
    db_site = (
        db.query(Site)
        .filter(
            Site.id == site_id,
            Site.tenant_id == current_user.tenant_id,
            Site.deleted_at == None,
        )
        .first()
    )
    if not db_site:
        # print(f"DEBUG: Site {site_id} not found or already deleted")
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.SITE_NOT_FOUND)
    
    # print(f"DEBUG: Found site {site_id}, setting deleted_at to {datetime.utcnow()}")
    db_site.deleted_at = datetime.utcnow()
    db.commit()
    # print(f"DEBUG: Site {site_id} soft deleted successfully")


@router.delete("/{site_id}/contacts/{contact_id}", status_code=204)
def delete_site_contact(
    site_id: uuid.UUID,
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    site = (
        db.query(Site)
        .filter(Site.id == site_id, Site.tenant_id == current_user.tenant_id)
        .first()
    )
    if not site:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.SITE_NOT_FOUND)
    site.contacts = [c for c in site.contacts if c.id != contact_id]
    db.commit()
    return None


@router.put("/{site_id}/contacts", response_model=List[ContactSchema])
def update_site_contacts(
    site_id: uuid.UUID,
    contact_ids: List[uuid.UUID],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    site = crud_sites.set_site_contacts(
        db, site_id, contact_ids, current_user.tenant_id
    )
    if not site:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.SITE_NOT_FOUND)
    return [ContactSchema.model_validate(c) for c in site.contacts]


@router.get("/{site_id}/contacts", response_model=List[ContactSchema])
def list_site_contacts(
    site_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    site = (
        db.query(Site)
        .filter(Site.id == site_id, Site.tenant_id == current_user.tenant_id)
        .first()
    )
    if not site:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.SITE_NOT_FOUND)
    return [ContactSchema.model_validate(c) for c in site.contacts]


@router.patch("/{site_id}/restore")
@audit_log_action("restore", "Site", model_class=Site)
def restore_site(
    site_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_site = (
        db.query(Site)
        .filter(
            Site.id == site_id,
            Site.tenant_id == current_user.tenant_id,
            Site.deleted_at != None,
        )
        .first()
    )
    if not db_site:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.SITE_NOT_FOUND)
    db_site.deleted_at = None
    db.commit()


@router.delete("/{site_id}/hard")
@audit_log_action("hard_delete", "Site", model_class=Site)
def hard_delete_site(
    site_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_site = (
        db.query(Site)
        .filter(
            Site.id == site_id,
            Site.tenant_id == current_user.tenant_id,
            Site.deleted_at != None,
        )
        .first()
    )
    if not db_site:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.SITE_NOT_FOUND)
    db.delete(db_site)
    db.commit()
