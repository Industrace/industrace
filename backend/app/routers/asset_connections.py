# routers/asset_connections.py

import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.audit_decorator import audit_log_action
from app.database import get_db
from app.services.auth import get_current_user
from app.models import User, AssetConnection
from app.schemas import (
    AssetConnection as AssetConnectionSchema,
    AssetConnectionCreate,
    AssetConnectionUpdate,
)
from app.crud import asset_connections as crud_assetconnections
from app.services.connection_dependency_analyzer import ConnectionDependencyAnalyzer
from typing import Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assets/{asset_id}/connections",
    tags=["assets"],
)


class AssetConnectionWithDependencyStatus(BaseModel):
    """Extended AssetConnection schema with dependency status"""
    id: uuid.UUID
    tenant_id: uuid.UUID
    parent_asset_id: Optional[uuid.UUID] = None
    child_asset_id: Optional[uuid.UUID] = None
    connection_type: Optional[str] = None
    port_parent: Optional[str] = None
    port_child: Optional[str] = None
    protocol: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    parent_asset: Optional[dict] = None
    child_asset: Optional[dict] = None
    local_interface_id: Optional[uuid.UUID] = None
    remote_interface_id: Optional[uuid.UUID] = None
    dependency_status: Optional[dict] = None
    
    class Config:
        from_attributes = True


@router.get("")
def list_connections(
    asset_id: uuid.UUID,
    include_dependency_status: bool = Query(False, description="Include dependency status in response"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List connections for an asset, optionally including dependency status"""
    from sqlalchemy.orm import joinedload
    
    # Get connections where the asset is parent or child with eager loading
    parent_connections = (
        db.query(AssetConnection)
        .options(
            joinedload(AssetConnection.parent_asset),
            joinedload(AssetConnection.child_asset),
            joinedload(AssetConnection.local_interface),
            joinedload(AssetConnection.remote_interface)
        )
        .filter(
            AssetConnection.parent_asset_id == asset_id,
            AssetConnection.tenant_id == current_user.tenant_id
        )
        .all()
    )
    
    child_connections = (
        db.query(AssetConnection)
        .options(
            joinedload(AssetConnection.parent_asset),
            joinedload(AssetConnection.child_asset),
            joinedload(AssetConnection.local_interface),
            joinedload(AssetConnection.remote_interface)
        )
        .filter(
            AssetConnection.child_asset_id == asset_id,
            AssetConnection.tenant_id == current_user.tenant_id
        )
        .all()
    )
    
    all_connections = parent_connections + child_connections
    
    # Add dependency status if requested
    if include_dependency_status:
        result = []
        for conn in all_connections:
            try:
                dependency_status = ConnectionDependencyAnalyzer.get_connection_dependency_status(db, conn)
            except Exception as e:
                # Se c'è un errore nel calcolo, usa uno stato di default
                logger.warning(f"Error calculating dependency status for connection {conn.id}: {e}", exc_info=True)
                dependency_status = {
                    'has_dependency': False,
                    'dependency_id': None,
                    'status': 'connection_only',
                    'severity': 'info',
                    'suggested_action': None,
                    'connection_type': getattr(conn, 'connection_type', None),
                    'is_critical': False
                }
            
            # Costruisci il dict mantenendo compatibilità con formato originale
            # Usa Pydantic per serializzare correttamente
            from app.schemas.asset_connection import AssetConnection as AssetConnectionSchema
            
            # Crea schema base
            conn_schema = AssetConnectionSchema.from_orm(conn)
            conn_dict = conn_schema.dict()
            
            # Aggiungi dependency_status
            conn_dict['dependency_status'] = dependency_status
            
            result.append(conn_dict)
        return result
    
    # Ritorna formato standard senza dependency_status usando schema Pydantic
    from app.schemas.asset_connection import AssetConnection as AssetConnectionSchema
    return [AssetConnectionSchema.from_orm(conn).dict() for conn in all_connections]


@router.get("/dependency-analysis")
def get_connections_dependency_analysis(
    asset_id: uuid.UUID,
    show_missing_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed dependency analysis for all connections"""
    connections_with_status = ConnectionDependencyAnalyzer.get_connections_with_dependency_status(
        db, asset_id, current_user.tenant_id
    )
    
    if show_missing_only:
        connections_with_status = [
            c for c in connections_with_status
            if c['dependency_status']['status'] == 'missing'
        ]
    
    return {
        'asset_id': str(asset_id),
        'total_connections': len(connections_with_status),
        'connections': connections_with_status,
        'summary': {
            'complete': len([c for c in connections_with_status if c['dependency_status']['status'] == 'complete']),
            'missing': len([c for c in connections_with_status if c['dependency_status']['status'] == 'missing']),
            'connection_only': len([c for c in connections_with_status if c['dependency_status']['status'] == 'connection_only'])
        }
    }


@router.get("/missing-dependencies")
def get_missing_dependencies(
    asset_id: uuid.UUID,
    critical_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get connections that are missing corresponding dependencies"""
    missing = ConnectionDependencyAnalyzer.find_missing_dependencies(
        db, current_user.tenant_id, critical_only
    )
    
    # Filter by asset_id if provided
    missing = [
        m for m in missing
        if str(m['parent_asset_id']) == str(asset_id) or str(m['child_asset_id']) == str(asset_id)
    ]
    
    return {
        'asset_id': str(asset_id),
        'missing_dependencies': missing,
        'count': len(missing)
    }


@router.post("/{connection_id}/suggest-dependency")
def suggest_dependency_from_connection(
    asset_id: uuid.UUID,
    connection_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Suggest dependency creation based on connection"""
    conn = crud_assetconnections.get_asset_connection(
        db, connection_id, current_user.tenant_id
    )
    if not conn:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_CONNECTION_NOT_FOUND
        )
    
    suggestion = ConnectionDependencyAnalyzer.suggest_dependency_from_connection(db, conn)
    return suggestion


@router.post("", response_model=AssetConnectionSchema)
@audit_log_action("create", "AssetConnection", model_class=AssetConnection)
def create_connection(
    asset_id: uuid.UUID,
    request: Request,
    data: AssetConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Set the asset_id as parent_asset_id if not specified
    if not data.parent_asset_id:
        data.parent_asset_id = asset_id
    return crud_assetconnections.create_asset_connection(
        db, data, current_user.tenant_id
    )


@router.put("/{connection_id}", response_model=AssetConnectionSchema)
@audit_log_action("update", "AssetConnection", model_class=AssetConnection)
def update_connection(
    asset_id: uuid.UUID,
    connection_id: uuid.UUID,
    request: Request,
    data: AssetConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = crud_assetconnections.get_asset_connection(
        db, connection_id, current_user.tenant_id
    )
    if not conn:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_CONNECTION_NOT_FOUND
        )
    return crud_assetconnections.update_asset_connection(db, conn, data)


@router.delete("/{connection_id}")
@audit_log_action("delete", "AssetConnection", model_class=AssetConnection)
def delete_connection(
    asset_id: uuid.UUID,
    connection_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = crud_assetconnections.get_asset_connection(
        db, connection_id, current_user.tenant_id
    )
    if not conn:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.ASSET_CONNECTION_NOT_FOUND
        )
    crud_assetconnections.delete_asset_connection(db, conn)
    return {"detail": "Connection deleted"}
