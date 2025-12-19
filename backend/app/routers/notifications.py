# backend/app/routers/notifications.py
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import User, NotificationPreference, NotificationQueue, NotificationLog, NotificationTemplate
from app.services.auth import get_current_user
from app.services.audit_decorator import audit_log_action
from app.services.email_queue_processor import EmailQueueProcessor
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationPreferenceResponse(BaseModel):
    """Response for notification preference"""
    id: uuid.UUID
    notification_type: str
    email_enabled: bool
    in_app_enabled: bool
    frequency: str
    severity_min: Optional[int] = None
    filters: Optional[dict] = None
    
    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    """Update notification preference"""
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    frequency: Optional[str] = Field(None, pattern="^(immediate|daily_digest|weekly_digest)$")
    severity_min: Optional[int] = Field(None, ge=0, le=10)
    filters: Optional[dict] = None


class NotificationPreferenceCreate(BaseModel):
    """Create notification preference"""
    notification_type: str
    email_enabled: bool = True
    in_app_enabled: bool = True
    frequency: str = Field("immediate", pattern="^(immediate|daily_digest|weekly_digest)$")
    severity_min: Optional[int] = Field(None, ge=0, le=10)
    filters: Optional[dict] = None


class NotificationQueueResponse(BaseModel):
    """Response for notification queue entry"""
    id: uuid.UUID
    notification_type: str
    email: str
    subject: str
    status: str
    attempts: int
    scheduled_for: datetime
    created_at: datetime
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class NotificationLogResponse(BaseModel):
    """Response for notification log"""
    id: uuid.UUID
    notification_type: str
    status: str
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TestNotificationRequest(BaseModel):
    """Request to send test notification"""
    template_code: str
    email: str


@router.get("/templates", response_model=List[dict])
def list_notification_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List available notification templates"""
    templates = (
        db.query(NotificationTemplate)
        .filter(
            NotificationTemplate.enabled == True,
            # System-wide templates or tenant-specific
            (NotificationTemplate.tenant_id == current_user.tenant_id) | 
            (NotificationTemplate.tenant_id.is_(None))
        )
        .all()
    )
    
    return [
        {
            "template_code": t.template_code,
            "name": t.name,
            "description": t.description
        }
        for t in templates
    ]


@router.get("/preferences", response_model=List[NotificationPreferenceResponse])
def list_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List notification preferences for current user"""
    preferences = (
        db.query(NotificationPreference)
        .filter(
            NotificationPreference.user_id == current_user.id,
            NotificationPreference.tenant_id == current_user.tenant_id
        )
        .all()
    )
    
    return [NotificationPreferenceResponse.from_orm(p) for p in preferences]


