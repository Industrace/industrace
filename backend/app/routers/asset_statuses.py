import uuid
from typing import List
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, AssetStatus
from app.schemas.asset_status import (
    AssetStatus as AssetStatusSchema,
    AssetStatusCreate,
    AssetStatusUpdate,
)
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.crud import asset_statuses as crud_asset_statuses
from app.services.audit_decorator import audit_log_action
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode

router = APIRouter(
    prefix="/asset-statuses",
    tags=["asset_statuses"],
    dependencies=[Depends(require_section_access("asset_statuses"))],
)


@router.post("", response_model=AssetStatusSchema)
@audit_log_action("create", "AssetStatus", model_class=AssetStatus)
def create_status(
    status_in: AssetStatusCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud_asset_statuses.create_asset_status(
        db, status_in, current_user.tenant_id
    )


@router.get("", response_model=List[AssetStatusSchema])
def list_statuses(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud_asset_statuses.list_asset_statuses(
        db, current_user.tenant_id, skip=skip, limit=limit
    )


@router.get("/{status_id}", response_model=AssetStatusSchema)
def get_status(
    status_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    status = crud_asset_statuses.get_asset_status(db, status_id, current_user.tenant_id)
    if not status:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_STATUS_NOT_FOUND
        )
    return status


@router.put("/{status_id}", response_model=AssetStatusSchema)
@audit_log_action("update", "AssetStatus", model_class=AssetStatus)
def update_status(
    status_id: uuid.UUID,
    status_update: AssetStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    status = crud_asset_statuses.get_asset_status(db, status_id, current_user.tenant_id)
    if not status:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_STATUS_NOT_FOUND
        )
    return crud_asset_statuses.update_asset_status(db, status, status_update)


@router.delete("/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
@audit_log_action("delete", "AssetStatus", model_class=AssetStatus)
def delete_status(
    status_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    status = crud_asset_statuses.get_asset_status(db, status_id, current_user.tenant_id)
    if not status:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_STATUS_NOT_FOUND
        )
    crud_asset_statuses.delete_asset_status(db, status)
    return None
