"""API integration tests for RBAC on core routers."""
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import Tenant, Role, User, Site
from app.models.audit_log import AuditLog
from app.routers import sites
from app.services.auth import get_current_user
from app.services.rbac_permissions import VIEWER_DEFAULT_PERMISSIONS, ADMIN_DEFAULT_PERMISSIONS


def _sqlite_jsonb_compat(tables):
    for table in tables:
        for column in table.columns:
            if isinstance(column.type, JSONB):
                from sqlalchemy import JSON

                column.type = JSON()


@pytest.fixture
def api_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [Tenant.__table__, Role.__table__, User.__table__, Site.__table__, AuditLog.__table__]
    _sqlite_jsonb_compat(tables)
    Base.metadata.create_all(bind=engine, tables=tables)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine, tables=tables)


def _build_client(db_session, permissions):
    tenant_id = uuid.uuid4()
    role_id = uuid.uuid4()
    user_id = uuid.uuid4()

    tenant = Tenant(id=tenant_id, name="Test Tenant", slug=f"tenant-{tenant_id.hex[:8]}")
    role = Role(
        id=role_id,
        tenant_id=tenant_id,
        name="test-role",
        permissions=permissions,
    )
    user = User(
        id=user_id,
        tenant_id=tenant_id,
        email=f"user-{user_id.hex[:8]}@test.com",
        password_hash="hash",
        name="Test User",
        role_id=role_id,
        is_active=True,
    )
    db_session.add_all([tenant, role, user])
    db_session.commit()
    db_session.refresh(user)

    app = FastAPI()
    app.include_router(sites.router)

    def override_db():
        yield db_session

    def override_user():
        return user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    return TestClient(app)


def test_viewer_can_list_sites(api_db):
    client = _build_client(api_db, VIEWER_DEFAULT_PERMISSIONS)
    response = client.get("/sites")
    assert response.status_code == 200


def test_viewer_cannot_create_site(api_db):
    client = _build_client(api_db, VIEWER_DEFAULT_PERMISSIONS)
    response = client.post(
        "/sites",
        json={"name": "Plant A", "code": "PLT-A"},
    )
    assert response.status_code == 403


def test_admin_can_create_site(api_db):
    client = _build_client(api_db, ADMIN_DEFAULT_PERMISSIONS)
    response = client.post(
        "/sites",
        json={"name": "Plant B", "code": "PLT-B"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Plant B"
