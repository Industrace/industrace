import uuid
from typing import List
from datetime import datetime

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
