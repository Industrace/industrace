# backend/models/tenant.py
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default={})
    default_review_interval_months = Column(Integer, default=6)  # Intervallo review default per asset
    review_due_days_ahead = Column(Integer, default=30)  # Giorni di anticipo per "in scadenza" (due)
    review_upcoming_days_ahead = Column(Integer, default=30)  # Giorni di anticipo per "in arrivo" (upcoming)
    smtp_config = relationship(
        "TenantSMTPConfig", uselist=False, back_populates="tenant"
    )
    sso_config = relationship(
        "TenantSSOConfig", uselist=False, back_populates="tenant"
    )
    syslog_config = relationship(
        "TenantSyslogConfig", uselist=False, back_populates="tenant"
    )
    api_keys = relationship("ApiKey", back_populates="tenant")
    areas = relationship("Area", back_populates="tenant")

    network_probes = relationship("NetworkProbe", back_populates="tenant")
    discovered_devices = relationship("DiscoveredDevice", back_populates="tenant")
