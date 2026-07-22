"""Integration-style MFA login / policy / reset tests (SQLite)."""
import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pyotp
import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.services.sso_encryption as sso_encryption
from app.config import settings
from app.database import Base, get_db
from app.models import Tenant, Role, User
from app.models.user_backup_code import UserBackupCode
from app.models.audit_log import AuditLog
from app.routers import mfa as mfa_router
from app.services.auth import (
    get_password_hash,
    create_mfa_pending_token,
    get_current_user,
)
from app.services import mfa as mfa_service
from app.services.rbac_permissions import ADMIN_DEFAULT_PERMISSIONS


@pytest.fixture
def encryption_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", key)
    monkeypatch.setattr(sso_encryption, "_fernet", None)
    return key


def _sqlite_jsonb_compat(tables):
    for table in tables:
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()


@pytest.fixture
def mfa_db(encryption_key):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        Tenant.__table__,
        Role.__table__,
        User.__table__,
        UserBackupCode.__table__,
        AuditLog.__table__,
    ]
    _sqlite_jsonb_compat(tables)
    Base.metadata.create_all(bind=engine, tables=tables)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine, tables=tables)


def _seed_user(db, *, totp_enabled=False, role_name="admin", tenant_settings=None):
    tenant_id = uuid.uuid4()
    role_id = uuid.uuid4()
    user_id = uuid.uuid4()
    tenant = Tenant(
        id=tenant_id,
        name="MFA Tenant",
        slug=f"mfa-{tenant_id.hex[:8]}",
        settings=tenant_settings or {},
    )
    role = Role(
        id=role_id,
        tenant_id=tenant_id,
        name=role_name,
        permissions=ADMIN_DEFAULT_PERMISSIONS,
    )
    secret = mfa_service.generate_totp_secret()
    user = User(
        id=user_id,
        tenant_id=tenant_id,
        email=f"mfa-{user_id.hex[:8]}@test.com",
        password_hash=get_password_hash("Password123!@#"),
        name="MFA User",
        role_id=role_id,
        is_active=True,
        totp_enabled=totp_enabled,
        totp_secret_encrypted=mfa_service.encrypt_totp_secret(secret) if totp_enabled else None,
        totp_verified_at=datetime.utcnow() if totp_enabled else None,
    )
    db.add_all([tenant, role, user])
    db.commit()
    db.refresh(user)
    db.refresh(tenant)
    return user, tenant, secret


def test_login_mfa_success_and_invalid(mfa_db, encryption_key, monkeypatch):
    monkeypatch.setattr(settings, "MFA_MAX_ATTEMPTS", 5)
    user, tenant, secret = _seed_user(mfa_db, totp_enabled=True)

    from app.main import app as full_app

    def override_db():
        yield mfa_db

    full_app.dependency_overrides[get_db] = override_db
    client = TestClient(full_app)

    # Password login should require MFA
    with patch("app.main.check_rate_limit_strict", return_value=True), patch(
        "app.main.add_rate_limit_headers_strict"
    ), patch("app.main.log_failed_login"), patch("app.main.log_successful_login"), patch(
        "app.main.log_mfa_event"
    ), patch("app.main.create_audit_log"):
        res = client.post(
            "/login",
            data={"email": user.email, "password": "Password123!@#"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body.get("mfa_required") is True
        assert "mfa_token" in body
        assert "access_token" not in body

        # Wrong code
        bad = client.post(
            "/login/mfa",
            json={"mfa_token": body["mfa_token"], "code": "000000"},
        )
        assert bad.status_code == 401

        # Good TOTP
        code = pyotp.TOTP(secret).now()
        ok = client.post(
            "/login/mfa",
            json={"mfa_token": body["mfa_token"], "code": code},
        )
        assert ok.status_code == 200
        assert "access_token" in ok.json()

    full_app.dependency_overrides.clear()


def test_mfa_lockout_after_failures(mfa_db, encryption_key, monkeypatch):
    monkeypatch.setattr(settings, "MFA_MAX_ATTEMPTS", 2)
    monkeypatch.setattr(settings, "MFA_LOCKOUT_MINUTES", 15)
    user, _, _ = _seed_user(mfa_db, totp_enabled=True)
    from app.main import app as full_app

    def override_db():
        yield mfa_db

    full_app.dependency_overrides[get_db] = override_db
    client = TestClient(full_app)
    token = create_mfa_pending_token(str(user.id), str(user.tenant_id))

    with patch("app.main.check_rate_limit_strict", return_value=True), patch(
        "app.main.add_rate_limit_headers_strict"
    ), patch("app.main.log_mfa_event"), patch("app.main.create_audit_log"):
        for _ in range(2):
            client.post("/login/mfa", json={"mfa_token": token, "code": "111111"})
        locked = client.post("/login/mfa", json={"mfa_token": token, "code": "111111"})
        assert locked.status_code == 403
        assert locked.json().get("error_code") == "MFA_LOCKED"

    full_app.dependency_overrides.clear()


def test_admin_reset_clears_mfa(mfa_db, encryption_key):
    user, tenant, _ = _seed_user(mfa_db, totp_enabled=True)
    mfa_service.generate_backup_codes(mfa_db, user.id, count=3)
    mfa_db.commit()

    app = FastAPI()
    app.include_router(mfa_router.router)

    def override_db():
        yield mfa_db

    def override_user():
        return user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    client = TestClient(app)

    with patch("app.routers.mfa.log_mfa_event"), patch(
        "app.routers.mfa.create_audit_log"
    ), patch("app.routers.mfa._notify_mfa_reset"):
        res = client.post(f"/users/{user.id}/mfa/reset")
        assert res.status_code == 200

    mfa_db.refresh(user)
    assert user.totp_enabled is False
    assert user.totp_secret_encrypted is None
    remaining = mfa_service.count_remaining_backup_codes(mfa_db, user.id)
    assert remaining == 0


def test_policy_setup_required_after_grace(mfa_db, encryption_key):
    past = (datetime.utcnow() - timedelta(days=10)).isoformat()
    user, tenant, _ = _seed_user(
        mfa_db,
        totp_enabled=False,
        role_name="admin",
        tenant_settings={
            "mfa_policy": "required_admins",
            "mfa_enrollment_deadline_days": 7,
            "mfa_policy_enforced_at": past,
        },
    )
    enf = mfa_service.check_mfa_policy(user, tenant)
    assert enf.requires_enrollment and enf.past_grace

    from app.main import app as full_app

    def override_db():
        yield mfa_db

    full_app.dependency_overrides[get_db] = override_db
    client = TestClient(full_app)
    with patch("app.main.check_rate_limit_strict", return_value=True), patch(
        "app.main.add_rate_limit_headers_strict"
    ), patch("app.main.log_failed_login"), patch("app.main.create_audit_log"):
        res = client.post(
            "/login",
            data={"email": user.email, "password": "Password123!@#"},
        )
        assert res.status_code == 403
        body = res.json()
        assert body.get("mfa_setup_required") is True
        assert body.get("mfa_setup_token")
    full_app.dependency_overrides.clear()


def test_sso_only_user_not_enforced():
    role = SimpleNamespace(name="admin")
    user = SimpleNamespace(password_hash=None, totp_enabled=False, role=role)
    tenant = SimpleNamespace(
        settings={
            "mfa_policy": "required_all",
            "mfa_enrollment_deadline_days": 0,
            "mfa_policy_enforced_at": datetime.utcnow().isoformat(),
        }
    )
    enf = mfa_service.check_mfa_policy(user, tenant)
    assert not enf.requires_enrollment
