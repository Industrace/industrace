import uuid
from typing import List
from fastapi import APIRouter, Depends, Request, UploadFile, File, Body
from fastapi.responses import StreamingResponse
from io import StringIO
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import User, Contact
from app.schemas.contact import Contact as ContactSchema, ContactCreate, ContactUpdate
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.crud import contacts as crud_contacts
from app.services.audit_decorator import audit_log_action
from datetime import datetime
import csv

router = APIRouter(
    prefix="/contacts",
    tags=["contacts"],
    dependencies=[Depends(require_section_access("contacts"))],
)


@router.get("/trash", response_model=List[ContactSchema])
def list_contacts_trash(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(Contact)
        .filter(Contact.tenant_id == current_user.tenant_id, Contact.deleted_at != None)
        .all()
    )


@router.get("/export")
@audit_log_action("export", "Contact", model_class=Contact)
def export_contacts_csv(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    contacts = (
        db.query(Contact)
        .filter(Contact.tenant_id == current_user.tenant_id, Contact.deleted_at == None)
        .all()
    )

    def iter_csv():
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["first_name", "last_name", "email", "phone1", "phone2", "type", "notes"]
        )
        for c in contacts:
            writer.writerow(
                [
                    c.first_name or "",
                    c.last_name or "",
                    c.email or "",
                    c.phone1 or "",
                    c.phone2 or "",
                    c.type or "",
                    c.notes or "",
                ]
            )
        output.seek(0)
        yield output.read()

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts.csv"},
    )


@router.post("/import/xlsx/preview")
@audit_log_action("import", "Contact", model_class=Contact)
def import_contacts_xlsx_preview(
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
        first_name = row.get("first_name")
        last_name = row.get("last_name")
        email = row.get("email")
        missing = []
        if first_name is None or str(first_name).strip() == "":
            missing.append("first_name")
        if last_name is None or str(last_name).strip() == "":
            missing.append("last_name")
        if missing:
            errors.append(
                {
                    "row": int(idx) + 2,
                    "error": f"Missing required fields: {', '.join(missing)}",
                }
            )
            continue
        contact = (
            db.query(Contact)
            .filter(
                Contact.tenant_id == current_user.tenant_id,
                Contact.first_name == first_name,
                Contact.last_name == last_name,
            )
            .first()
        )
        if contact:
            diff = {}
            for field in ["phone1", "phone2", "type", "notes"]:
                new = row.get(field)
                old = getattr(contact, field)
                if str(old) != str(new):
                    diff[field] = {"old": old, "new": new}
            if diff:
                to_update.append(
                    {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "diff": diff,
                    }
                )
        else:
            to_create.append(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone1": row.get("phone1"),
                    "phone2": row.get("phone2"),
                    "type": row.get("type"),
                    "notes": row.get("notes"),
                }
            )
    return {"to_create": to_create, "to_update": to_update, "errors": errors}


