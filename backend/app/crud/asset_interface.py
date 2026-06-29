from sqlalchemy.orm import Session
from app.models.asset_interface import AssetInterface
from app.schemas.asset_interface import AssetInterfaceCreate, AssetInterfaceUpdate
from uuid import UUID
from app.models.asset_connection import AssetConnection


def create_interface(db: Session, interface_in: AssetInterfaceCreate):
    db_interface = AssetInterface(**interface_in.model_dump())
    db.add(db_interface)
    db.commit()
    db.refresh(db_interface)
    return db_interface


def get_interface(db: Session, interface_id: UUID):
    return db.query(AssetInterface).filter(AssetInterface.id == interface_id).first()


def get_interfaces_by_asset(db: Session, asset_id: UUID):
    return db.query(AssetInterface).filter(AssetInterface.asset_id == asset_id).all()


def update_interface(
    db: Session, interface_id: UUID, interface_in: AssetInterfaceUpdate
):
    db_interface = get_interface(db, interface_id)
    if not db_interface:
        return None
    for field, value in interface_in.model_dump(exclude_unset=True).items():
        setattr(db_interface, field, value)
    db.commit()
    db.refresh(db_interface)
    return db_interface


def delete_interface(db: Session, interface_id: UUID):
    db_interface = get_interface(db, interface_id)
    if not db_interface:
        return None
    # Check: is the interface used in asset_connections?
    used = (
        db.query(AssetConnection)
        .filter(
            (AssetConnection.local_interface_id == interface_id)
            | (AssetConnection.remote_interface_id == interface_id)
        )
        .first()
    )
    if used:
        # Don't delete, it's still referenced
        return None
    db.delete(db_interface)
    db.commit()
    return db_interface


def create_interfaces_bulk(db: Session, interfaces_in: list[AssetInterfaceCreate]):
    db_interfaces = [AssetInterface(**interface.model_dump()) for interface in interfaces_in]
    db.add_all(db_interfaces)
    db.commit()
    for db_interface in db_interfaces:
        db.refresh(db_interface)
    return db_interfaces
