# backend/app/models/notification_template.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    __table_args__ = (
        UniqueConstraint('template_code', 'tenant_id', name='uq_notification_templates_code_tenant'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)  # NULL = system-wide
    
    # Template Info
    template_code = Column(String(50), nullable=False)  # es: "asset_review_due" - unique with tenant_id
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Email Content
    subject_template = Column(String(500), nullable=False)  # Template string con variabili
    body_template_html = Column(Text, nullable=False)  # HTML template
    body_template_text = Column(Text, nullable=True)  # Plain text fallback
    
    # Variables
    variables = Column(JSONB, nullable=True)  # Lista variabili disponibili: ["asset_name", "days_until_review", etc.]
    
    # Status
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

