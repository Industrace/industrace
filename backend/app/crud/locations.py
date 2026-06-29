# backend/crud/locations.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
import uuid
from app.models import Location
from app.schemas import LocationCreate
from app.utils import sanitize_text_fields


def get_location(db: Session, location_id: uuid.UUID) -> Optional[Location]:
    """Retrieve a location by ID"""
    return db.query(Location).filter(Location.id == location_id).first()


def get_locations(db: Session, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """List all locations of a tenant with pagination"""
    return (
        db.query(Location)
        .filter(Location.tenant_id == tenant_id)
        .options(joinedload(Location.floorplan), joinedload(Location.site), joinedload(Location.area))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_location_by_code(
    db: Session, tenant_id: uuid.UUID, code: str
) -> Optional[Location]:
    """Retrieve a location by code"""
    return (
        db.query(Location)
        .filter(and_(Location.tenant_id == tenant_id, Location.code == code))
        .first()
    )


def create_location(
    db: Session, location: LocationCreate, tenant_id: uuid.UUID
) -> Location:
    """Create a new location"""
    data = sanitize_text_fields(location.model_dump(), ["description", "notes"])
    data["tenant_id"] = tenant_id
    db_location = Location(**data)
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


def update_location(
    db: Session,
    location_id: uuid.UUID,
    location_update: LocationCreate,
    tenant_id: uuid.UUID,
) -> Optional[Location]:
    """Update an existing location"""
    db_location = (
        db.query(Location)
        .filter(and_(Location.id == location_id, Location.tenant_id == tenant_id))
        .first()
    )
    if db_location:
        update_data = sanitize_text_fields(
            location_update.model_dump(exclude_unset=True), ["description", "notes"]
        )
        for key, value in update_data.items():
            setattr(db_location, key, value)
        db.commit()
        db.refresh(db_location)
    return db_location


def delete_location(db: Session, location_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
    """Delete a location"""
    db_location = (
        db.query(Location)
        .filter(and_(Location.id == location_id, Location.tenant_id == tenant_id))
        .first()
    )
    if db_location:
        db.delete(db_location)
        db.commit()
        return True
    return False


def set_location_contacts(
    db: Session, location_id: uuid.UUID, contact_ids: list, tenant_id: uuid.UUID
):
    """Set the contacts of a location"""
    location = (
        db.query(Location)
        .filter(Location.id == location_id, Location.tenant_id == tenant_id)
        .first()
    )
    if not location:
        return None
    from app.models.contact import Contact

    contacts = (
        db.query(Contact)
        .filter(Contact.id.in_(contact_ids), Contact.tenant_id == tenant_id)
        .all()
    )
    location.contacts = contacts
    db.commit()
    db.refresh(location)
    return location
