# backend/app/models/sr_assessment.py
"""
SR Assessment Model

Valutazione di un Security Requirement per una Zone o Conduit.
Sostituisce SecurityRequirementCompliance con un modello più strutturato.
"""
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SRAssessment(Base):
    """
    Valutazione di un Security Requirement per una Zone o Conduit.
    Tenant-specific.
    """
    __tablename__ = "sr_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Requirement Reference
    sr_id = Column(UUID(as_uuid=True), ForeignKey("security_requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Object Reference (one of these must be set)
    object_type = Column(String(20), nullable=False)  # 'zone', 'conduit'
    object_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # zone_id or conduit_id
    
    # Assessment Status
    status = Column(String(30), nullable=False, default="insufficient_info")  # 'compliant', 'non_compliant', 'partial', 'not_applicable', 'insufficient_info'
    
    # Assessment Details
    justification = Column(Text, nullable=True)
    assessor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assessed_at = Column(DateTime, default=func.now())
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    security_requirement = relationship("SecurityRequirement", back_populates="assessments")
    assessor = relationship("User", foreign_keys=[assessor_id])
    evidence = relationship("SRAssessmentEvidence", back_populates="assessment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SRAssessment(sr_id={self.sr_id}, object_type='{self.object_type}', object_id={self.object_id}, status='{self.status}')>"

