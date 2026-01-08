# backend/app/routers/notifications.py
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import User, NotificationPreference, NotificationQueue, NotificationLog, NotificationTemplate
from app.services.auth import get_current_user
from app.services.audit_decorator import audit_log_action
from app.services.rbac import require_permission
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
    perm=Depends(require_permission("notifications", 1)),
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
    
    # Group templates by template_code and prioritize tenant-specific overrides
    template_map = {}
    for t in templates:
        key = t.template_code
        # If we already have this template_code, prefer tenant-specific override
        if key in template_map:
            # Keep tenant-specific if current is tenant-specific, otherwise replace with tenant-specific
            if t.tenant_id == current_user.tenant_id:
                template_map[key] = t
            # If current in map is system-wide and we have tenant-specific, replace
            elif template_map[key].tenant_id is None and t.tenant_id == current_user.tenant_id:
                template_map[key] = t
        else:
            template_map[key] = t
    
    return [
        {
            "template_code": t.template_code,
            "name": t.name,
            "description": t.description,
            "tenant_id": str(t.tenant_id) if t.tenant_id else None
        }
        for t in template_map.values()
    ]


@router.get("/templates/{template_code}", response_model=dict)
def get_notification_template(
    template_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("notifications", 1)),
):
    """Get notification template details - prioritizes tenant-specific override if exists"""
    # First try to get tenant-specific override
    template = (
        db.query(NotificationTemplate)
        .filter(
            NotificationTemplate.template_code == template_code,
            NotificationTemplate.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    # If no tenant-specific override, get system-wide template
    if not template:
        template = (
            db.query(NotificationTemplate)
            .filter(
                NotificationTemplate.template_code == template_code,
                NotificationTemplate.tenant_id.is_(None)
            )
            .first()
        )
    
    if not template:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail=f"Template {template_code} not found"
        )
    
    return {
        "id": str(template.id),
        "template_code": template.template_code,
        "name": template.name,
        "description": template.description,
        "subject_template": template.subject_template,
        "body_template_html": template.body_template_html,
        "body_template_text": template.body_template_text,
        "variables": template.variables or [],
        "enabled": template.enabled,
        "tenant_id": str(template.tenant_id) if template.tenant_id else None,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None
    }


@router.post("/templates/{template_code}/override", response_model=dict)
def create_template_override(
    template_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("notifications", 3)),
):
    """Create a tenant-specific override of a system-wide template"""
    # Check if override already exists - if so, return it
    existing_override = (
        db.query(NotificationTemplate)
        .filter(
            NotificationTemplate.template_code == template_code,
            NotificationTemplate.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    if existing_override:
        # Return existing override instead of error
        return {
            "id": str(existing_override.id),
            "template_code": existing_override.template_code,
            "name": existing_override.name,
            "description": existing_override.description,
            "subject_template": existing_override.subject_template,
            "body_template_html": existing_override.body_template_html,
            "body_template_text": existing_override.body_template_text,
            "variables": existing_override.variables or [],
            "enabled": existing_override.enabled,
            "tenant_id": str(existing_override.tenant_id) if existing_override.tenant_id else None,
            "created_at": existing_override.created_at.isoformat() if existing_override.created_at else None,
            "updated_at": existing_override.updated_at.isoformat() if existing_override.updated_at else None
        }
    
    # Find system-wide template
    # Note: Due to unique constraint on template_code, we need to check if there's ANY template with this code
    # and if it's system-wide (tenant_id is None)
    system_template = (
        db.query(NotificationTemplate)
        .filter(
            NotificationTemplate.template_code == template_code,
            NotificationTemplate.tenant_id.is_(None)
        )
        .first()
    )
    
    if not system_template:
        # Check if template exists but is tenant-specific (might be from another tenant)
        any_template = (
            db.query(NotificationTemplate)
            .filter(NotificationTemplate.template_code == template_code)
            .first()
        )
        if any_template:
            raise ErrorCodeException(
                status_code=400,
                error_code=ErrorCode.ASSET_NOT_FOUND,
                detail=f"Template {template_code} exists but is not a system template. Cannot create override."
            )
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail=f"System template {template_code} not found"
        )
    
    # Create tenant-specific override
    # Add "(Override)" suffix to name to indicate it's a tenant-specific override
    override_name = f"{system_template.name} (Override)"
    
    try:
        template = NotificationTemplate(
            tenant_id=current_user.tenant_id,
            template_code=system_template.template_code,
            name=override_name,
            description=system_template.description,
            subject_template=system_template.subject_template,
            body_template_html=system_template.body_template_html,
            body_template_text=system_template.body_template_text,
            variables=system_template.variables,
            enabled=system_template.enabled
        )
        db.add(template)
        db.commit()
        db.refresh(template)
    except Exception as e:
        db.rollback()
        # If it's a unique constraint violation, check if override was created by another request
        if "already exists" in str(e).lower() or "unique" in str(e).lower():
            # Try to fetch the override that might have been created
            existing_override = (
                db.query(NotificationTemplate)
                .filter(
                    NotificationTemplate.template_code == template_code,
                    NotificationTemplate.tenant_id == current_user.tenant_id
                )
                .first()
            )
            if existing_override:
                return {
                    "id": str(existing_override.id),
                    "template_code": existing_override.template_code,
                    "name": existing_override.name,
                    "description": existing_override.description,
                    "subject_template": existing_override.subject_template,
                    "body_template_html": existing_override.body_template_html,
                    "body_template_text": existing_override.body_template_text,
                    "variables": existing_override.variables or [],
                    "enabled": existing_override.enabled,
                    "tenant_id": str(existing_override.tenant_id) if existing_override.tenant_id else None,
                    "created_at": existing_override.created_at.isoformat() if existing_override.created_at else None,
                    "updated_at": existing_override.updated_at.isoformat() if existing_override.updated_at else None
                }
        raise ErrorCodeException(
            status_code=500,
            error_code=ErrorCode.INTERNAL_ERROR,
            detail=f"Failed to create override: {str(e)}"
        )
    
    return {
        "id": str(template.id),
        "template_code": template.template_code,
        "name": template.name,
        "description": template.description,
        "subject_template": template.subject_template,
        "body_template_html": template.body_template_html,
        "body_template_text": template.body_template_text,
        "variables": template.variables or [],
        "enabled": template.enabled,
        "tenant_id": str(template.tenant_id) if template.tenant_id else None,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None
    }


@router.delete("/templates/{template_code}/override", status_code=204)
def delete_template_override(
    template_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("notifications", 3)),
):
    """Delete a tenant-specific template override (only tenant-specific templates can be deleted)"""
    # Find tenant-specific override
    template = (
        db.query(NotificationTemplate)
        .filter(
            NotificationTemplate.template_code == template_code,
            NotificationTemplate.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    if not template:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail=f"Tenant-specific override for template {template_code} not found"
        )
    
    # Only allow deletion of tenant-specific templates (not system-wide)
    if template.tenant_id is None:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="Cannot delete system-wide templates. Only tenant-specific overrides can be deleted."
        )
    
    db.delete(template)
    db.commit()
    
    return None


