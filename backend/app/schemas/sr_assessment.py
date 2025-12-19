# backend/app/schemas/sr_assessment.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class SRAssessmentBase(BaseModel):
    sr_id: UUID
    object_type: str  # 'zone', 'conduit'
    object_id: UUID
    status: str  # 'compliant', 'non_compliant', 'partial', 'not_applicable', 'insufficient_info'
    justification: Optional[str] = None
    assessor_id: Optional[UUID] = None


class SRAssessmentCreate(SRAssessmentBase):
    pass


class SRAssessmentUpdate(BaseModel):
    status: Optional[str] = None
    justification: Optional[str] = None
    assessor_id: Optional[UUID] = None


class SRAssessmentRead(SRAssessmentBase):
    id: UUID
    tenant_id: UUID
    assessed_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SRAssessmentWithDetails(SRAssessmentRead):
    """SRAssessment with related SecurityRequirement and Evidence"""
    security_requirement: Optional[dict] = None  # Basic SR info (id, requirement_id, title)
    evidence: List[dict] = []  # List of evidence records

