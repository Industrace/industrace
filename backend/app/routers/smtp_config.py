import uuid
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import TenantSMTPConfig, Tenant, User
from app.schemas.tenant_smtp_config import (
    TenantSMTPConfigRead,
    TenantSMTPConfigCreate,
    TenantSMTPConfigUpdate,
)
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.services.email_service import EmailConfig, EmailProvider, send_email
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from pydantic import EmailStr

router = APIRouter(
    prefix="/smtp-config",
    tags=["smtp-config"],
    dependencies=[Depends(require_section_access("notifications"))],
)


def _sanitize_smtp_config(config: TenantSMTPConfig) -> TenantSMTPConfigRead:
    payload = TenantSMTPConfigRead.model_validate(config).model_dump()
    if payload.get("password"):
        payload["password"] = "********"
    return TenantSMTPConfigRead(**payload)


@router.get("", response_model=TenantSMTPConfigRead)
def get_smtp_config(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    config = (
        db.query(TenantSMTPConfig)
        .filter(TenantSMTPConfig.tenant_id == current_user.tenant_id)
        .first()
    )
    if not config:
        raise ErrorCodeException(
            status_code=404, error_code=ErrorCode.SMTP_CONFIG_NOT_FOUND
        )
    return _sanitize_smtp_config(config)


@router.post("", response_model=TenantSMTPConfigRead)
def set_smtp_config(
    config_in: TenantSMTPConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        config = (
            db.query(TenantSMTPConfig)
            .filter(TenantSMTPConfig.tenant_id == current_user.tenant_id)
            .first()
        )
        
        config_data = config_in.model_dump(exclude_unset=True)
        
        if config:
            # Update existing config
            for field, value in config_data.items():
                if hasattr(config, field):
                    setattr(config, field, value)
        else:
            # Create new config
            config = TenantSMTPConfig(
                tenant_id=current_user.tenant_id,
                **config_data
            )
            db.add(config)
        
        db.commit()
        db.refresh(config)
        return _sanitize_smtp_config(config)
    except Exception as e:
        db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error saving SMTP config: {e}", exc_info=True)
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.SMTP_CONFIG_NOT_FOUND,
            detail=f"Error saving SMTP configuration: {str(e)}"
        )


@router.post("/test")
def test_smtp_config(
    config_data: TenantSMTPConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Test SMTP configuration.
    Accepts SMTP config data and sends a test email to the current user's email.
    """
    # Use provided config or get from database
    if config_data.host:
        # Use provided config
        email_config = EmailConfig(
            provider=EmailProvider(config_data.provider or "smtp"),
            smtp_host=config_data.host,
            smtp_port=config_data.port,
            smtp_username=config_data.username,
            smtp_password=config_data.password,
            smtp_use_tls=config_data.use_tls,
            from_email=config_data.from_email
        )
        test_email = current_user.email
    else:
        # Get from database
        config = (
            db.query(TenantSMTPConfig)
            .filter(TenantSMTPConfig.tenant_id == current_user.tenant_id)
            .first()
        )
        if not config:
            raise ErrorCodeException(
                status_code=404, error_code=ErrorCode.SMTP_CONFIG_NOT_FOUND,
                detail="No SMTP configuration found. Please save configuration first."
            )
        
        email_config = EmailConfig(
            provider=EmailProvider(config.provider or "smtp"),
            api_key=config.api_key,
            domain=config.domain,
            region=config.region,
            from_email=config.from_email,
            credentials=config.credentials,
            smtp_host=config.host,
            smtp_port=config.port,
            smtp_username=config.username,
            smtp_password=config.password,
            smtp_use_tls=config.use_tls
        )
        test_email = current_user.email
    
    try:
        success = send_email(
            test_email,
            "Test Email - Industrace",
            "This is a test email from Industrace notification system.",
            email_config
        )
        if success:
            return {"detail": "Test email sent successfully", "email": test_email}
        else:
            raise ErrorCodeException(
                status_code=400,
                error_code=ErrorCode.SMTP_SEND_ERROR,
                detail="Failed to send test email. Check SMTP configuration."
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"SMTP test error: {e}", exc_info=True)
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.SMTP_SEND_ERROR,
            detail=f"SMTP test failed: {str(e)}"
        )
