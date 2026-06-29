# backend/schemas/asset_document.py

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class AssetDocumentBase(BaseModel):
    asset_id: uuid.UUID
    name: str
    file_path: str
    description: Optional[str] = None


class AssetDocumentCreate(AssetDocumentBase):
    tenant_id: uuid.UUID


class AssetDocument(AssetDocumentBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    uploaded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