@router.put("/templates/{template_code}", response_model=dict)
def update_notification_template(
    template_code: str,
    template_data: dict = Body(...),  # Accept dict as JSON body
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("notifications", 3)),
):
    """Update notification template (only tenant-specific templates can be updated)"""
    template = (
        db.query(NotificationTemplate)
        .filter(
            NotificationTemplate.template_code == template_code,
            # Only allow updating tenant-specific templates
            NotificationTemplate.tenant_id == current_user.tenant_id
        )
        .first()
    )
    
    if not template:
        # Try to find system-wide template to create tenant override
        system_template = (
            db.query(NotificationTemplate)
            .filter(
                NotificationTemplate.template_code == template_code,
                NotificationTemplate.tenant_id.is_(None)
            )
            .first()
        )
        
        if not system_template:
            raise ErrorCodeException(
                status_code=404,
                error_code=ErrorCode.ASSET_NOT_FOUND,
                detail=f"Template {template_code} not found"
            )
        
        # Create tenant-specific override
        from app.schemas.notification_template import NotificationTemplateCreate
        template = NotificationTemplate(
            tenant_id=current_user.tenant_id,
            template_code=system_template.template_code,
            name=system_template.name,
            description=system_template.description,
            subject_template=system_template.subject_template,
            body_template_html=system_template.body_template_html,
            body_template_text=system_template.body_template_text,
            variables=system_template.variables,
            enabled=system_template.enabled
        )
        db.add(template)
    
    # Update fields
    update_fields = ['name', 'description', 'subject_template', 'body_template_html', 
                     'body_template_text', 'variables', 'enabled']
    for field in update_fields:
        if field in template_data:
            setattr(template, field, template_data[field])
    
    from datetime import datetime
    template.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(template)
    
    return {
        "id": str(template.id),
        "template_code": template.template_code,
        "name": template.name,
        "description": template.description,
        "subject_template": template.subject_template,
        "body_template_html": template.body_template_html,
        "body_template_text": template.body_template_text,
        "variables": template.variables or [],
        "enabled": template.enabled,
        "tenant_id": str(template.tenant_id) if template.tenant_id else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None
    }


@router.get("/preferences", response_model=List[NotificationPreferenceResponse])
def list_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("notifications", 1)),
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
    perm=Depends(require_permission("notifications", 2)),
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
    perm=Depends(require_permission("notifications", 2)),
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
    perm=Depends(require_permission("notifications", 2)),
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
    perm=Depends(require_permission("notifications", 3)),
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
    perm=Depends(require_permission("notifications", 3)),
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
    perm=Depends(require_permission("notifications", 3)),
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
    perm=Depends(require_permission("notifications", 1)),
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
    perm=Depends(require_permission("notifications", 2)),
):
    """Send test notification email - prioritizes tenant-specific override if exists"""
    # First try to get tenant-specific override
    template = (
        db.query(NotificationTemplate)
        .filter(
            NotificationTemplate.template_code == test_data.template_code,
            NotificationTemplate.tenant_id == current_user.tenant_id,
            NotificationTemplate.enabled == True
        )
        .first()
    )
    
    # If no tenant-specific override, get system-wide template
    if not template:
        template = (
            db.query(NotificationTemplate)
            .filter(
                NotificationTemplate.template_code == test_data.template_code,
                NotificationTemplate.tenant_id.is_(None),
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
    
    # Create log entry for test notification
    from datetime import datetime
    log_entry = NotificationLog(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        notification_type=test_data.template_code,
        status='sent' if success else 'failed',
        sent_at=datetime.utcnow() if success else None,
        error_message=None if success else "Failed to send test email",
        context_data=context
    )
    db.add(log_entry)
    db.commit()
    
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
    perm=Depends(require_permission("notifications", 3)),
):
    """Manually trigger notification queue processing (admin)"""
    stats = EmailQueueProcessor.process_queue(db, batch_size)
    
    return {
        "message": "Queue processed",
        "stats": stats
    }


@router.post("/check-reviews", status_code=200)
def check_asset_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("notifications", 3)),
):
    """Manually trigger asset review check and send notifications (admin)"""
    from app.services.background_tasks import check_asset_reviews_manual
    
    # Check reviews for current tenant only
    results = check_asset_reviews_manual(tenant_id=current_user.tenant_id)
    
    return {
        "message": "Asset reviews checked",
        "results": results
    }

