# backend/app/models/security_requirement.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SecurityRequirement(Base):
    """
    ISA/IEC 62443 Security Requirement.
    System-wide reference data (no tenant_id).
    Based on ISA/IEC 62443 standard requirements.
    """
    __tablename__ = "security_requirements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Requirement Identifier (from ISA/IEC 62443 standard)
    requirement_id = Column(String(50), unique=True, nullable=False)  # e.g., "SR 1.1", "FR 1.1"
    requirement_category = Column(String(50), nullable=True)  # 'SR', 'FR', 'CR' (Security, Foundational, Component)
    
    # Requirement Details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    requirement_text = Column(Text, nullable=True)  # Full requirement text from standard
    
    # Applicability
    applies_to_zones = Column(Boolean, default=True)  # Applies to Security Zones
    applies_to_conduits = Column(Boolean, default=True)  # Applies to Conduits
    applies_to_assets = Column(Boolean, default=False)  # Applies to individual Assets
    
    # Security Level
    min_security_level = Column(Integer, nullable=True)  # Minimum SL required (1-4)
    max_security_level = Column(Integer, nullable=True)  # Maximum SL applicable (1-4)
    
    # Metadata
    standard_version = Column(String(20), nullable=True)  # e.g., "62443-3-3:2013"
    section_reference = Column(String(100), nullable=True)  # Section in standard
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    compliance_records = relationship("SecurityRequirementCompliance", back_populates="requirement")
    capability_mappings = relationship("SRCapability", back_populates="security_requirement", cascade="all, delete-orphan")
    assessments = relationship("SRAssessment", back_populates="security_requirement", cascade="all, delete-orphan")

