# backend/app/services/mfa.py
"""TOTP MFA helpers: secrets, verification, backup codes, tenant policy."""
from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Tuple
from uuid import UUID

import pyotp
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.user_backup_code import UserBackupCode
from app.models.tenant import Tenant
from app.services.auth import get_password_hash, verify_password
from app.services.sso_encryption import encrypt_secret, decrypt_secret


class MfaPolicy(str, Enum):
    OPTIONAL = "optional"
    REQUIRED_ADMINS = "required_admins"
    REQUIRED_ALL = "required_all"


@dataclass
class MfaEnforcement:
    policy: MfaPolicy
    deadline_days: int
    enforced_at: Optional[datetime]
    requires_enrollment: bool
    past_grace: bool
    can_self_disable: bool


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def build_provisioning_uri(email: str, secret: str) -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=settings.MFA_ISSUER_NAME)


def encrypt_totp_secret(secret: str) -> str:
    return encrypt_secret(secret)


def decrypt_totp_secret(encrypted: str) -> str:
    return decrypt_secret(encrypted)


def verify_totp_code(secret: str, code: str, valid_window: int = 1) -> bool:
    if not secret or not code:
        return False
    cleaned = code.strip().replace(" ", "")
    if not cleaned.isdigit() or len(cleaned) != 6:
        return False
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(cleaned, valid_window=valid_window))


def verify_totp_for_user(user: User, code: str) -> bool:
    if not user.totp_secret_encrypted:
        return False
    secret = decrypt_totp_secret(user.totp_secret_encrypted)
    return verify_totp_code(secret, code)


def _format_backup_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    # Avoid ambiguous characters
    alphabet = alphabet.replace("O", "").replace("0", "").replace("I", "").replace("1", "")
    part1 = "".join(secrets.choice(alphabet) for _ in range(4))
    part2 = "".join(secrets.choice(alphabet) for _ in range(4))
    return f"{part1}-{part2}"


def generate_backup_codes(
    db: Session, user_id: UUID, count: Optional[int] = None
) -> List[str]:
    """Invalidate previous codes and create new ones. Returns plaintext once."""
    n = count if count is not None else settings.MFA_BACKUP_CODES_COUNT
    db.query(UserBackupCode).filter(UserBackupCode.user_id == user_id).delete(
        synchronize_session=False
    )
    plain_codes: List[str] = []
    for _ in range(n):
        code = _format_backup_code()
        plain_codes.append(code)
        db.add(
            UserBackupCode(
                user_id=user_id,
                code_hash=get_password_hash(code.replace("-", "").upper()),
            )
        )
    db.flush()
    return plain_codes


def _normalize_backup_input(code: str) -> str:
    return code.strip().replace("-", "").replace(" ", "").upper()


def verify_backup_code(db: Session, user_id: UUID, code: str) -> bool:
    normalized = _normalize_backup_input(code)
    if len(normalized) < 8:
        return False
    candidates = (
        db.query(UserBackupCode)
        .filter(
            UserBackupCode.user_id == user_id,
            UserBackupCode.used_at.is_(None),
        )
        .all()
    )
    for row in candidates:
        if verify_password(normalized, row.code_hash):
            row.used_at = datetime.utcnow()
            db.flush()
            return True
    return False


def count_remaining_backup_codes(db: Session, user_id: UUID) -> int:
    return (
        db.query(UserBackupCode)
        .filter(
            UserBackupCode.user_id == user_id,
            UserBackupCode.used_at.is_(None),
        )
        .count()
    )


def is_local_password_user(user: User) -> bool:
    return bool(user.password_hash)


def is_admin_user(user: User) -> bool:
    role = getattr(user, "role", None)
    if not role:
        return False
    name = (getattr(role, "name", "") or "").lower()
    return name == "admin"


