# backend/app/models/notification_log.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Notification Info
    notification_type = Column(String(50), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Result
    status = Column(String(20), nullable=False)  # 'sent', 'failed', 'skipped'
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Context
    context_data = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), index=True)


# Index for querying logs
Index('idx_notification_logs_created', NotificationLog.created_at)
Index('idx_notification_logs_user_type', NotificationLog.user_id, NotificationLog.notification_type)