@router.post("/import/xlsx/confirm")
@audit_log_action("import", "Contact", model_class=Contact)
def import_contacts_xlsx_confirm(
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
    created, updated, errors = [], [], []
    for idx, row in df.iterrows():
        first_name = row.get("first_name")
        last_name = row.get("last_name")
        email = row.get("email")
        missing = []
        if first_name is None or str(first_name).strip() == "":
            missing.append("first_name")
        if last_name is None or str(last_name).strip() == "":
            missing.append("last_name")
        if missing:
            errors.append(
                {
                    "row": int(idx) + 2,
                    "error": f"Missing required fields: {', '.join(missing)}",
                }
            )
            continue
        contact = (
            db.query(Contact)
            .filter(
                Contact.tenant_id == current_user.tenant_id,
                Contact.first_name == first_name,
                Contact.last_name == last_name,
            )
            .first()
        )
        try:
            if contact:
                contact.phone1 = row.get("phone1")
                contact.phone2 = row.get("phone2")
                contact.type = row.get("type")
                contact.notes = row.get("notes")
                db.commit()
                email_display = f" <{email}>" if email else ""
                updated.append(f"{first_name} {last_name}{email_display}")
            else:
                new_contact = Contact(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone1=row.get("phone1"),
                    phone2=row.get("phone2"),
                    type=row.get("type"),
                    notes=row.get("notes"),
                    tenant_id=current_user.tenant_id,
                )
                db.add(new_contact)
                db.commit()
                email_display = f" <{email}>" if email else ""
                created.append(f"{first_name} {last_name}{email_display}")
        except IntegrityError as e:
            db.rollback()
            errors.append(
                {"row": int(idx) + 2, "error": f"Integrity error: {str(e)}"}
            )
        except Exception as e:
            db.rollback()
            errors.append({"row": int(idx) + 2, "error": str(e)})
    return {"created": created, "updated": updated, "errors": errors}


@router.post("", response_model=ContactSchema)
@audit_log_action("create", "Contact", model_class=Contact)
def create_contact(
    contact: ContactCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud_contacts.create_contact(db, contact, current_user.tenant_id)


@router.get("", response_model=List[ContactSchema])
def list_contacts(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Contact)
        .filter(Contact.tenant_id == current_user.tenant_id, Contact.deleted_at == None)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{contact_id}", response_model=ContactSchema)
def get_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = (
        db.query(Contact)
        .filter(
            Contact.id == contact_id,
            Contact.tenant_id == current_user.tenant_id,
            Contact.deleted_at == None,
        )
        .first()
    )
    if not contact:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.CONTACT_NOT_FOUND
        )
    return contact


@router.put("/{contact_id}", response_model=ContactSchema)
@audit_log_action("update", "Contact", model_class=Contact)
def update_contact(
    contact_id: uuid.UUID,
    contact: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = crud_contacts.update_contact(
        db, contact_id, contact, current_user.tenant_id
    )
    if not updated:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.CONTACT_NOT_FOUND
        )
    return updated


@router.delete("/{contact_id}")
@audit_log_action("soft_delete", "Contact", model_class=Contact)
def soft_delete_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = (
        db.query(Contact)
        .filter(
            Contact.id == contact_id,
            Contact.tenant_id == current_user.tenant_id,
            Contact.deleted_at == None,
        )
        .first()
    )
    if not contact:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.CONTACT_NOT_FOUND
        )
    contact.deleted_at = datetime.utcnow()
    db.commit()


@router.patch("/{contact_id}/restore")
@audit_log_action("restore", "Contact", model_class=Contact)
def restore_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = (
        db.query(Contact)
        .filter(
            Contact.id == contact_id,
            Contact.tenant_id == current_user.tenant_id,
            Contact.deleted_at != None,
        )
        .first()
    )
    if not contact:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.CONTACT_NOT_FOUND
        )
    contact.deleted_at = None
    db.commit()


@router.delete("/{contact_id}/hard")
@audit_log_action("hard_delete", "Contact", model_class=Contact)
def hard_delete_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = (
        db.query(Contact)
        .filter(
            Contact.id == contact_id,
            Contact.tenant_id == current_user.tenant_id,
            Contact.deleted_at != None,
        )
        .first()
    )
    if not contact:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.CONTACT_NOT_FOUND
        )
    db.delete(contact)
    db.commit()


@router.post("/bulk-update")
@audit_log_action("bulk_update", "Contact", model_class=Contact)
def bulk_update_contacts(
    ids: List[uuid.UUID] = Body(...),
    fields: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = []
    errors = []
    for contact_id in ids:
        contact = (
            db.query(Contact)
            .filter(
                Contact.id == contact_id,
                Contact.tenant_id == current_user.tenant_id,
                Contact.deleted_at == None,
            )
            .first()
        )
        if not contact:
            errors.append({"id": str(contact_id), "error": "Contact not found"})
            continue
        for key, value in fields.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        try:
            db.commit()
            updated.append(str(contact_id))
        except Exception as e:
            db.rollback()
            errors.append({"id": str(contact_id), "error": str(e)})
    return {"updated": updated, "errors": errors}
