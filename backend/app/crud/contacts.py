from sqlalchemy.orm import Session, joinedload
from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactUpdate
import uuid
from typing import List, Optional
from app.utils import sanitize_text_fields


def create_contact(
    db: Session, contact_in: ContactCreate, tenant_id: uuid.UUID
) -> Contact:
    """Create a new contact"""
    data = sanitize_text_fields(contact_in.model_dump(), ["notes"])
    contact = Contact(**data, tenant_id=tenant_id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def get_contact(
    db: Session, contact_id: uuid.UUID, tenant_id: uuid.UUID
) -> Optional[Contact]:
    """Retrieve a contact by ID"""
    return (
        db.query(Contact)
        .options(
            joinedload(Contact.assets),
            joinedload(Contact.sites),
            joinedload(Contact.locations),
            joinedload(Contact.suppliers),
        )
        .filter(Contact.id == contact_id, Contact.tenant_id == tenant_id)
        .first()
    )


def list_contacts(
    db: Session, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[Contact]:
    """List all contacts of a tenant with pagination"""
    return (
        db.query(Contact)
        .filter(Contact.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_contact(
    db: Session,
    contact_id: uuid.UUID,
    contact_update: ContactUpdate,
    tenant_id: uuid.UUID,
) -> Optional[Contact]:
    """Update an existing contact"""
    contact = get_contact(db, contact_id, tenant_id)
    if contact:
        update_data = sanitize_text_fields(
            contact_update.model_dump(exclude_unset=True), ["notes"]
        )
        for key, value in update_data.items():
            setattr(contact, key, value)
        db.commit()
        db.refresh(contact)
    return contact


def delete_contact(db: Session, contact_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
    """Delete a contact"""
    contact = get_contact(db, contact_id, tenant_id)
    if contact:
        db.delete(contact)
        db.commit()
        return True
    return False
