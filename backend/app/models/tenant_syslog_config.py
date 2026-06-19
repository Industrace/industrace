import uuid
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class TenantSyslogConfig(Base):
    """Configurazione server syslog esterno per inoltro audit log."""
    __tablename__ = "tenant_syslog_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, unique=True
    )

    host = Column(String(255), nullable=True)
    port = Column(Integer, default=514, nullable=False)
    protocol = Column(String(10), default="udp", nullable=False)  # udp, tcp
    facility = Column(Integer, default=16, nullable=False)  # 0-23, 16=local0
    enabled = Column(Boolean, default=False, nullable=False)

    tenant = relationship("Tenant", back_populates="syslog_config")
