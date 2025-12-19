# backend/app/models/security_capability.py
"""
Security Capability Model

Rappresenta una capacità di sicurezza che può essere richiesta da un Security Requirement
e valutata su un Asset o Conduit.

Esempi:
- authentication (autenticazione)
- logging (registrazione eventi)
- rbac (role-based access control)
- encryption (cifratura)
- session_management (gestione sessioni)
- network_segmentation (segmentazione di rete)
"""
import uuid
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SecurityCapability(Base):
    """
    Security Capability.
    System-wide reference data (no tenant_id).
    """
    __tablename__ = "security_capabilities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Capability Identifier
    code = Column(String(100), unique=True, nullable=False)  # e.g., "firewall_enforcement", "authentication"
    name = Column(String(255), nullable=False)  # Human-readable name
    
    # Capability Classification
    category = Column(String(50), nullable=True)  # 'identity', 'boundary', 'monitoring', 'system_integrity', etc.
    
    # Applicability (where this capability can be applied)
    applies_to_asset = Column(Boolean, default=True)
    applies_to_zone = Column(Boolean, default=False)
    applies_to_conduit = Column(Boolean, default=True)
    
    # Typical roles (for UX guidance only, not for calculations)
    typical_roles = Column(JSONB, default=list)  # e.g., ["firewall", "router", "plc", "hmi"]
    
    # Capability Details
    description = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    sr_mappings = relationship("SRCapability", back_populates="capability")
    asset_capabilities = relationship("AssetCapability", back_populates="capability")
    assessment_evidence = relationship("SRAssessmentEvidence", back_populates="capability")
    
    def __repr__(self):
        return f"<SecurityCapability(code='{self.code}')>"

