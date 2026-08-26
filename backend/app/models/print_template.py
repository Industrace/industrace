from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base


class PrintTemplate(Base):
    __tablename__ = "print_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_print_templates_tenant_key"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True
    )
    key = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    name_translations = Column(JSONB, default=dict)
    description = Column(Text)
    description_translations = Column(JSONB, default=dict)
    icon = Column(String(100))
    component = Column(String(100))
    options = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
