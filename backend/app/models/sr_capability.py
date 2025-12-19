# backend/app/models/sr_capability.py
"""
SR-Capability Mapping Model

Mappa i Security Requirements alle Security Capabilities richieste,
con un livello di importanza (primary, supporting).
"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SRCapability(Base):
    """
    Mapping tra Security Requirement e Security Capability.
    System-wide reference data (no tenant_id).
    """
    __tablename__ = "sr_capabilities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    sr_id = Column(UUID(as_uuid=True), ForeignKey("security_requirements.id", ondelete="CASCADE"), nullable=False)
    capability_id = Column(UUID(as_uuid=True), ForeignKey("security_capabilities.id", ondelete="CASCADE"), nullable=False)
    
    # Importance level
    importance = Column(String(20), nullable=False, default="primary")  # 'primary', 'supporting'
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    security_requirement = relationship("SecurityRequirement", back_populates="capability_mappings")
    capability = relationship("SecurityCapability", back_populates="sr_mappings")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("importance IN ('primary', 'supporting')", name="check_importance_values"),
        # Unique constraint: un SR non può avere la stessa capability con la stessa importance più volte
        # (ma può avere la stessa capability con importance diversa - non ha senso, ma non lo impediamo)
    )
    
    def __repr__(self):
        return f"<SRCapability(sr_id={self.sr_id}, capability_id={self.capability_id}, importance='{self.importance}')>"

