from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid


class AssetStatusBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#64748b"
    active: Optional[bool] = True
    order: Optional[int] = 0


class AssetStatusCreate(AssetStatusBase):
    pass


class AssetStatusUpdate(AssetStatusBase):
    pass


class AssetStatus(AssetStatusBase):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)
