import uuid
from datetime import datetime
from typing import List
import csv
from fastapi import APIRouter, Depends, status, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from io import StringIO
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import User, Supplier, SupplierDocument
from app.schemas import (
    Supplier as SupplierSchema,
    SupplierCreate,
    SupplierUpdate,
    SupplierDocument as SupplierDocumentSchema,
    SupplierDocumentCreate,
)
from app.schemas.validators import (
    validate_vat_number,
    validate_tax_code,
    validate_email,
    validate_phone,
    validate_website,
)
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.crud import suppliers as crud_suppliers
from app.crud import supplier_documents as crud_documents
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.audit_decorator import audit_log_action
from app.schemas.contact import Contact as ContactSchema, ContactCreate

router = APIRouter(
    prefix="/suppliers",
    tags=["suppliers"],
    dependencies=[Depends(require_section_access("suppliers"))],
)


@router.get("/trash", response_model=List[SupplierSchema])
def list_suppliers_trash(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(Supplier)
        .filter(
            Supplier.tenant_id == current_user.tenant_id, Supplier.deleted_at != None
        )
        .all()
    )


@router.get("/export")
def export_suppliers_csv(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    suppliers = (
        db.query(Supplier)
        .filter(
            Supplier.tenant_id == current_user.tenant_id, Supplier.deleted_at == None
        )
        .all()
    )

    def iter_csv():
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "name",
                "description",
                "vat_number",
                "tax_code",
                "address",
                "city",
                "zip_code",
                "province",
                "country",
                "phone",
                "email",
                "website",
                "notes",
            ]
        )
        for s in suppliers:
            writer.writerow(
                [
                    s.name or "",
                    s.description or "",
                    s.vat_number or "",
                    s.tax_code or "",
                    s.address or "",
                    s.city or "",
                    s.zip_code or "",
                    s.province or "",
                    s.country or "",
                    s.phone or "",
                    s.email or "",
                    s.website or "",
                    s.notes or "",
                ]
            )
        output.seek(0)
        yield output.read()

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=suppliers.csv"},
    )


@router.post("/import/xlsx/preview")
def import_suppliers_xlsx_preview(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        if file.filename.endswith(".csv"):
            # Read CSV with string dtype for all columns to avoid numeric interpretation
            df = pd.read_csv(file.file, dtype=str)
            # Replace NaN values with None
            df = df.where(pd.notnull(df), None)
        else:
            df = pd.read_excel(file.file)
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}
    to_create, to_update, errors = [], [], []
    for idx, row in df.iterrows():
        name = row.get("name")
        vat_number = row.get("vat_number")
        email = row.get("email")
        missing = []
        if name is None or str(name).strip() == "":
            missing.append("name")
        if vat_number is None or str(vat_number).strip() == "":
            missing.append("vat_number")
        if missing:
            errors.append(
                {
                    "row": int(idx) + 2,
                    "error": f"Missing required fields: {', '.join(missing)}",
                }
            )
            continue
        
        # Validate fields if they are provided
        try:
            if vat_number:
                validate_vat_number(None, vat_number)
            if row.get("tax_code"):
                validate_tax_code(None, row.get("tax_code"))
            if email:
                validate_email(None, email)
            if row.get("phone"):
                validate_phone(None, row.get("phone"))
            if row.get("website"):
                validate_website(None, row.get("website"))
        except Exception as e:
            errors.append(
                {
                    "row": int(idx) + 2,
                    "error": f"Validation error: {str(e)}",
                }
            )
            continue
            
        supplier = (
            db.query(Supplier)
            .filter(
                Supplier.tenant_id == current_user.tenant_id,
                Supplier.vat_number == vat_number,
            )
            .first()
        )
        if supplier:
            diff = {}
            for field in ["name", "description", "vat_number", "tax_code", "address", "city", "zip_code", "province", "country", "phone", "email", "website", "notes"]:
                new = row.get(field)
                old = getattr(supplier, field)
                if str(old) != str(new):
                    diff[field] = {"old": old, "new": new}
            if diff:
                to_update.append({"vat_number": vat_number, "diff": diff})
        else:
            to_create.append(
                {
                    "name": name,
                    "description": row.get("description"),
                    "vat_number": vat_number,
                    "tax_code": row.get("tax_code"),
                    "address": row.get("address"),
                    "city": row.get("city"),
                    "zip_code": row.get("zip_code"),
                    "province": row.get("province"),
                    "country": row.get("country"),
                    "phone": row.get("phone"),
                    "email": email,
                    "website": row.get("website"),
                    "notes": row.get("notes"),
                }
            )
    return {"to_create": to_create, "to_update": to_update, "errors": errors}


