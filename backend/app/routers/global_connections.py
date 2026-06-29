# routers/global_connections.py

import uuid
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.database import get_db
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.models import User, AssetConnection
from app.schemas import AssetConnection as AssetConnectionSchema
from app.crud import asset_connections as crud_assetconnections

router = APIRouter(
    prefix="/asset-connections",
    tags=["connections"],
    dependencies=[Depends(require_section_access("assets"))],
)


@router.get("", response_model=List[AssetConnectionSchema])
def get_all_connections(
    site_id: uuid.UUID = Query(None, description="Filter by site ID"),
    asset_type_id: uuid.UUID = Query(None, description="Filter by asset type ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all asset connections in the tenant's infrastructure.
    Optionally filter by site or asset type.
    """
    return crud_assetconnections.get_all_connections(
        db, 
        current_user.tenant_id,
        site_id=site_id,
        asset_type_id=asset_type_id
    )


@router.get("/network-topology")
def get_network_topology(
    site_id: uuid.UUID = Query(None, description="Filter by site ID"),
    asset_type_id: uuid.UUID = Query(None, description="Filter by asset type ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get network topology data including nodes and edges for visualization.
    """
    return crud_assetconnections.get_network_topology(
        db,
        current_user.tenant_id,
        site_id=site_id,
        asset_type_id=asset_type_id
    )


@router.get("/statistics")
def get_connection_statistics(
    site_id: uuid.UUID = Query(None, description="Filter by site ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get connection statistics for the network map.
    """
    return crud_assetconnections.get_connection_statistics(
        db,
        current_user.tenant_id,
        site_id=site_id
    ) 