# backend/app/models/asset_capability.py
"""
Asset Capability Model

Valuta se un Asset supporta una specifica Security Capability.
Può essere manuale, inferito (in futuro), o incompleto.
"""
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AssetCapability(Base):
    """
    Valutazione di una Security Capability su un Asset.
    Tenant-specific.
    """
    __tablename__ = "asset_capabilities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # References
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    capability_id = Column(UUID(as_uuid=True), ForeignKey("security_capabilities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Support Level
    support_level = Column(String(20), nullable=False, default="unknown")  # 'supported', 'not_supported', 'unknown'
    
    # Assessment Details
    notes = Column(Text, nullable=True)
    evidence_ref = Column(String(500), nullable=True)  # Reference to document, config file, etc.
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    asset = relationship("Asset", back_populates="capabilities")
    capability = relationship("SecurityCapability", back_populates="asset_capabilities")
    
    def __repr__(self):
        return f"<AssetCapability(asset_id={self.asset_id}, capability_id={self.capability_id}, support_level='{self.support_level}')>"

