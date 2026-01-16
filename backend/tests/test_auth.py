import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models.user import User
from app.models.tenant import Tenant
from app.models.role import Role
from app.services.auth import get_password_hash
import uuid
import os

# Test database - use PostgreSQL for consistency
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_tenant():
    db = TestingSessionLocal()
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Test Tenant",
        slug="test-tenant"
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    db.close()
    return tenant

@pytest.fixture
def test_role(test_tenant):
    db = TestingSessionLocal()
    role = Role(
        id=uuid.uuid4(),
        name="Admin",
        tenant_id=test_tenant.id,
        permissions={"assets": 3, "users": 3}
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    db.close()
    return role

@pytest.fixture
def test_user(test_tenant, test_role):
    db = TestingSessionLocal()
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=get_password_hash("testpassword"),
        name="Test User",
        tenant_id=test_tenant.id,
        role_id=test_role.id,
        password_change_required=False  # Set to False for tests to allow login
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

client = TestClient(app)

def test_login_success(test_user):
    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_login_invalid_credentials():
    response = client.post("/login", data={
        "email": "wrong@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_protected_endpoint_without_token():
    response = client.get("/users/me")
    assert response.status_code == 401

def test_protected_endpoint_with_valid_token(test_user):
    # Login to get token
    login_response = client.post("/login", data={
        "email": "test@example.com",
        "password": "testpassword"
    })
    token = login_response.json()["access_token"]
    
    # Use token to access protected endpoint
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200 