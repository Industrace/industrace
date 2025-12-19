# backend/app/models/asset_zone_membership.py
"""
Asset Zone Membership Model

Permette a un asset di appartenere a più Security Zones con ruoli diversi.
Questo è conforme a ISA/IEC 62443 dove un asset può avere interfacce diverse
che appartengono a zone diverse.

Esempio:
- HMI-01 in Control Zone con ruolo "operator_interface"
- HMI-01 in DMZ con ruolo "data_publisher"
"""
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AssetZoneMembership(Base):
    """
    Rappresenta l'appartenenza di un asset a una Security Zone con un ruolo specifico.
    
    Un asset può avere multiple memberships, ognuna con un ruolo diverso.
    Questo permette di modellare scenari reali dove un asset ha interfacce diverse
    che appartengono a zone diverse (es: HMI con interfaccia operator in Control Zone
    e interfaccia data publisher in DMZ).
    """
    __tablename__ = "asset_zone_memberships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Asset e Zone
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    security_zone_id = Column(UUID(as_uuid=True), ForeignKey("security_zones.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Ruolo nella zona
    role = Column(String(100), nullable=False)
    # Valori comuni: 'operator_interface', 'data_publisher', 'control_interface', 
    # 'monitoring', 'data_collector', 'gateway', 'primary', 'secondary', etc.
    
    # Scope opzionale (quale interfaccia dell'asset appartiene a questa zona)
    interface_scope = Column(String(255), nullable=True)
    # Può essere: nome interfaccia, IP address, o descrizione dell'interfaccia
    
    # Security Level Target override (opzionale, altrimenti usa quello della zona)
    sl_target = Column(Integer, nullable=True)  # 1-4
    
    # Note
    notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    asset = relationship("Asset", back_populates="zone_memberships")
    security_zone = relationship("SecurityZone", back_populates="asset_memberships")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('sl_target IS NULL OR (sl_target >= 1 AND sl_target <= 4)', name='check_sl_target_range'),
        # Unique constraint: un asset non può avere lo stesso ruolo nella stessa zona
        # (ma può avere ruoli diversi nella stessa zona)
    )
    
    def __repr__(self):
        return f"<AssetZoneMembership(asset_id={self.asset_id}, zone_id={self.security_zone_id}, role='{self.role}')>"

