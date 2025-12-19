# backend/app/models/security_requirement_compliance.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SecurityRequirementCompliance(Base):
    """
    ISA/IEC 62443 Compliance Record.
    Tracks compliance status of Security Requirements for Zones, Conduits, or Assets.
    """
    __tablename__ = "security_requirement_compliance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Requirement Reference
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("security_requirements.id"), nullable=False)
    
    # Entity Reference (one of these must be set)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("security_zones.id"), nullable=True)
    conduit_id = Column(UUID(as_uuid=True), ForeignKey("conduits.id"), nullable=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True)
    
    # Compliance Status
    compliance_status = Column(String(20), nullable=False)  # 'compliant', 'non_compliant', 'partial', 'not_applicable', 'not_assessed'
    compliance_percentage = Column(Integer, nullable=True)  # 0-100, for partial compliance
    
    # Assessment Details
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assessment_date = Column(DateTime, default=func.now())
    assessment_notes = Column(Text, nullable=True)
    
    # Evidence
    evidence_documents = Column(JSONB, nullable=True)  # List of document IDs/URLs
    evidence_notes = Column(Text, nullable=True)
    
    # Remediation
    remediation_required = Column(Boolean, default=False)
    remediation_plan = Column(Text, nullable=True)
    remediation_deadline = Column(DateTime, nullable=True)
    remediation_status = Column(String(20), nullable=True)  # 'planned', 'in_progress', 'completed', 'deferred'
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    requirement = relationship("SecurityRequirement", back_populates="compliance_records")
    zone = relationship("SecurityZone", back_populates="compliance_records")
    conduit = relationship("Conduit", back_populates="compliance_records")
    asset = relationship("Asset", back_populates="compliance_records")
    assessor = relationship("User", foreign_keys=[assessed_by])

