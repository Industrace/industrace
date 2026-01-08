import uuid
from datetime import datetime
from typing import List
import csv
from fastapi import UploadFile, File, Body
from fastapi.responses import StreamingResponse
from io import StringIO
import pandas as pd
from sqlalchemy.exc import IntegrityError

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Manufacturer
from app.schemas import (
    Manufacturer as ManufacturerSchema,
    ManufacturerCreate,
    ManufacturerUpdate,
)
from app.services.auth import get_current_user
from app.crud import manufacturers as crud_manufacturers
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.audit_decorator import audit_log_action

router = APIRouter(
    prefix="/manufacturers",
    tags=["manufacturers"],
)


@router.get("/export")
def export_manufacturers_csv(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    manufacturers = (
        db.query(Manufacturer)
        .filter(Manufacturer.tenant_id == current_user.tenant_id)
        .all()
    )

    def iter_csv():
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["name", "description", "website", "email", "phone"])
        for m in manufacturers:
            writer.writerow(
                [
                    m.name or "",
                    m.description or "",
                    m.website or "",
                    m.email or "",
                    m.phone or "",
                ]
            )
        output.seek(0)
        yield output.read()

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=manufacturers.csv"},
    )


@router.post("/import/xlsx/preview")
def import_manufacturers_xlsx_preview(
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
    to_create, to_update, errors = [], [], []
    for idx, row in df.iterrows():
        name = row.get("name")
        missing = []
        if name is None or str(name).strip() == "":
            missing.append("name")
        if missing:
            errors.append(
                {
                    "row": int(idx) + 2,
                    "error": f"Campi obbligatori mancanti: {', '.join(missing)}",
                }
            )
            continue
        manufacturer = (
            db.query(Manufacturer)
            .filter(
                Manufacturer.tenant_id == current_user.tenant_id,
                Manufacturer.name == name,
            )
            .first()
        )
        if manufacturer:
            diff = {}
            for field in ["description", "website", "email", "phone"]:
                new = row.get(field)
                old = getattr(manufacturer, field)
                if str(old) != str(new):
                    diff[field] = {"old": old, "new": new}
            if diff:
                to_update.append({"name": name, "diff": diff})
        else:
            to_create.append(
                {
                    "name": name,
                    "description": row.get("description"),
                    "website": row.get("website"),
                    "email": row.get("email"),
                    "phone": row.get("phone"),
                }
            )
    return {"to_create": to_create, "to_update": to_update, "errors": errors}


@router.post("/import/xlsx/confirm")
def import_manufacturers_xlsx_confirm(
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
        missing = []
        if name is None or str(name).strip() == "":
            missing.append("name")
        if missing:
            errors.append(
                {
                    "row": int(idx) + 2,
                    "error": f"Campi obbligatori mancanti: {', '.join(missing)}",
                }
            )
            continue
        manufacturer = (
            db.query(Manufacturer)
            .filter(
                Manufacturer.tenant_id == current_user.tenant_id,
                Manufacturer.name == name,
            )
            .first()
        )
        try:
            if manufacturer:
                manufacturer.description = row.get("description")
                manufacturer.website = row.get("website")
                manufacturer.email = row.get("email")
                manufacturer.phone = row.get("phone")
                db.commit()
                updated.append(name)
            else:
                new_manufacturer = Manufacturer(
                    name=name,
                    description=row.get("description"),
                    website=row.get("website"),
                    email=row.get("email"),
                    phone=row.get("phone"),
                    tenant_id=current_user.tenant_id,
                )
                db.add(new_manufacturer)
                db.commit()
                created.append(name)
        except IntegrityError as e:
            db.rollback()
            errors.append(
                {"row": int(idx) + 2, "error": f"Errore di integrità: {str(e)}"}
            )
        except Exception as e:
            db.rollback()
            errors.append({"row": int(idx) + 2, "error": str(e)})
    return {"created": created, "updated": updated, "errors": errors}


@router.post("/bulk-update")
def bulk_update_manufacturers(
    ids: List[uuid.UUID] = Body(...),
    fields: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = []
    errors = []
    for manufacturer_id in ids:
        manufacturer = (
            db.query(Manufacturer)
            .filter(
                Manufacturer.id == manufacturer_id,
                Manufacturer.tenant_id == current_user.tenant_id,
            )
            .first()
        )
        if not manufacturer:
            errors.append(
                {"id": str(manufacturer_id), "error": "Manufacturer not found"}
            )
            continue
        for key, value in fields.items():
            if hasattr(manufacturer, key):
                setattr(manufacturer, key, value)
        try:
            db.commit()
            updated.append(str(manufacturer_id))
        except Exception as e:
            db.rollback()
            errors.append({"id": str(manufacturer_id), "error": str(e)})
    return {"updated": updated, "errors": errors}


@router.post("", response_model=ManufacturerSchema)
@audit_log_action("create", "Manufacturer", model_class=Manufacturer)
def create_manufacturer(
    manufacturer_in: ManufacturerCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud_manufacturers.create_manufacturer(
        db, manufacturer_in, tenant_id=current_user.tenant_id
    )


@router.get("", response_model=List[ManufacturerSchema])
def list_manufacturers(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return crud_manufacturers.list_manufacturers(db, current_user.tenant_id)


@router.get("/trash", response_model=List[ManufacturerSchema])
def list_manufacturers_trash(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(Manufacturer)
        .filter(
            Manufacturer.tenant_id == current_user.tenant_id,
            Manufacturer.deleted_at != None
        )
        .all()
    )


@router.get("/{manufacturer_id}", response_model=ManufacturerSchema)
def get_manufacturer(
    manufacturer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    manufacturer = crud_manufacturers.get_manufacturer(
        db, manufacturer_id, current_user.tenant_id
    )
    if not manufacturer:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.MANUFACTURER_NOT_FOUND
        )
    return manufacturer


@router.put("/{manufacturer_id}", response_model=ManufacturerSchema)
@audit_log_action("update", "Manufacturer", model_class=Manufacturer)
def update_manufacturer(
    manufacturer_id: uuid.UUID,
    manufacturer_update: ManufacturerUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    manufacturer = crud_manufacturers.get_manufacturer(
        db, manufacturer_id, current_user.tenant_id
    )
    if not manufacturer:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.MANUFACTURER_NOT_FOUND
        )
    return crud_manufacturers.update_manufacturer(db, manufacturer, manufacturer_update)


@router.delete("/{manufacturer_id}", status_code=status.HTTP_204_NO_CONTENT)
@audit_log_action("delete", "Manufacturer", model_class=Manufacturer)
def delete_manufacturer(
    manufacturer_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    manufacturer = crud_manufacturers.get_manufacturer(
        db, manufacturer_id, current_user.tenant_id
    )
    if not manufacturer:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.MANUFACTURER_NOT_FOUND
        )
    crud_manufacturers.delete_manufacturer(db, manufacturer)
    return None


@router.patch("/{manufacturer_id}/restore", response_model=ManufacturerSchema)
@audit_log_action("restore", "Manufacturer", model_class=Manufacturer)
def restore_manufacturer(
    manufacturer_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    manufacturer = crud_manufacturers.get_manufacturer(
        db, manufacturer_id, current_user.tenant_id, include_deleted=True
    )
    if not manufacturer:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.MANUFACTURER_NOT_FOUND
        )
    if manufacturer.deleted_at is None:
        raise ErrorCodeException(
            status_code=400, error_code=ErrorCode.MANUFACTURER_NOT_IN_TRASH
        )
    return crud_manufacturers.restore_manufacturer(db, manufacturer)


@router.delete("/{manufacturer_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
@audit_log_action("hard_delete", "Manufacturer", model_class=Manufacturer)
def hard_delete_manufacturer(
    manufacturer_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    manufacturer = crud_manufacturers.get_manufacturer(
        db, manufacturer_id, current_user.tenant_id, include_deleted=True
    )
    if not manufacturer:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.MANUFACTURER_NOT_FOUND
        )
    crud_manufacturers.hard_delete_manufacturer(db, manufacturer)
    return None
