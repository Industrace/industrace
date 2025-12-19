# backend/app/models/conduit.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Conduit(Base):
    """
    ISA/IEC 62443 Conduit.
    Communication path between Security Zones.
    """
    __tablename__ = "conduits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Zone Relationships
    from_zone_id = Column(UUID(as_uuid=True), ForeignKey("security_zones.id"), nullable=False)
    to_zone_id = Column(UUID(as_uuid=True), ForeignKey("security_zones.id"), nullable=False)
    
    # Conduit Information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    conduit_type = Column(String(50), nullable=True)  # 'network', 'serial', 'wireless', 'vpn', etc.
    
    # Security Properties
    is_encrypted = Column(Boolean, default=False)
    encryption_type = Column(String(50), nullable=True)  # 'tls', 'ipsec', 'proprietary', etc.
    authentication_required = Column(Boolean, default=True)
    authentication_method = Column(String(50), nullable=True)  # 'certificate', 'psk', 'username_password', etc.
    
    # Network Details
    protocol = Column(String(50), nullable=True)  # 'tcp', 'udp', 'modbus', 'opcua', etc.
    port_range = Column(String(100), nullable=True)  # '502', '502-510', etc.
    allowed_direction = Column(String(50), default="bidirectional")  # 'unidirectional', 'bidirectional', 'request_response'
    
    # Governance
    flow_justification = Column(Text, nullable=True)  # Motivazione del flusso (principio "least privilege")
    ownership = Column(String(255), nullable=True)  # Chi è responsabile della manutenzione
    
    # ISA/IEC 62443 Security Level
    security_level_target = Column(Integer, nullable=True)  # Target SL for conduit
    security_level_achieved = Column(Integer, nullable=True)  # Achieved SL
    
    # Compliance
    compliance_status = Column(String(20), default="not_assessed")
    last_assessment_date = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    from_zone = relationship("SecurityZone", foreign_keys=[from_zone_id], back_populates="conduits_from")
    to_zone = relationship("SecurityZone", foreign_keys=[to_zone_id], back_populates="conduits_to")
    compliance_records = relationship("SecurityRequirementCompliance", back_populates="conduit")
    conduit_assets = relationship("ConduitAsset", back_populates="conduit", cascade="all, delete-orphan")

