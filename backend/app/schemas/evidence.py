# backend/app/schemas/evidence.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class EvidenceBase(BaseModel):
    source: str = Field(..., description="Source: manual, document, import, probe")
    type: Optional[str] = None
    description: str = Field(..., max_length=500)
    raw_data: Optional[dict] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Relazioni opzionali
    asset_id: Optional[UUID] = None
    zone_id: Optional[UUID] = None
    conduit_id: Optional[UUID] = None
    capability_id: Optional[UUID] = None
    sr_assessment_id: Optional[UUID] = None


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceUpdate(BaseModel):
    source: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    raw_data: Optional[dict] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    asset_id: Optional[UUID] = None
    zone_id: Optional[UUID] = None
    conduit_id: Optional[UUID] = None
    capability_id: Optional[UUID] = None
    sr_assessment_id: Optional[UUID] = None


class EvidenceRead(EvidenceBase):
    id: UUID
    tenant_id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class EvidenceResponse(EvidenceRead):
    """Response con informazioni aggiuntive"""
    creator_name: Optional[str] = None
    asset_name: Optional[str] = None
    zone_name: Optional[str] = None
    capability_name: Optional[str] = None

