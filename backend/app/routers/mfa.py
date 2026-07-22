# backend/app/routers/mfa.py
"""MFA self-service and admin endpoints."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors.error_codes import ErrorCode
from app.errors.exceptions import ErrorCodeException
from app.models import User, Tenant, TenantSMTPConfig
from app.schemas.mfa import (
    MfaStatusResponse,
    MfaSetupResponse,
    MfaVerifySetupRequest,
    MfaDisableRequest,
    MfaRegenerateBackupRequest,
    BackupCodesResponse,
    MfaPolicyResponse,
    MfaPolicyUpdate,
    AdminMfaStatusResponse,
)
from app.services.auth import (
    get_current_user,
    get_current_user_or_mfa_setup,
    verify_password,
)
from app.services.rbac import require_permission
from app.services.audit_log import create_audit_log, resolve_audit_language
from app.services.security_logging import log_mfa_event
from app.services import mfa as mfa_service
from app.services.email_service import EmailConfig, EmailProvider, send_email
from app.config import settings as app_settings

router = APIRouter(tags=["mfa"])


def _user_tenant(db: Session, user: User) -> Tenant:
    tenant = user.tenant
    if tenant is None:
        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.TENANT_NOT_FOUND)
    return tenant


@router.get("/users/me/mfa/status", response_model=MfaStatusResponse)
def mfa_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_mfa_setup),
):
    tenant = _user_tenant(db, current_user)
    enforcement = mfa_service.check_mfa_policy(current_user, tenant)
    return MfaStatusResponse(
        totp_enabled=bool(current_user.totp_enabled),
        totp_verified_at=current_user.totp_verified_at,
        backup_codes_remaining=mfa_service.count_remaining_backup_codes(
            db, current_user.id
        ),
        policy=enforcement.policy.value,
        enrollment_deadline_days=enforcement.deadline_days,
        requires_enrollment=enforcement.requires_enrollment,
        past_grace=enforcement.past_grace,
        can_self_disable=enforcement.can_self_disable,
    )


@router.post("/users/me/mfa/setup", response_model=MfaSetupResponse)
def mfa_setup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_mfa_setup),
):
    if current_user.totp_enabled:
        raise ErrorCodeException(status_code=400, error_code=ErrorCode.MFA_ALREADY_ENABLED)
    if not mfa_service.is_local_password_user(current_user):
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.ACCESS_DENIED,
            detail="MFA enrollment is only available for local password users.",
        )

    secret = mfa_service.generate_totp_secret()
    current_user.totp_secret_encrypted = mfa_service.encrypt_totp_secret(secret)
    current_user.totp_enrolled_at = datetime.utcnow()
    current_user.totp_enabled = False
    current_user.totp_verified_at = None
    db.commit()

    return MfaSetupResponse(
        secret=secret,
        provisioning_uri=mfa_service.build_provisioning_uri(current_user.email, secret),
    )


@router.post("/users/me/mfa/verify-setup", response_model=BackupCodesResponse)
def mfa_verify_setup(
    body: MfaVerifySetupRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_mfa_setup),
):
    if current_user.totp_enabled:
        raise ErrorCodeException(status_code=400, error_code=ErrorCode.MFA_ALREADY_ENABLED)
    if not current_user.totp_secret_encrypted:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.MFA_NOT_ENABLED,
            detail="Call /users/me/mfa/setup first.",
        )

    if not mfa_service.verify_totp_for_user(current_user, body.code):
        raise ErrorCodeException(status_code=400, error_code=ErrorCode.MFA_INVALID_CODE)

    current_user.totp_enabled = True
    current_user.totp_verified_at = datetime.utcnow()
    codes = mfa_service.generate_backup_codes(db, current_user.id)
    db.commit()

    log_mfa_event(
        "MFA_ENABLED",
        f"MFA enabled for {current_user.email}",
        request=request,
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
    )
    create_audit_log(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="mfa_enabled",
        entity="User",
        entity_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        commit=True,
        language=resolve_audit_language(current_user, request),
    )
    return BackupCodesResponse(backup_codes=codes)


@router.post("/users/me/mfa/disable")
def mfa_disable(
    body: MfaDisableRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant = _user_tenant(db, current_user)
    enforcement = mfa_service.check_mfa_policy(current_user, tenant)
    if not enforcement.can_self_disable:
        raise ErrorCodeException(
            status_code=403, error_code=ErrorCode.MFA_DISABLE_FORBIDDEN
        )
    if not current_user.totp_enabled:
        raise ErrorCodeException(status_code=400, error_code=ErrorCode.MFA_NOT_ENABLED)
    if not current_user.password_hash or not verify_password(
        body.password, current_user.password_hash
    ):
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.INVALID_CREDENTIALS)
    if not mfa_service.verify_mfa_code(db, current_user, body.code):
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.MFA_INVALID_CODE)

    mfa_service.clear_user_mfa(db, current_user)
    db.commit()

    log_mfa_event(
        "MFA_DISABLED",
        f"MFA disabled for {current_user.email}",
        request=request,
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
    )
    create_audit_log(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="mfa_disabled",
        entity="User",
        entity_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        commit=True,
        language=resolve_audit_language(current_user, request),
    )
    return {"message": "MFA disabled"}


@router.post("/users/me/mfa/backup-codes/regenerate", response_model=BackupCodesResponse)
def mfa_regenerate_backup_codes(
    body: MfaRegenerateBackupRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.totp_enabled:
        raise ErrorCodeException(status_code=400, error_code=ErrorCode.MFA_NOT_ENABLED)
    if not mfa_service.verify_totp_for_user(current_user, body.code):
        raise ErrorCodeException(status_code=401, error_code=ErrorCode.MFA_INVALID_CODE)

    codes = mfa_service.generate_backup_codes(db, current_user.id)
    db.commit()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="backup_codes_regenerated",
        entity="User",
        entity_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        commit=True,
        language=resolve_audit_language(current_user, request),
    )
    return BackupCodesResponse(backup_codes=codes)


@router.get(
    "/users/{user_id}/mfa/status",
    response_model=AdminMfaStatusResponse,
    dependencies=[Depends(require_permission("users", 1))],
)
def admin_mfa_status(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id,
            User.deleted_at.is_(None),
        )
        .first()
    )
    if not target:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.USER_NOT_FOUND)
    return AdminMfaStatusResponse(
        user_id=target.id,
        totp_enabled=bool(target.totp_enabled),
        totp_verified_at=target.totp_verified_at,
        backup_codes_remaining=mfa_service.count_remaining_backup_codes(db, target.id),
    )


@router.post(
    "/users/{user_id}/mfa/reset",
    dependencies=[Depends(require_permission("users", 2))],
)
def admin_mfa_reset(
    user_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id,
            User.deleted_at.is_(None),
        )
        .first()
    )
    if not target:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.USER_NOT_FOUND)

    mfa_service.clear_user_mfa(db, target)
    db.commit()

    log_mfa_event(
        "MFA_RESET",
        f"MFA reset for {target.email} by {current_user.email}",
        request=request,
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        additional_data={"target_user_id": str(target.id)},
        severity="WARNING",
    )
    create_audit_log(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="mfa_reset",
        entity="User",
        entity_id=target.id,
        ip_address=request.client.host if request.client else None,
        commit=True,
        language=resolve_audit_language(current_user, request),
    )

    _notify_mfa_reset(db, target)

    return {"message": "MFA reset", "user_id": str(target.id)}


@router.get(
    "/tenants/mfa-policy",
    response_model=MfaPolicyResponse,
    dependencies=[Depends(require_permission("sso", 1))],
)
def get_mfa_policy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant = _user_tenant(db, current_user)
    policy, deadline, enforced_at = mfa_service.get_tenant_mfa_settings(tenant)
    return MfaPolicyResponse(
        mfa_policy=policy.value,
        mfa_enrollment_deadline_days=deadline,
        mfa_policy_enforced_at=enforced_at.isoformat() if enforced_at else None,
    )


@router.put(
    "/tenants/mfa-policy",
    response_model=MfaPolicyResponse,
    dependencies=[Depends(require_permission("sso", 2))],
)
def update_mfa_policy(
    body: MfaPolicyUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant = _user_tenant(db, current_user)
    policy = mfa_service.MfaPolicy(body.mfa_policy)
    settings_dict = mfa_service.set_tenant_mfa_policy(
        tenant, policy, body.mfa_enrollment_deadline_days
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="mfa_policy_updated",
        entity="Tenant",
        entity_id=tenant.id,
        ip_address=request.client.host if request.client else None,
        commit=True,
        language=resolve_audit_language(current_user, request),
    )

    enforced = settings_dict.get("mfa_policy_enforced_at")
    return MfaPolicyResponse(
        mfa_policy=settings_dict["mfa_policy"],
        mfa_enrollment_deadline_days=settings_dict["mfa_enrollment_deadline_days"],
        mfa_policy_enforced_at=enforced,
    )


def _notify_mfa_reset(db: Session, target: User) -> None:
    """Best-effort email when SMTP is configured for the tenant."""
    try:
        smtp = (
            db.query(TenantSMTPConfig)
            .filter(TenantSMTPConfig.tenant_id == target.tenant_id)
            .first()
        )
        if not smtp or not smtp.from_email:
            return
        config = EmailConfig(
            provider=EmailProvider(smtp.provider or "smtp"),
            api_key=smtp.api_key,
            domain=smtp.domain,
            region=smtp.region,
            from_email=smtp.from_email,
            credentials=smtp.credentials,
            smtp_host=smtp.host,
            smtp_port=smtp.port,
            smtp_username=smtp.username,
            smtp_password=smtp.password,
            smtp_use_tls=bool(smtp.use_tls),
        )
        send_email(
            to_email=target.email,
            subject="Industrace MFA reset",
            content=(
                "An administrator has reset multi-factor authentication on your Industrace account. "
                "If you did not expect this, contact your administrator immediately."
            ),
            config=config,
        )
    except Exception:
        # Never fail the reset because of email issues
        pass
