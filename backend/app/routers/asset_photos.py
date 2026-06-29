import uuid
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.audit_decorator import audit_log_action
from app.services.file_validation import validate_image_file, validate_file_size
from app.config import settings
from app.database import get_db
from app.models import User, AssetPhoto
from app.schemas import AssetPhotoCreate, AssetPhoto as AssetPhotoSchema
from app.services.auth import get_current_user
from app.services.rbac import require_section_access

router = APIRouter(
    prefix="/assets/{asset_id}/photos",
    tags=["assets"],
    dependencies=[Depends(require_section_access("asset_photos"))],
)


@router.post("", response_model=AssetPhotoSchema)
@audit_log_action("create", "AssetPhoto", model_class=AssetPhoto)
def upload_photo(
    asset_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate file size first (before processing)
    if not validate_file_size(file):
        raise ErrorCodeException(
            status_code=400, error_code=ErrorCode.FILE_TOO_LARGE
        )
    
    # Validate content_type (quick check)
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise ErrorCodeException(
            status_code=400, error_code=ErrorCode.INVALID_ASSET_PHOTO_FORMAT
        )
    
    # Validate actual file content using magic numbers and PIL
    if not validate_image_file(file):
        raise ErrorCodeException(
            status_code=400, error_code=ErrorCode.INVALID_ASSET_PHOTO_FORMAT
        )

    filename = f"{uuid.uuid4()}_{file.filename}"
    relative_path = Path("tenants") / str(current_user.tenant_id) / "photos" / filename
    file_location = Path("uploads") / relative_path

    file_location.parent.mkdir(parents=True, exist_ok=True)

    with file_location.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    photo_data = AssetPhotoCreate(
        asset_id=asset_id,
        tenant_id=current_user.tenant_id,
        file_path=str(relative_path),
    )
    photo = AssetPhoto(**photo_data.model_dump())

    db.add(photo)
    db.commit()
    db.refresh(photo)

    return photo


@router.delete("/{photo_id}")
@audit_log_action("delete", "AssetPhoto", model_class=AssetPhoto)
def delete_photo(
    asset_id: uuid.UUID,
    photo_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    photo = (
        db.query(AssetPhoto)
        .filter_by(id=photo_id, asset_id=asset_id, tenant_id=current_user.tenant_id)
        .first()
    )
    if not photo:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_PHOTO_NOT_FOUND
        )

    file_path = Path("uploads") / photo.file_path
    if file_path.exists():
        file_path.unlink()

    db.delete(photo)
    db.commit()
    return {"detail": "Photo deleted"}


@router.get("/{photo_id}")
def get_photo(
    asset_id: uuid.UUID,
    photo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    photo = db.query(AssetPhoto).filter_by(id=photo_id, asset_id=asset_id).first()
    if not photo:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_PHOTO_NOT_FOUND
        )
    if photo.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(
            status_code=403, error_code=ErrorCode.UNAUTHORIZED_ASSET_ACCESS
        )

    full_path = Path("uploads") / photo.file_path
    if not full_path.exists():
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_PHOTO_NOT_FOUND
        )

    return FileResponse(path=full_path)
