# backend/crud/sites.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
import uuid
from app.models import Site
from app.schemas import SiteCreate, SiteUpdate
from app.utils import sanitize_text_fields


def get_site(db: Session, site_id: uuid.UUID) -> Optional[Site]:
    """Retrieve a site by ID"""
    return db.query(Site).filter(Site.id == site_id).first()


def get_site_by_tenant(
    db: Session, site_id: uuid.UUID, tenant_id: uuid.UUID
) -> Optional[Site]:
    """Retrieve a site by ID and tenant"""
    return (
        db.query(Site)
        .filter(
            Site.id == site_id, Site.tenant_id == tenant_id, Site.deleted_at == None
        )
        .first()
    )


def get_sites(
    db: Session, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[Site]:
    """List all sites of a tenant with pagination"""
    return (
        db.query(Site)
        .filter(Site.tenant_id == tenant_id, Site.deleted_at == None)
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_sites(
    db: Session, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[Site]:
    """Alias for get_sites for consistency with other CRUD modules"""
    return get_sites(db, tenant_id, skip, limit)


def get_site_by_code(db: Session, tenant_id: uuid.UUID, code: str) -> Optional[Site]:
    """Retrieve a site by code and tenant"""
    return (
        db.query(Site)
        .filter(and_(Site.tenant_id == tenant_id, Site.code == code))
        .first()
    )


def create_site(db: Session, site: SiteCreate, tenant_id: uuid.UUID) -> Site:
    """Create a new site"""
    data = sanitize_text_fields(site.model_dump(), ["description", "address"])
    data["tenant_id"] = tenant_id
    db_site = Site(**data)
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site


def update_site(
    db: Session, site_id: uuid.UUID, site_update: SiteUpdate
) -> Optional[Site]:
    """Update an existing site"""
    db_site = db.query(Site).filter(Site.id == site_id).first()
    if db_site:
        update_data = sanitize_text_fields(
            site_update.model_dump(exclude_unset=True), ["description", "address"]
        )
        for key, value in update_data.items():
            setattr(db_site, key, value)
        db.commit()
        db.refresh(db_site)
    return db_site


def delete_site(db: Session, site_id: uuid.UUID) -> bool:
    """Delete a site"""
    db_site = db.query(Site).filter(Site.id == site_id).first()
    if db_site:
        db.delete(db_site)
        db.commit()
        return True
    return False


def set_site_contacts(
    db: Session, site_id: uuid.UUID, contact_ids: list, tenant_id: uuid.UUID
):
    """Set the contacts of a site"""
    site = (
        db.query(Site).filter(Site.id == site_id, Site.tenant_id == tenant_id).first()
    )
    if not site:
        return None
    from app.models.contact import Contact

    contacts = (
        db.query(Contact)
        .filter(Contact.id.in_(contact_ids), Contact.tenant_id == tenant_id)
        .all()
    )
    site.contacts = contacts
    db.commit()
    db.refresh(site)
    return site 
