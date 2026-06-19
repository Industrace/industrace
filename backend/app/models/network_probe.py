import uuid
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class NetworkProbe(Base):
    __tablename__ = "network_probes"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True)

    # Identificazione sonda
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    probe_type = Column(String(50), default="network")  # network, wireless, industrial

    # Configurazione rete
    interface_name = Column(String(100), nullable=False)
    interface_ip = Column(String(45), nullable=True)
    mirror_port = Column(String(100), nullable=True)

    # Configurazione sniffing
    promiscuous_mode = Column(Boolean, default=True)
    capture_filter = Column(String(500), nullable=True)  # BPF filter
    max_packet_size = Column(Integer, default=1518)
    buffer_size = Column(Integer, default=65536)

    # Configurazione analisi
    enabled_protocols = Column(JSONB, nullable=True)  # Lista protocolli
    sampling_rate = Column(Float, default=1.0)
    metadata_extraction = Column(Boolean, default=True)
    payload_analysis = Column(Boolean, default=False)

    # Stato operativo
    status = Column(String(20), default="inactive")  # active, inactive, error, maintenance
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    last_data_received = Column(DateTime(timezone=True), nullable=True)

    # Statistiche aggregate (best effort)
    total_packets_captured = Column(Integer, default=0)
    total_bytes_processed = Column(Integer, default=0)
    active_connections = Column(Integer, default=0)
    unique_devices_seen = Column(Integer, default=0)

    # Telecontrollo
    heartbeat_interval = Column(Integer, default=30)
    data_transmission_interval = Column(Integer, default=300)
    max_retry_attempts = Column(Integer, default=3)

    # Sicurezza
    api_key = Column(String(255), nullable=False, unique=True, index=True)
    encryption_enabled = Column(Boolean, default=True)
    ssl_verify = Column(Boolean, default=True)

    # Metadati aggiuntivi
    location_info = Column(JSONB, nullable=True)
    hardware_info = Column(JSONB, nullable=True)
    software_version = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_config_update = Column(DateTime(timezone=True), nullable=True)

    # Relazioni
    tenant = relationship("Tenant", back_populates="network_probes")
    site = relationship("Site", back_populates="network_probes")
    discovered_devices = relationship("DiscoveredDevice", back_populates="probe")


class ProbeHeartbeat(Base):
    __tablename__ = "probe_heartbeats"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    probe_id = Column(UUID(as_uuid=True), ForeignKey("network_probes.id"), nullable=False, index=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    status = Column(String(20), nullable=False)  # healthy, warning, error

    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    disk_usage = Column(Float, nullable=True)
    network_throughput = Column(Float, nullable=True)

    packets_per_second = Column(Float, nullable=True)
    bytes_per_second = Column(Float, nullable=True)
    active_connections = Column(Integer, nullable=True)

    error_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    last_error_message = Column(Text, nullable=True)

    probe = relationship("NetworkProbe")


class ProbeDataTransmission(Base):
    __tablename__ = "probe_data_transmissions"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    probe_id = Column(UUID(as_uuid=True), ForeignKey("network_probes.id"), nullable=False, index=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    transmission_type = Column(String(50), nullable=False)  # metadata, statistics, alert

    data_size = Column(Integer, nullable=False)  # bytes (payload size, o size stimata)
    compression_ratio = Column(Float, nullable=True)
    encryption_used = Column(Boolean, default=True)

    new_devices_discovered = Column(Integer, default=0)
    new_connections_detected = Column(Integer, default=0)
    protocol_breakdown = Column(JSONB, nullable=True)
    discovered_devices = Column(JSONB, nullable=True)  # Lista device (metadati)

    status = Column(String(20), default="success")  # success, failed, partial
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    probe = relationship("NetworkProbe")
