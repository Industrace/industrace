from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional
from datetime import datetime


class AssetCommunicationBase(BaseModel):
    src_interface_id: UUID4
    dst_interface_id: UUID4
    packet_count: Optional[int] = 0


class AssetCommunicationCreate(AssetCommunicationBase):
    tenant_id: UUID4
    site_id: UUID4


class AssetCommunicationUpdate(BaseModel):
    packet_count: Optional[int]


class AssetCommunicationInDBBase(AssetCommunicationBase):
    id: UUID4
    tenant_id: UUID4
    site_id: UUID4
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class AssetCommunication(AssetCommunicationInDBBase):
    pass
