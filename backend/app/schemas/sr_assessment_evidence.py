# backend/app/schemas/sr_assessment_evidence.py
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SRAssessmentEvidenceBase(BaseModel):
    sr_assessment_id: UUID
    asset_id: UUID
    capability_id: UUID
    comment: Optional[str] = None


class SRAssessmentEvidenceCreate(SRAssessmentEvidenceBase):
    pass


class SRAssessmentEvidenceUpdate(BaseModel):
    comment: Optional[str] = None


class SRAssessmentEvidenceRead(SRAssessmentEvidenceBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SRAssessmentEvidenceWithDetails(SRAssessmentEvidenceRead):
    """SRAssessmentEvidence with related Asset and SecurityCapability details"""
    asset: Optional[dict] = None  # Basic asset info (id, name)
    capability: Optional[dict] = None  # Basic capability info (id, code, description)

