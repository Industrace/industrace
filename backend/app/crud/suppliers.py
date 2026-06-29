# backend/crud/suppliers.py
from sqlalchemy.orm import Session
from app.models import Supplier
from app.schemas import SupplierCreate, SupplierUpdate
import uuid
from typing import Optional
from datetime import datetime, timezone
from app.models.contact import Contact
from app.utils import sanitize_text_fields


def create_supplier(
    db: Session, supplier_in: SupplierCreate, tenant_id: uuid.UUID
) -> Supplier:
    """Create a new supplier"""
    data = sanitize_text_fields(
        supplier_in.model_dump(exclude={"tenant_id"}), ["description", "notes"]
    )
    data["tenant_id"] = tenant_id
    supplier = Supplier(**data)
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def list_suppliers(db: Session, tenant_id: uuid.UUID) -> list[Supplier]:
    """List all suppliers of a tenant"""
    return db.query(Supplier).filter(Supplier.tenant_id == tenant_id).all()


def get_supplier(
    db: Session, supplier_id: uuid.UUID, tenant_id: uuid.UUID
) -> Optional[Supplier]:
    """Retrieve a supplier by ID"""
    return (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id, Supplier.tenant_id == tenant_id)
        .first()
    )


def update_supplier(
    db: Session, supplier: Supplier, update_data: SupplierUpdate
) -> Supplier:
    """Update an existing supplier"""
    update_data_dict = sanitize_text_fields(
        update_data.model_dump(exclude_unset=True), ["description", "notes"]
    )
    for key, value in update_data_dict.items():
        setattr(supplier, key, value)
    supplier.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(supplier)
    return supplier


def delete_supplier(db: Session, supplier: Supplier) -> None:
    """Delete a supplier"""
    supplier.deleted_at = datetime.utcnow()
    db.commit()


def set_supplier_contacts(db, supplier_id, contact_ids, tenant_id):
    """Set the contacts of a supplier"""
    supplier = (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id, Supplier.tenant_id == tenant_id)
        .first()
    )
    if not supplier:
        return None
    contacts = (
        db.query(Contact)
        .filter(Contact.id.in_(contact_ids), Contact.tenant_id == tenant_id)
        .all()
    )
    supplier.contacts = contacts
    db.commit()
    db.refresh(supplier)
    return supplier


def get_supplier_contacts(db, supplier_id, tenant_id):
    """Retrieve the contacts of a supplier"""
    supplier = (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id, Supplier.tenant_id == tenant_id)
        .first()
    )
    if not supplier:
        return []
    return supplier.contacts
