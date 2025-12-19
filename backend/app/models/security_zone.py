# backend/app/models/security_zone.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Boolean, Table
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


# Many-to-many table for SecurityZone <-> Location mapping
security_zone_locations = Table(
    "security_zone_locations",
    Base.metadata,
    Column(
        "security_zone_id",
        UUID(as_uuid=True),
        ForeignKey("security_zones.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "location_id",
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class SecurityZone(Base):
    """
    ISA/IEC 62443 Security Zone.
    Logical security boundary, not physical location.
    Assets can be assigned to zones, and zones can be mapped to physical locations.
    """
    __tablename__ = "security_zones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True)  # Optional: zone can span multiple sites
    
    # Zone Information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    zone_type = Column(String(50), nullable=True)  # 'process', 'safety', 'control', 'enterprise', etc.
    
    # ISA/IEC 62443 Security Level
    security_level_target = Column(Integer, nullable=True)  # Target SL (1-4)
    security_level_achieved = Column(Integer, nullable=True)  # Achieved SL (1-4)
    security_level_capability = Column(Integer, nullable=True)  # Capability SL (1-4)
    
    # Zone Properties
    is_dmz = Column(Boolean, default=False)  # Is this a DMZ zone?
    is_air_gapped = Column(Boolean, default=False)  # Is this zone air-gapped?
    network_segment = Column(String(100), nullable=True)  # Network segment/VLAN
    
    # Compliance
    compliance_status = Column(String(20), default="not_assessed")  # 'not_assessed', 'compliant', 'non_compliant', 'partial'
    last_assessment_date = Column(DateTime, nullable=True)
    next_assessment_date = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    assets = relationship("Asset", back_populates="security_zone", foreign_keys="Asset.security_zone_id")
    # DEPRECATED: assets è mantenuto per retrocompatibilità (usa security_zone_id)
    # Usare asset_memberships per supportare multiple zone con ruoli diversi
    asset_memberships = relationship("AssetZoneMembership", back_populates="security_zone", cascade="all, delete-orphan")
    conduits_from = relationship("Conduit", foreign_keys="Conduit.from_zone_id", back_populates="from_zone")
    conduits_to = relationship("Conduit", foreign_keys="Conduit.to_zone_id", back_populates="to_zone")
    locations = relationship("Location", secondary=security_zone_locations, backref="security_zones")
    compliance_records = relationship("SecurityRequirementCompliance", back_populates="zone")

