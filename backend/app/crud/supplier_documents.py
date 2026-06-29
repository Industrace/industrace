# backend/crud/supplier_documents.py
from sqlalchemy.orm import Session
from typing import Optional
from app.models import SupplierDocument
from app.schemas import SupplierDocumentCreate
import uuid


def create_supplier_document(
    db: Session, doc_in: SupplierDocumentCreate, supplier_id: uuid.UUID
) -> SupplierDocument:
    """Create a new supplier document"""
    doc = SupplierDocument(**doc_in.model_dump(), supplier_id=supplier_id)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def list_documents(
    db: Session, supplier_id: uuid.UUID, tenant_id: uuid.UUID
) -> list[SupplierDocument]:
    """List all documents for a supplier"""
    return (
        db.query(SupplierDocument)
        .filter(
            SupplierDocument.supplier_id == supplier_id,
            SupplierDocument.tenant_id == tenant_id,
        )
        .all()
    )


def get_document(
    db: Session, document_id: uuid.UUID, supplier_id: uuid.UUID, tenant_id: uuid.UUID
) -> Optional[SupplierDocument]:
    """Retrieve a document by ID"""
    return (
        db.query(SupplierDocument)
        .filter(
            SupplierDocument.id == document_id,
            SupplierDocument.supplier_id == supplier_id,
            SupplierDocument.tenant_id == tenant_id,
        )
        .first()
    )


def delete_document(db: Session, document: SupplierDocument) -> None:
    """Delete a document"""
    db.delete(document)
    db.commit()
