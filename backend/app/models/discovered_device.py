import uuid
import enum
from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class DeviceDiscoveryStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    MATCHED = "matched"
    IMPORTED = "imported"
    ASSIGNED = "assigned"
    IGNORED = "ignored"
    CONFLICT = "conflict"


class DiscoveredDevice(Base):
    __tablename__ = "discovered_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True)
    probe_id = Column(UUID(as_uuid=True), ForeignKey("network_probes.id"), nullable=False, index=True)

    mac_address = Column(String(17), nullable=False, index=True)
    ip_addresses = Column(JSONB, default=list)
    hostname = Column(String(255), nullable=True)

    vendor = Column(String(100), nullable=True)
    device_type = Column(String(100), nullable=True)
    protocols = Column(JSONB, default=list)
    firmware_version = Column(String(100), nullable=True)

    first_seen = Column(DateTime(timezone=True), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=False, index=True)
    discovery_count = Column(Integer, default=1)
    confidence_score = Column(Integer, default=0)

    status = Column(
        Enum(
            DeviceDiscoveryStatus,
            name="devicediscoverystatus",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=DeviceDiscoveryStatus.DISCOVERED.value,
    )
    matched_asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True)
    match_confidence = Column(Integer, default=0)
    match_reason = Column(String(255), nullable=True)

    raw_data = Column(JSONB, default=dict)
    notes = Column(Text, nullable=True)
    auto_import_enabled = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant", back_populates="discovered_devices")
    site = relationship("Site", back_populates="discovered_devices")
    probe = relationship("NetworkProbe", back_populates="discovered_devices")
    matched_asset = relationship("Asset", back_populates="discovered_devices")

    def __repr__(self) -> str:
        return f"<DiscoveredDevice(mac={self.mac_address}, status={self.status})>"