def get_tenant_mfa_settings(tenant: Tenant) -> Tuple[MfaPolicy, int, Optional[datetime]]:
    raw = tenant.settings if isinstance(tenant.settings, dict) else {}
    policy_raw = (raw.get("mfa_policy") or MfaPolicy.OPTIONAL.value).lower()
    try:
        policy = MfaPolicy(policy_raw)
    except ValueError:
        policy = MfaPolicy.OPTIONAL
    try:
        deadline_days = int(raw.get("mfa_enrollment_deadline_days", 7))
    except (TypeError, ValueError):
        deadline_days = 7
    enforced_at = None
    enforced_raw = raw.get("mfa_policy_enforced_at")
    if enforced_raw:
        try:
            enforced_at = datetime.fromisoformat(str(enforced_raw).replace("Z", "+00:00"))
            if enforced_at.tzinfo is not None:
                enforced_at = enforced_at.replace(tzinfo=None)
        except ValueError:
            enforced_at = None
    return policy, deadline_days, enforced_at


def set_tenant_mfa_policy(
    tenant: Tenant,
    policy: MfaPolicy,
    deadline_days: int = 7,
) -> dict:
    settings_dict = dict(tenant.settings) if isinstance(tenant.settings, dict) else {}
    previous = (settings_dict.get("mfa_policy") or MfaPolicy.OPTIONAL.value).lower()
    settings_dict["mfa_policy"] = policy.value
    settings_dict["mfa_enrollment_deadline_days"] = max(0, int(deadline_days))
    if policy in (MfaPolicy.REQUIRED_ADMINS, MfaPolicy.REQUIRED_ALL):
        if previous != policy.value or not settings_dict.get("mfa_policy_enforced_at"):
            settings_dict["mfa_policy_enforced_at"] = datetime.utcnow().isoformat()
    else:
        settings_dict.pop("mfa_policy_enforced_at", None)
    tenant.settings = settings_dict
    return settings_dict


def check_mfa_policy(user: User, tenant: Tenant) -> MfaEnforcement:
    policy, deadline_days, enforced_at = get_tenant_mfa_settings(tenant)
    can_self_disable = policy == MfaPolicy.OPTIONAL

    if not is_local_password_user(user):
        return MfaEnforcement(
            policy=policy,
            deadline_days=deadline_days,
            enforced_at=enforced_at,
            requires_enrollment=False,
            past_grace=False,
            can_self_disable=can_self_disable,
        )

    if user.totp_enabled:
        return MfaEnforcement(
            policy=policy,
            deadline_days=deadline_days,
            enforced_at=enforced_at,
            requires_enrollment=False,
            past_grace=False,
            can_self_disable=can_self_disable,
        )

    requires = False
    if policy == MfaPolicy.REQUIRED_ALL:
        requires = True
    elif policy == MfaPolicy.REQUIRED_ADMINS and is_admin_user(user):
        requires = True

    past_grace = False
    if requires:
        start = enforced_at or datetime.utcnow()
        past_grace = datetime.utcnow() >= start + timedelta(days=deadline_days)

    return MfaEnforcement(
        policy=policy,
        deadline_days=deadline_days,
        enforced_at=enforced_at,
        requires_enrollment=requires,
        past_grace=past_grace,
        can_self_disable=can_self_disable,
    )


def is_mfa_locked(user: User) -> bool:
    return bool(user.mfa_locked_until and user.mfa_locked_until > datetime.utcnow())


def register_mfa_failure(user: User) -> None:
    user.failed_mfa_attempts = (user.failed_mfa_attempts or 0) + 1
    if user.failed_mfa_attempts >= settings.MFA_MAX_ATTEMPTS:
        user.mfa_locked_until = datetime.utcnow() + timedelta(
            minutes=settings.MFA_LOCKOUT_MINUTES
        )


def reset_mfa_failures(user: User) -> None:
    user.failed_mfa_attempts = 0
    user.mfa_locked_until = None


def clear_user_mfa(db: Session, user: User) -> None:
    user.totp_secret_encrypted = None
    user.totp_enabled = False
    user.totp_verified_at = None
    user.totp_enrolled_at = None
    reset_mfa_failures(user)
    db.query(UserBackupCode).filter(UserBackupCode.user_id == user.id).delete(
        synchronize_session=False
    )


def verify_mfa_code(db: Session, user: User, code: str) -> bool:
    """Verify TOTP or backup code. Marks backup code used on success."""
    cleaned = (code or "").strip()
    if verify_totp_for_user(user, cleaned):
        return True
    if verify_backup_code(db, user.id, cleaned):
        return True
    return False
