# backend/app/models/notification_preference.py
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Notification Type
    notification_type = Column(String(50), nullable=False)  # 'asset_review', 'risk_alert', etc.
    
    # Channels
    email_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)  # Per futuro
    
    # Frequency
    frequency = Column(String(20), default="immediate")  # 'immediate', 'daily_digest', 'weekly_digest'
    
    # Filters
    severity_min = Column(Integer, nullable=True)  # Solo alert con severity >= questo
    filters = Column(JSONB, nullable=True)  # Filtri aggiuntivi (es: solo asset di certi site)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Unique constraint: user + notification_type
    __table_args__ = (
        UniqueConstraint('user_id', 'notification_type', name='uq_user_notification_type'),
    )

