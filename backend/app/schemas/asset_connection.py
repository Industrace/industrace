# backend/schemas/asset_connection.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

from .asset import AssetSummary
from .asset_interface import AssetInterface


class AssetConnection(BaseModel):
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
    parent_asset: Optional[AssetSummary] = None
    child_asset: Optional[AssetSummary] = None
    local_interface_id: Optional[uuid.UUID] = None
    remote_interface_id: Optional[uuid.UUID] = None
    local_interface: Optional[AssetInterface] = None
    remote_interface: Optional[AssetInterface] = None

    model_config = ConfigDict(from_attributes=True)


class AssetConnectionCreate(BaseModel):
    local_interface_id: uuid.UUID
    remote_interface_id: uuid.UUID
    # optional for backward compatibility
    parent_asset_id: Optional[uuid.UUID] = None
    child_asset_id: Optional[uuid.UUID] = None
    connection_type: Optional[str] = None
    port_parent: Optional[str] = None
    port_child: Optional[str] = None
    protocol: Optional[str] = None
    description: Optional[str] = None


class AssetConnectionUpdate(BaseModel):
    local_interface_id: Optional[uuid.UUID] = None
    remote_interface_id: Optional[uuid.UUID] = None
    connection_type: Optional[str] = None
    port_parent: Optional[str] = None
    port_child: Optional[str] = None
    protocol: Optional[str] = None
    description: Optional[str] = None
