import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.audit_decorator import audit_log_action
from app.database import get_db
from app.models import User, AssetType
from app.schemas import AssetType as AssetTypeSchema, AssetTypeCreate, AssetTypeUpdate
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.crud import asset_types as crud_asset_types


router = APIRouter(
    prefix="/asset-types",
    tags=["asset_types"],
    dependencies=[Depends(require_section_access("asset_types"))],
)


@router.post("", response_model=AssetTypeSchema)
@audit_log_action("create", "AssetType", model_class=AssetType)
def create_asset_type(
    asset_type_in: AssetTypeCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud_asset_types.create_asset_type(
        db, asset_type_in, tenant_id=current_user.tenant_id
    )


@router.get("", response_model=List[AssetTypeSchema])
def list_asset_types(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return crud_asset_types.get_asset_types(db, current_user.tenant_id)


@router.get("/{asset_type_id}", response_model=AssetTypeSchema)
def get_asset_type(
    asset_type_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset_type = crud_asset_types.get_asset_type(db, asset_type_id)
    if not asset_type:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_TYPE_NOT_FOUND
        )
    return asset_type


@router.put("/{asset_type_id}", response_model=AssetTypeSchema)
@audit_log_action("update", "AssetType", model_class=AssetType)
def update_asset_type(
    asset_type_id: uuid.UUID,
    asset_type_update: AssetTypeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset_type = crud_asset_types.get_asset_type(db, asset_type_id)
    if not asset_type:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_TYPE_NOT_FOUND
        )
    return crud_asset_types.update_asset_type(db, asset_type_id, asset_type_update)


@router.delete("/{asset_type_id}", status_code=status.HTTP_204_NO_CONTENT)
@audit_log_action("delete", "AssetType", model_class=AssetType)
def delete_asset_type(
    asset_type_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset_type = crud_asset_types.get_asset_type(db, asset_type_id)
    if not asset_type:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_TYPE_NOT_FOUND
        )
    crud_asset_types.delete_asset_type(db, asset_type_id)
    return None
