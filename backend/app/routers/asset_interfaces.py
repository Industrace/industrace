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
    get_interfaces_by_asset,
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
from app.services.audit_log import get_entity_name_by_id
from app.services.audit_decorator import audit_log_action
from app.models import User

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
    # Set tenant_id if missing
    data = interface_in.model_dump()
    if not data.get("tenant_id"):
        data["tenant_id"] = current_user.tenant_id
    return create_interface(db, AssetInterfaceCreate(**data))


@router.post("/bulk", response_model=List[AssetInterface])
@audit_log_action("create", "AssetInterface", model_class=AssetInterface)
def create_asset_interfaces_bulk(
    interfaces_in: List[AssetInterfaceCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Set tenant_id if missing on each interface
    interfaces = []
    for interface in interfaces_in:
        data = interface.model_dump()
        if not data.get("tenant_id"):
            data["tenant_id"] = current_user.tenant_id
        interfaces.append(AssetInterfaceCreate(**data))
    return create_interfaces_bulk(db, interfaces)


@router.get("/{interface_id}", response_model=AssetInterface)
def read_asset_interface(interface_id: UUID, db: Session = Depends(get_db)):
    interface = get_interface(db, interface_id)
    if not interface:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_INTERFACE_NOT_FOUND
        )
    return interface


@router.get("/by-asset/{asset_id}", response_model=List[AssetInterface])
def read_interfaces_by_asset(asset_id: UUID, db: Session = Depends(get_db)):
    return get_interfaces_by_asset(db, asset_id)


@router.put("/{interface_id}", response_model=AssetInterface)
@audit_log_action("update", "AssetInterface", model_class=AssetInterface)
def update_asset_interface(
    interface_id: UUID,
    interface_in: AssetInterfaceUpdate,
    db: Session = Depends(get_db),
):
    interface = update_interface(db, interface_id, interface_in)
    if not interface:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_INTERFACE_NOT_FOUND
        )
    return interface


@router.delete("/{interface_id}", response_model=AssetInterface)
@audit_log_action("delete", "AssetInterface", model_class=AssetInterface)
def delete_asset_interface(interface_id: UUID, db: Session = Depends(get_db)):
    interface = delete_interface(db, interface_id)
    if not interface:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_INTERFACE_NOT_FOUND
        )
    return interface