@router.post("/import/xlsx/confirm")
def import_suppliers_xlsx_confirm(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        if file.filename.endswith(".csv"):
            # Read CSV with string dtype for all columns to avoid numeric interpretation
            df = pd.read_csv(file.file, dtype=str)
            # Replace NaN values with None
            df = df.where(pd.notnull(df), None)
        else:
            df = pd.read_excel(file.file)
    except Exception as e:
        return {"error": f"Errore nella lettura del file: {str(e)}"}
    created, updated, errors = [], [], []
    for idx, row in df.iterrows():
        name = row.get("name")
        vat_number = row.get("vat_number")
        email = row.get("email")
        missing = []
        if name is None or str(name).strip() == "":
            missing.append("name")
        if vat_number is None or str(vat_number).strip() == "":
            missing.append("vat_number")
        if missing:
            errors.append(
                {
                    "row": int(idx) + 2,
                    "error": f"Missing required fields: {', '.join(missing)}",
                }
            )
            continue
        
        # Validate fields if they are provided
        try:
            if vat_number:
                validate_vat_number(None, vat_number)
            if row.get("tax_code"):
                validate_tax_code(None, row.get("tax_code"))
            if email:
                validate_email(None, email)
            if row.get("phone"):
                validate_phone(None, row.get("phone"))
            if row.get("website"):
                validate_website(None, row.get("website"))
        except Exception as e:
            errors.append(
                {
                    "row": int(idx) + 2,
                    "error": f"Validation error: {str(e)}",
                }
            )
            continue
            
        supplier = (
            db.query(Supplier)
            .filter(
                Supplier.tenant_id == current_user.tenant_id,
                Supplier.vat_number == vat_number,
            )
            .first()
        )
        try:
            if supplier:
                supplier.name = name
                supplier.description = row.get("description")
                supplier.vat_number = vat_number
                supplier.tax_code = row.get("tax_code")
                supplier.address = row.get("address")
                supplier.city = row.get("city")
                supplier.zip_code = row.get("zip_code")
                supplier.province = row.get("province")
                supplier.country = row.get("country")
                supplier.phone = row.get("phone")
                supplier.email = email
                supplier.website = row.get("website")
                supplier.notes = row.get("notes")
                db.commit()
                updated.append(vat_number)
            else:
                new_supplier = Supplier(
                    name=name,
                    description=row.get("description"),
                    vat_number=vat_number,
                    tax_code=row.get("tax_code"),
                    address=row.get("address"),
                    city=row.get("city"),
                    zip_code=row.get("zip_code"),
                    province=row.get("province"),
                    country=row.get("country"),
                    phone=row.get("phone"),
                    email=email,
                    website=row.get("website"),
                    notes=row.get("notes"),
                    tenant_id=current_user.tenant_id,
                )
                db.add(new_supplier)
                db.commit()
                created.append(vat_number)
        except IntegrityError as e:
            db.rollback()
            errors.append(
                {"row": int(idx) + 2, "error": f"Integrity error: {str(e)}"}
            )
        except Exception as e:
            db.rollback()
            errors.append({"row": int(idx) + 2, "error": str(e)})
    return {"created": created, "updated": updated, "errors": errors}


@router.post("", response_model=SupplierSchema)
@audit_log_action("create", "Supplier", model_class=Supplier)
def create_supplier(
    supplier_in: SupplierCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud_suppliers.create_supplier(
        db, supplier_in, tenant_id=current_user.tenant_id
    )


@router.get("", response_model=List[SupplierSchema])
def list_suppliers(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(Supplier)
        .filter(
            Supplier.tenant_id == current_user.tenant_id, Supplier.deleted_at == None
        )
        .all()
    )


@router.get("/{supplier_id}", response_model=SupplierSchema)
def get_supplier(
    supplier_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == supplier_id,
            Supplier.tenant_id == current_user.tenant_id,
            Supplier.deleted_at == None,
        )
        .first()
    )
    if not supplier:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SUPPLIER_NOT_FOUND
        )
    return supplier


@router.put("/{supplier_id}", response_model=SupplierSchema)
@audit_log_action("update", "Supplier", model_class=Supplier)
def update_supplier(
    supplier_id: uuid.UUID,
    supplier_update: SupplierUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    supplier = crud_suppliers.get_supplier(db, supplier_id, current_user.tenant_id)
    if not supplier:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SUPPLIER_NOT_FOUND
        )
    return crud_suppliers.update_supplier(db, supplier, supplier_update)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