@router.post("/preferences", response_model=NotificationPreferenceResponse, status_code=201)
def create_notification_preference(
    preference_data: NotificationPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create notification preference"""
    # Check if already exists
    existing = (
        db.query(NotificationPreference)
        .filter(
            NotificationPreference.user_id == current_user.id,
            NotificationPreference.notification_type == preference_data.notification_type
        )
        .first()
    )
    
    if existing:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.ASSET_NOT_FOUND,  # TODO: Create proper error code
            detail="Preference already exists for this notification type"
        )
    
    preference = NotificationPreference(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        **preference_data.dict()
    )
    
    db.add(preference)
    db.commit()
    db.refresh(preference)
    
    return NotificationPreferenceResponse.from_orm(preference)


@router.put("/preferences/{preference_id}", response_model=NotificationPreferenceResponse)
def update_notification_preference(
    preference_id: uuid.UUID,
    preference_data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update notification preference"""
    preference = (
        db.query(NotificationPreference)
        .filter(
            NotificationPreference.id == preference_id,
            NotificationPreference.user_id == current_user.id
        )
        .first()
    )
    
    if not preference:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    # Update fields
    update_data = preference_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(preference, key, value)
    
    db.commit()
    db.refresh(preference)
    
    return NotificationPreferenceResponse.from_orm(preference)


@router.delete("/preferences/{preference_id}")
@audit_log_action("delete_notification_preference", "NotificationPreference")
def delete_notification_preference(
    preference_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete notification preference"""
    preference = (
        db.query(NotificationPreference)
        .filter(
            NotificationPreference.id == preference_id,
            NotificationPreference.user_id == current_user.id
        )
        .first()
    )
    
    if not preference:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,  # TODO: Create proper error code
            detail="Preference not found"
        )
    
    db.delete(preference)
    db.commit()
    
    return None


@router.get("/queue", response_model=List[NotificationQueueResponse])
def list_notification_queue(
    status: Optional[str] = Query(None, description="Filter by status: pending, sent, failed"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List notification queue (admin only - filtered by tenant)"""
    query = (
        db.query(NotificationQueue)
        .filter(NotificationQueue.tenant_id == current_user.tenant_id)
    )
    
    if status:
        query = query.filter(NotificationQueue.status == status)
    
    queue_entries = query.order_by(NotificationQueue.created_at.desc()).limit(limit).all()
    
    return [NotificationQueueResponse.from_orm(entry) for entry in queue_entries]


@router.post("/queue/{queue_id}/retry", response_model=NotificationQueueResponse)
def retry_notification(
    queue_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retry sending a failed notification"""
    queue_entry = (
        db.query(NotificationQueue)
        .filter(
            NotificationQueue.id == queue_id,
            NotificationQueue.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    if not queue_entry:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    if queue_entry.status not in ['failed', 'pending']:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="Can only retry failed or pending notifications"
        )
    
    # Reset status
    queue_entry.status = 'pending'
    queue_entry.error_message = None
    
    db.commit()
    db.refresh(queue_entry)
    
    # Process immediately
    EmailQueueProcessor.process_queue(db, batch_size=1)
    
    return NotificationQueueResponse.from_orm(queue_entry)


@router.delete("/queue/{queue_id}", status_code=204)
def cancel_notification(
    queue_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a pending notification"""
    queue_entry = (
        db.query(NotificationQueue)
        .filter(
            NotificationQueue.id == queue_id,
            NotificationQueue.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    if not queue_entry:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)
    
    if queue_entry.status == 'sent':
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="Cannot cancel already sent notification"
        )
    
    queue_entry.status = 'cancelled'
    db.commit()
    
    return None


@router.get("/logs", response_model=List[NotificationLogResponse])
def list_notification_logs(
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user ID"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    from_date: Optional[datetime] = Query(None, description="From date"),
    to_date: Optional[datetime] = Query(None, description="To date"),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List notification logs"""
    query = (
        db.query(NotificationLog)
        .filter(NotificationLog.tenant_id == current_user.tenant_id)
    )
    
    if user_id:
        query = query.filter(NotificationLog.user_id == user_id)
    
    if notification_type:
        query = query.filter(NotificationLog.notification_type == notification_type)
    
    if from_date:
        query = query.filter(NotificationLog.created_at >= from_date)
    
    if to_date:
        query = query.filter(NotificationLog.created_at <= to_date)
    
    logs = query.order_by(NotificationLog.created_at.desc()).limit(limit).all()
    
    return [NotificationLogResponse.from_orm(log) for log in logs]


@router.post("/test", status_code=200)
def test_notification(
    test_data: TestNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send test notification email"""
    template = (
        db.query(NotificationTemplate)
        .filter(
            NotificationTemplate.template_code == test_data.template_code,
            NotificationTemplate.enabled == True
        )
        .first()
    )
    
    if not template:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail=f"Template {test_data.template_code} not found"
        )
    
    # Render with test data
    from app.services.notification_service import NotificationService
    context = {
        'user_name': 'Test User',
        'asset_name': 'Test Asset',
        'site_name': 'Test Site',
        'last_review_date': '2025-01-01',
        'days_until_review': 30,
        'days_overdue': 0,
        'risk_score': 8.5,
        'risk_level': 'high',
        'asset_url': '/assets/test-id'
    }
    
    rendered = NotificationService.render_template(template, context)
    
    # Send test email
    from app.models import TenantSMTPConfig
    from app.services.email_service import EmailConfig, EmailProvider, send_email
    
    smtp_config = (
        db.query(TenantSMTPConfig)
        .filter(TenantSMTPConfig.tenant_id == current_user.tenant_id)
        .first()
    )
    
    if not smtp_config or not smtp_config.host:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="SMTP configuration not found"
        )
    
    email_config = EmailConfig(
        provider=EmailProvider.SMTP,
        smtp_host=smtp_config.host,
        smtp_port=smtp_config.port,
        smtp_username=smtp_config.username,
        smtp_password=smtp_config.password,
        smtp_use_tls=smtp_config.use_tls,
        from_email=smtp_config.from_email
    )
    
    success = send_email(
        test_data.email,
        rendered['subject'],
        rendered['body_text'] or '',
        email_config,
        rendered['body_html']
    )
    
    if success:
        return {"message": "Test email sent successfully", "email": test_data.email}
    else:
        raise ErrorCodeException(
            status_code=500,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="Failed to send test email"
        )


@router.post("/queue/process", status_code=200)
def process_notification_queue(
    batch_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually trigger notification queue processing (admin)"""
    stats = EmailQueueProcessor.process_queue(db, batch_size)
    
    return {
        "message": "Queue processed",
        "stats": stats
    }

