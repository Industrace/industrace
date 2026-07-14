import uuid
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os

from app.database import get_db
from app.models import User, AssetDocument, Asset
from app.schemas import AssetDocumentCreate, AssetDocument as AssetDocumentSchema
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.services.file_validation import validate_document_file, validate_file_size
from app.config import settings
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.audit_decorator import audit_log_action

router = APIRouter(
    prefix="/assets/{asset_id}/documents",
    tags=["assets"],
    dependencies=[Depends(require_section_access("asset_documents"))],
)


@router.post("", response_model=AssetDocumentSchema)
@audit_log_action("create", "AssetDocument", model_class=AssetDocument)
def upload_document(
    asset_id: uuid.UUID,
    request: Request,
    description: str = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.UNAUTHORIZED_ASSET_ACCESS
        )

    # Validate file size first (before processing)
    if not validate_file_size(file):
        raise ErrorCodeException(
            status_code=400, error_code=ErrorCode.FILE_TOO_LARGE
        )
    
    # Validate content_type (quick check)
    allowed_mime_types = [
        "application/pdf",
        "application/msword",  # .doc
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "text/plain",  # .txt
        "text/csv",  # .csv
        "application/vnd.ms-excel",  # .xls
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    ]
    
    if file.content_type not in allowed_mime_types:
        raise ErrorCodeException(
            status_code=400, 
            error_code=ErrorCode.INVALID_ASSET_DOCUMENT_FORMAT
        )
    
    # Validate actual file content using magic numbers
    if not validate_document_file(file):
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_ASSET_DOCUMENT_FORMAT
        )

    unique_filename = f"{uuid.uuid4()}{Path(file.filename).suffix}"
    relative_path = (
        Path("tenants") / str(current_user.tenant_id) / "documents" / unique_filename
    )
    file_location = Path("uploads") / relative_path

    file_location.parent.mkdir(parents=True, exist_ok=True)

    with file_location.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = AssetDocument(
        asset_id=asset_id,
        tenant_id=current_user.tenant_id,
        file_path=str(relative_path),
        name=file.filename,
        description=description,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return document


@router.delete("/{document_id}")
@audit_log_action("delete", "AssetDocument", model_class=AssetDocument)
def delete_document(
    asset_id: uuid.UUID,
    document_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = (
        db.query(AssetDocument)
        .filter_by(id=document_id, asset_id=asset_id, tenant_id=current_user.tenant_id)
        .first()
    )
    if not document:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_DOCUMENT_NOT_FOUND
        )

    file_path = Path("uploads") / document.file_path
    if file_path.exists():
        file_path.unlink()

    db.delete(document)
    db.commit()
    return {"detail": "document deleted"}


@router.get("/{document_id}")
def get_document(
    asset_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = (
        db.query(AssetDocument).filter_by(id=document_id, asset_id=asset_id).first()
    )
    if not document:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_DOCUMENT_NOT_FOUND
        )
    if document.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(
            status_code=403, error_code=ErrorCode.UNAUTHORIZED_ASSET_ACCESS
        )

    full_path = Path("uploads") / document.file_path
    if not full_path.exists():
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_DOCUMENT_NOT_FOUND
        )

    return FileResponse(
        path=full_path,
        filename=document.name,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{document.name}"'},
    )
