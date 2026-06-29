# backend/crud/asset_connections.py

from typing import List, Optional
import uuid
from app.models import AssetConnection
from app.schemas.asset_connection import AssetConnectionCreate, AssetConnectionUpdate
from sqlalchemy.orm import Session


def create_asset_connection(
    db: Session, connection_in: AssetConnectionCreate, tenant_id: uuid.UUID
) -> AssetConnection:
    """Create a new connection between assets"""
    from app.models.asset_interface import AssetInterface

    # Retrieve interfaces
    local_iface = (
        db.query(AssetInterface)
        .filter(AssetInterface.id == connection_in.local_interface_id)
        .first()
    )
    remote_iface = (
        db.query(AssetInterface)
        .filter(AssetInterface.id == connection_in.remote_interface_id)
        .first()
    )
    # Set parent/child asset if not present
    if local_iface and not connection_in.parent_asset_id:
        connection_in.parent_asset_id = local_iface.asset_id
    if remote_iface and not connection_in.child_asset_id:
        connection_in.child_asset_id = remote_iface.asset_id
    # Set connection_type if not present
    if not connection_in.connection_type and local_iface:
        connection_in.connection_type = local_iface.type
    connection = AssetConnection(**connection_in.model_dump(), tenant_id=tenant_id)
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection


def get_asset_connection(
    db: Session, connection_id: uuid.UUID, tenant_id: uuid.UUID
) -> Optional[AssetConnection]:
    """Retrieve a connection by ID"""
    return (
        db.query(AssetConnection)
        .filter(
            AssetConnection.id == connection_id, AssetConnection.tenant_id == tenant_id
        )
        .first()
    )


def list_asset_connections(
    db: Session, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[AssetConnection]:
    """List all connections of a tenant with pagination"""
    return (
        db.query(AssetConnection)
        .filter(AssetConnection.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_asset_connections_by_parent(
    db: Session, parent_asset_id: uuid.UUID, tenant_id: uuid.UUID
) -> List[AssetConnection]:
    """Retrieve all connections where an asset is parent"""
    return (
        db.query(AssetConnection)
        .filter(
            AssetConnection.parent_asset_id == parent_asset_id,
            AssetConnection.tenant_id == tenant_id,
        )
        .all()
    )


def get_asset_connections_by_child(
    db: Session, child_asset_id: uuid.UUID, tenant_id: uuid.UUID
) -> List[AssetConnection]:
    """Retrieve all connections where an asset is child"""
    return (
        db.query(AssetConnection)
        .filter(
            AssetConnection.child_asset_id == child_asset_id,
            AssetConnection.tenant_id == tenant_id,
        )
        .all()
    )


def update_asset_connection(
    db: Session, connection: AssetConnection, update_data: AssetConnectionUpdate
) -> AssetConnection:
    """Update an existing connection"""
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(connection, key, value)
    db.commit()
    db.refresh(connection)
    return connection


def delete_asset_connection(db: Session, connection: AssetConnection) -> None:
    """Delete a connection"""
    db.delete(connection)
    db.commit()


def get_all_connections(
    db: Session, 
    tenant_id: uuid.UUID,
    site_id: uuid.UUID = None,
    asset_type_id: uuid.UUID = None
) -> List[AssetConnection]:
    """Get all connections with optional filtering"""
    query = db.query(AssetConnection).filter(AssetConnection.tenant_id == tenant_id)
    
    if site_id:
        # Filter by site - need to join with assets
        from app.models.asset import Asset
        query = query.join(Asset, AssetConnection.parent_asset_id == Asset.id).filter(Asset.site_id == site_id)
    
    if asset_type_id:
        # Filter by asset type - need to join with assets
        from app.models.asset import Asset
        query = query.join(Asset, AssetConnection.parent_asset_id == Asset.id).filter(Asset.asset_type_id == asset_type_id)
    
    return query.all()


def get_network_topology(
    db: Session,
    tenant_id: uuid.UUID,
    site_id: uuid.UUID = None,
    asset_type_id: uuid.UUID = None
) -> dict:
    """Get network topology data for visualization"""
    connections = get_all_connections(db, tenant_id, site_id, asset_type_id)
    
    # Get unique assets from connections
    asset_ids = set()
    for conn in connections:
        if conn.parent_asset_id:
            asset_ids.add(conn.parent_asset_id)
        if conn.child_asset_id:
            asset_ids.add(conn.child_asset_id)
    
    # Get asset details
    from app.models.asset import Asset
    from app.models.asset_type import AssetType
    from app.models.site import Site
    from app.models.asset_status import AssetStatus
    
    assets = (
        db.query(Asset)
        .join(AssetType, Asset.asset_type_id == AssetType.id)
        .join(Site, Asset.site_id == Site.id)
        .join(AssetStatus, Asset.status_id == AssetStatus.id)
        .filter(Asset.id.in_(asset_ids))
        .all()
    )
    
    # Build nodes and edges
    nodes = []
    edges = []
    
    for asset in assets:
        nodes.append({
            "id": str(asset.id),
            "label": asset.name,
            "type": asset.asset_type.name,
            "site": asset.site.name,
            "status": asset.status.name,
            "risk_score": asset.risk_score
        })
    
    for conn in connections:
        if conn.parent_asset_id and conn.child_asset_id:
            edges.append({
                "from": str(conn.parent_asset_id),
                "to": str(conn.child_asset_id),
                "type": conn.connection_type,
                "protocol": conn.protocol
            })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "total_assets": len(nodes),
        "total_connections": len(edges)
    }


def get_connection_statistics(
    db: Session,
    tenant_id: uuid.UUID,
    site_id: uuid.UUID = None
) -> dict:
    """Get connection statistics"""
    from app.models.asset import Asset
    from sqlalchemy import func
    
    # Base query for assets
    asset_query = db.query(Asset).filter(Asset.tenant_id == tenant_id)
    if site_id:
        asset_query = asset_query.filter(Asset.site_id == site_id)
    
    total_assets = asset_query.count()
    
    # Get connected assets
    connected_asset_ids = set()
    connections = get_all_connections(db, tenant_id, site_id)
    
    for conn in connections:
        if conn.parent_asset_id:
            connected_asset_ids.add(conn.parent_asset_id)
        if conn.child_asset_id:
            connected_asset_ids.add(conn.child_asset_id)
    
    connected_assets = len(connected_asset_ids)
    isolated_assets = total_assets - connected_assets
    total_connections = len(connections)
    
    return {
        "total_assets": total_assets,
        "connected_assets": connected_assets,
        "isolated_assets": isolated_assets,
        "total_connections": total_connections
    }
