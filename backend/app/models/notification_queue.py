# backend/app/models/notification_queue.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base


class NotificationQueue(Base):
    __tablename__ = "notification_queue"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Recipient
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String(255), nullable=False)
    
    # Notification
    notification_type = Column(String(50), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("notification_templates.id"), nullable=True)
    
    # Content (rendered)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)
    
    # Context
    context_data = Column(JSONB, nullable=True)  # Dati contestuali (asset_id, etc.)
    
    # Status
    status = Column(String(20), default="pending")  # 'pending', 'sent', 'failed', 'cancelled'
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Scheduling
    scheduled_for = Column(DateTime, default=func.now(), index=True)
    created_at = Column(DateTime, default=func.now())


# Index for queue processing
Index('idx_notification_queue_scheduled', NotificationQueue.status, NotificationQueue.scheduled_for)

