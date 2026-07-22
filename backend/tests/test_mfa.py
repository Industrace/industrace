"""Unit tests for MFA/TOTP service and tokens."""
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import pyotp
from cryptography.fernet import Fernet

import app.services.sso_encryption as sso_encryption
from app.config import settings
from app.services import mfa as mfa_service
from app.services.auth import (
    create_mfa_pending_token,
    create_mfa_setup_token,
    decode_typed_token,
    create_access_token,
)
from app.errors.exceptions import ErrorCodeException


@pytest.fixture
def encryption_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", key)
    monkeypatch.setattr(sso_encryption, "_fernet", None)
    return key


def test_totp_generate_and_verify(encryption_key):
    secret = mfa_service.generate_totp_secret()
    uri = mfa_service.build_provisioning_uri("user@example.com", secret)
    assert "otpauth://totp/" in uri
    assert "Industrace" in uri or settings.MFA_ISSUER_NAME in uri
    code = pyotp.TOTP(secret).now()
    assert mfa_service.verify_totp_code(secret, code)
    assert not mfa_service.verify_totp_code(secret, "000000")


def test_encrypt_decrypt_totp_secret(encryption_key):
    secret = mfa_service.generate_totp_secret()
    enc = mfa_service.encrypt_totp_secret(secret)
    assert enc != secret
    assert mfa_service.decrypt_totp_secret(enc) == secret


def test_mfa_pending_token_roundtrip():
    uid = str(uuid4())
    tid = str(uuid4())
    token = create_mfa_pending_token(uid, tid)
    payload = decode_typed_token(token, "mfa_pending")
    assert payload["sub"] == uid
    assert payload["tenant_id"] == tid
    assert payload["type"] == "mfa_pending"


def test_mfa_pending_token_rejects_access_type():
    uid = str(uuid4())
    tid = str(uuid4())
    access = create_access_token({"sub": uid, "tenant_id": tid})
    with pytest.raises(ErrorCodeException):
        decode_typed_token(access, "mfa_pending")


def test_mfa_setup_token_type():
    token = create_mfa_setup_token(str(uuid4()), str(uuid4()))
    payload = decode_typed_token(token, "mfa_setup")
    assert payload["type"] == "mfa_setup"


def test_backup_codes_generate_and_verify(encryption_key):
    db = MagicMock()
    stored = []

    def add(obj):
        stored.append(obj)

    db.add.side_effect = add
    db.query.return_value.filter.return_value.delete.return_value = None
    db.flush.return_value = None

    user_id = uuid4()
    codes = mfa_service.generate_backup_codes(db, user_id, count=3)
    assert len(codes) == 3
    assert all("-" in c for c in codes)
    assert len(stored) == 3

    # Simulate verify against stored hashes
    db.query.return_value.filter.return_value.all.return_value = stored
    assert mfa_service.verify_backup_code(db, user_id, codes[0])
    assert stored[0].used_at is not None


def test_policy_optional_no_enrollment():
    role = SimpleNamespace(name="admin")
    user = SimpleNamespace(password_hash="x", totp_enabled=False, role=role)
    tenant = SimpleNamespace(settings={})
    enf = mfa_service.check_mfa_policy(user, tenant)
    assert enf.policy == mfa_service.MfaPolicy.OPTIONAL
    assert not enf.requires_enrollment
    assert enf.can_self_disable


def test_policy_required_admins_past_grace():
    role = SimpleNamespace(name="admin")
    user = SimpleNamespace(password_hash="x", totp_enabled=False, role=role)
    past = (datetime.utcnow() - timedelta(days=10)).isoformat()
    tenant = SimpleNamespace(
        settings={
            "mfa_policy": "required_admins",
            "mfa_enrollment_deadline_days": 7,
            "mfa_policy_enforced_at": past,
        }
    )
    enf = mfa_service.check_mfa_policy(user, tenant)
    assert enf.requires_enrollment
    assert enf.past_grace
    assert not enf.can_self_disable


def test_policy_skips_sso_only_users():
    role = SimpleNamespace(name="admin")
    user = SimpleNamespace(password_hash=None, totp_enabled=False, role=role)
    tenant = SimpleNamespace(
        settings={"mfa_policy": "required_all", "mfa_enrollment_deadline_days": 0}
    )
    enf = mfa_service.check_mfa_policy(user, tenant)
    assert not enf.requires_enrollment


def test_register_mfa_failure_lockout(monkeypatch):
    monkeypatch.setattr(settings, "MFA_MAX_ATTEMPTS", 2)
    monkeypatch.setattr(settings, "MFA_LOCKOUT_MINUTES", 15)
    user = SimpleNamespace(failed_mfa_attempts=0, mfa_locked_until=None)
    mfa_service.register_mfa_failure(user)
    assert user.failed_mfa_attempts == 1
    assert not mfa_service.is_mfa_locked(user)
    mfa_service.register_mfa_failure(user)
    assert mfa_service.is_mfa_locked(user)


def test_set_tenant_mfa_policy_sets_enforced_at():
    tenant = SimpleNamespace(settings={})
    result = mfa_service.set_tenant_mfa_policy(
        tenant, mfa_service.MfaPolicy.REQUIRED_ALL, 7
    )
    assert result["mfa_policy"] == "required_all"
    assert "mfa_policy_enforced_at" in result
