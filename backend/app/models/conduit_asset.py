# backend/app/models/conduit_asset.py
"""
Conduit Asset Model

Associa Asset a Conduit con un ruolo specifico (enforcement, monitoring).
Le capability dei conduit spesso arrivano da firewall, data diode, VPN gateway, IDS.
"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ConduitAsset(Base):
    """
    Associazione tra Conduit e Asset con un ruolo specifico.
    Tenant-specific.
    """
    __tablename__ = "conduit_assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # References
    conduit_id = Column(UUID(as_uuid=True), ForeignKey("conduits.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Role
    role = Column(String(50), nullable=False, default="enforcement")  # 'enforcement', 'monitoring', 'gateway', etc.
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    conduit = relationship("Conduit", back_populates="conduit_assets")
    asset = relationship("Asset", back_populates="conduit_assets")
    
    def __repr__(self):
        return f"<ConduitAsset(conduit_id={self.conduit_id}, asset_id={self.asset_id}, role='{self.role}')>"

