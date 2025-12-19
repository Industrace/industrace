# backend/app/models/sr_assessment_evidence.py
"""
SR Assessment Evidence Model

Evidenze che collegano Asset e Capability a una valutazione SR.
"I seguenti asset sono stati considerati per questa valutazione"
"""
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SRAssessmentEvidence(Base):
    """
    Evidenza di una valutazione SR.
    Collega un Asset e una Capability a una valutazione SR.
    Tenant-specific.
    """
    __tablename__ = "sr_assessment_evidence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Assessment Reference
    sr_assessment_id = Column(UUID(as_uuid=True), ForeignKey("sr_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Evidence Details
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    capability_id = Column(UUID(as_uuid=True), ForeignKey("security_capabilities.id", ondelete="CASCADE"), nullable=False)
    
    # Comment
    comment = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    assessment = relationship("SRAssessment", back_populates="evidence")
    asset = relationship("Asset")
    capability = relationship("SecurityCapability", back_populates="assessment_evidence")
    
    def __repr__(self):
        return f"<SRAssessmentEvidence(sr_assessment_id={self.sr_assessment_id}, asset_id={self.asset_id}, capability_id={self.capability_id})>"

