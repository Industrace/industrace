from fastapi import APIRouter, Depends
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from sqlalchemy.orm import Session
from app.schemas.asset_interface import (
    AssetInterface,
    AssetInterfaceCreate,
    AssetInterfaceUpdate,
)
from app.crud.asset_interface import (
    create_interface,
    get_interface,
    update_interface,
    delete_interface,
    create_interfaces_bulk,
)
from app.database import get_db
from uuid import UUID
from typing import List
from app.schemas.audit_log import AuditLog as AuditLogSchema
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.services.audit_decorator import audit_log_action
from app.models import User, Asset
from app.models.asset_interface import AssetInterface as AssetInterfaceModel

router = APIRouter(
    prefix="/asset-interfaces",
    tags=["Asset Interfaces"],
    dependencies=[Depends(require_section_access("assets"))],
)


@router.post("/", response_model=AssetInterface)
@audit_log_action("create", "AssetInterface", model_class=AssetInterface)
def create_asset_interface(
    interface_in: AssetInterfaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset = (
        db.query(Asset)
        .filter(Asset.id == interface_in.asset_id, Asset.tenant_id == current_user.tenant_id)
        .first()
    )
    if not asset:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.UNAUTHORIZED_ASSET_ACCESS
        )

    # Always enforce tenant_id from authenticated user
    data = interface_in.model_dump()
    data["tenant_id"] = current_user.tenant_id
    return create_interface(db, AssetInterfaceCreate(**data))


@router.post("/bulk", response_model=List[AssetInterface])
@audit_log_action("create", "AssetInterface", model_class=AssetInterface)
def create_asset_interfaces_bulk(
    interfaces_in: List[AssetInterfaceCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset_ids = {interface.asset_id for interface in interfaces_in}
    tenant_assets = (
        db.query(Asset.id)
        .filter(Asset.id.in_(asset_ids), Asset.tenant_id == current_user.tenant_id)
        .all()
    )
    tenant_asset_ids = {asset_id for (asset_id,) in tenant_assets}
    if tenant_asset_ids != asset_ids:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.UNAUTHORIZED_ASSET_ACCESS
        )

    # Always enforce tenant_id from authenticated user
    interfaces = []
    for interface in interfaces_in:
        data = interface.model_dump()
        data["tenant_id"] = current_user.tenant_id
        interfaces.append(AssetInterfaceCreate(**data))
    return create_interfaces_bulk(db, interfaces)


@router.get("/{interface_id}", response_model=AssetInterface)
def read_asset_interface(
    interface_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interface = get_interface(db, interface_id)
    if not interface:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_INTERFACE_NOT_FOUND
        )
    if interface.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(
            status_code=403, error_code=ErrorCode.UNAUTHORIZED_ASSET_ACCESS
        )
    return interface


@router.get("/by-asset/{asset_id}", response_model=List[AssetInterface])
def read_interfaces_by_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(AssetInterfaceModel).filter_by(
        asset_id=asset_id, tenant_id=current_user.tenant_id
    ).all()


@router.put("/{interface_id}", response_model=AssetInterface)
@audit_log_action("update", "AssetInterface", model_class=AssetInterface)
def update_asset_interface(
    interface_id: UUID,
    interface_in: AssetInterfaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_interface = get_interface(db, interface_id)
    if not existing_interface:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_INTERFACE_NOT_FOUND
        )
    if existing_interface.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(
            status_code=403, error_code=ErrorCode.UNAUTHORIZED_ASSET_ACCESS
        )

    interface = update_interface(db, interface_id, interface_in)
    if not interface:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_INTERFACE_NOT_FOUND
        )
    return interface


@router.delete("/{interface_id}", response_model=AssetInterface)
@audit_log_action("delete", "AssetInterface", model_class=AssetInterface)
def delete_asset_interface(
    interface_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_interface = get_interface(db, interface_id)
    if not existing_interface:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_INTERFACE_NOT_FOUND
        )
    if existing_interface.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(
            status_code=403, error_code=ErrorCode.UNAUTHORIZED_ASSET_ACCESS
        )

    interface = delete_interface(db, interface_id)
    if not interface:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_INTERFACE_NOT_FOUND
        )
    return interface
