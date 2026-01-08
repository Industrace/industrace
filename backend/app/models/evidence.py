# backend/app/models/evidence.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Float, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Evidence(Base):
    """
    Evidence (Evidenza) per Security Capabilities e Security Requirements.
    Può essere collegata a Asset, Zone, Conduit, Capability o SRAssessment.
    """
    __tablename__ = "evidence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Source and Type
    source = Column(String(20), nullable=False)  # 'manual', 'document', 'import', 'probe'
    type = Column(String(50), nullable=True)  # Tipo di evidenza (text, enum opzionale)
    description = Column(String(500), nullable=False)
    raw_data = Column(JSONB, nullable=True)  # Dati grezzi opzionali
    
    # Confidence (opzionale, 0-1)
    confidence = Column(Float, nullable=True)
    
    # Relazioni opzionali (tutte nullable - evidence può essere "libera")
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("security_zones.id", ondelete="SET NULL"), nullable=True)
    conduit_id = Column(UUID(as_uuid=True), ForeignKey("conduits.id", ondelete="SET NULL"), nullable=True)
    capability_id = Column(UUID(as_uuid=True), ForeignKey("security_capabilities.id", ondelete="SET NULL"), nullable=True)
    sr_assessment_id = Column(UUID(as_uuid=True), ForeignKey("sr_assessments.id", ondelete="SET NULL"), nullable=True)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    # Note: Using lazy loading to avoid circular import issues
    asset = relationship("Asset", lazy="select")
    zone = relationship("SecurityZone", lazy="select")
    conduit = relationship("Conduit", lazy="select")
    capability = relationship("SecurityCapability", lazy="select")
    sr_assessment = relationship("SRAssessment", lazy="select")
    creator = relationship("User", foreign_keys=[created_by], lazy="select")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="check_confidence_range"),
        CheckConstraint("source IN ('manual', 'document', 'import', 'probe')", name="check_source_values"),
    )
    
    def __repr__(self):
        return f"<Evidence(id={self.id}, source='{self.source}', description='{self.description[:50]}...')>"