@audit_log_action("delete", "Supplier", model_class=Supplier)
def delete_supplier(
    supplier_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    supplier = crud_suppliers.get_supplier(db, supplier_id, current_user.tenant_id)
    if not supplier:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SUPPLIER_NOT_FOUND
        )
    crud_suppliers.delete_supplier(db, supplier)
    return None


@router.post("/{supplier_id}/contacts", response_model=ContactSchema)
@audit_log_action("create", "Contact", model_class=ContactSchema)
def create_supplier_contact(
    supplier_id: uuid.UUID,
    contact_in: ContactCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if contact_in.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(status_code=403, error_code=ErrorCode.TENANT_MISMATCH)

    supplier = crud_suppliers.get_supplier(db, supplier_id, current_user.tenant_id)
    if not supplier:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SUPPLIER_NOT_FOUND
        )

    # return crud_contacts.create_supplier_contact(db, contact_in, supplier_id)


@router.get("/{supplier_id}/contacts", response_model=List[ContactSchema])
def list_supplier_contacts(
    supplier_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    supplier = crud_suppliers.get_supplier(db, supplier_id, current_user.tenant_id)
    if not supplier:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SUPPLIER_NOT_FOUND
        )
    return [ContactSchema.model_validate(c) for c in supplier.contacts]


@router.put("/{supplier_id}/contacts", response_model=List[ContactSchema])
def update_supplier_contacts(
    supplier_id: uuid.UUID,
    contact_ids: List[uuid.UUID],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    supplier = crud_suppliers.set_supplier_contacts(
        db, supplier_id, contact_ids, current_user.tenant_id
    )
    if not supplier:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SUPPLIER_NOT_FOUND
        )
    return [ContactSchema.model_validate(c) for c in supplier.contacts]


@router.delete(
    "/{supplier_id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT
)
@audit_log_action("delete", "Contact", model_class=ContactSchema)
def delete_supplier_contact(
    supplier_id: uuid.UUID,
    contact_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    supplier = crud_suppliers.get_supplier(db, supplier_id, current_user.tenant_id)
    if not supplier:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SUPPLIER_NOT_FOUND
        )
    # Remove only the association
    supplier.contacts = [c for c in supplier.contacts if c.id != contact_id]
    db.commit()
    return None


@router.post("/{supplier_id}/documents", response_model=SupplierDocumentSchema)
@audit_log_action("create", "SupplierDocument", model_class=SupplierDocument)
def create_supplier_document(
    supplier_id: uuid.UUID,
    document_in: SupplierDocumentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if document_in.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(status_code=403, error_code=ErrorCode.TENANT_MISMATCH)

    supplier = crud_suppliers.get_supplier(db, supplier_id, current_user.tenant_id)
    if not supplier:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SUPPLIER_NOT_FOUND
        )

    return crud_documents.create_supplier_document(db, document_in, supplier_id)


@router.get("/{supplier_id}/documents", response_model=List[SupplierDocumentSchema])
def list_supplier_documents(
    supplier_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud_documents.list_documents(db, supplier_id, current_user.tenant_id)


@router.delete(
    "/{supplier_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT
)
@audit_log_action("delete", "SupplierDocument", model_class=SupplierDocument)
def delete_supplier_document(
    supplier_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = crud_documents.get_document(
        db, document_id, supplier_id, current_user.tenant_id
    )
    if not document:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SUPPLIER_DOCUMENT_NOT_FOUND
        )
    crud_documents.delete_document(db, document)
    return None


@router.delete("/{supplier_id}")
@audit_log_action("soft_delete", "Supplier", model_class=Supplier)
def soft_delete_supplier(
    supplier_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == supplier_id,
            Supplier.tenant_id == current_user.tenant_id,
            Supplier.deleted_at == None,
        )
        .first()
    )
    if not supplier:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SUPPLIER_NOT_FOUND
        )
    supplier.deleted_at = datetime.utcnow()
    db.commit()


@router.patch("/{supplier_id}/restore")
@audit_log_action("restore", "Supplier", model_class=Supplier)
def restore_supplier(
    supplier_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == supplier_id,
            Supplier.tenant_id == current_user.tenant_id,
            Supplier.deleted_at != None,
        )
        .first()
    )
    if not supplier:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SUPPLIER_NOT_FOUND
        )
    supplier.deleted_at = None
    db.commit()


@router.delete("/{supplier_id}/hard")
@audit_log_action("hard_delete", "Supplier", model_class=Supplier)
def hard_delete_supplier(
    supplier_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == supplier_id,
            Supplier.tenant_id == current_user.tenant_id,
            Supplier.deleted_at != None,
        )
        .first()
    )
    if not supplier:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SUPPLIER_NOT_FOUND
        )
    db.delete(supplier)
    db.commit()
