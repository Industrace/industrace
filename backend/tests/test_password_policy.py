"""
Tests for password policy and password change required functionality
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models.user import User
from app.models.tenant import Tenant
from app.models.role import Role
from app.services.auth import get_password_hash, verify_password
from app.schemas.validators import validate_password_strength
from app.errors.validation_errors import InvalidPasswordError
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
def admin_role(test_tenant):
    db = TestingSessionLocal()
    role = Role(
        id=uuid.uuid4(),
        name="Admin",
        tenant_id=test_tenant.id,
        permissions={
            "assets": 3, 
            "users": 3, 
            "roles": 3,
            "reset_user_password": 1
        }
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    db.close()
    return role

@pytest.fixture
def user_with_password_change_required(test_tenant, admin_role):
    """User with password_change_required=True (default account)"""
    db = TestingSessionLocal()
    user = User(
        id=uuid.uuid4(),
        email="default@test.com",
        password_hash=get_password_hash("admin123"),  # Weak password
        name="Default User",
        tenant_id=test_tenant.id,
        role_id=admin_role.id,
        is_active=True,
        password_change_required=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture
def user_without_password_change_required(test_tenant, admin_role):
    """User with password_change_required=False (normal account)"""
    db = TestingSessionLocal()
    user = User(
        id=uuid.uuid4(),
        email="normal@test.com",
        password_hash=get_password_hash("StrongPassword123!"),  # Strong password
        name="Normal User",
        tenant_id=test_tenant.id,
        role_id=admin_role.id,
        is_active=True,
        password_change_required=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

client = TestClient(app)


class TestPasswordChangeRequired:
    """Tests for password change required functionality"""
    
    def test_login_with_password_change_required_fails(self, user_with_password_change_required):
        """Login should fail when password_change_required=True"""
        response = client.post("/login", data={
            "email": "default@test.com",
            "password": "admin123"
        })
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "PASSWORD_CHANGE_REQUIRED"
        assert "Password change required" in data["detail"]
    
    def test_login_without_password_change_required_succeeds(self, user_without_password_change_required):
        """Login should succeed when password_change_required=False"""
        response = client.post("/login", data={
            "email": "normal@test.com",
            "password": "StrongPassword123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_change_password_resets_flag(self, user_with_password_change_required):
        """Changing password should reset password_change_required flag"""
        # First, we need to bypass the password_change_required check
        # by directly updating the user in the database
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "default@test.com").first()
        
        # Verify password is correct
        assert verify_password("admin123", user.password_hash)
        
        # Change password via API (we'll need to temporarily set password_change_required=False)
        # Actually, we can't login to change password if password_change_required=True
        # So we'll test the endpoint directly by temporarily setting the flag
        user.password_change_required = False
        db.commit()
        db.close()
        
        # Now login and change password
        login_response = client.post("/login", data={
            "email": "default@test.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Set password_change_required back to True to test the change
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "default@test.com").first()
        user.password_change_required = True
        db.commit()
        db.close()
        
        # Change password
        new_password = "NewStrongPassword123!"
        response = client.post("/reset-password", 
                              json={
                                  "current_password": "admin123",
                                  "new_password": new_password
                              },
                              headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        
        # Verify password_change_required is reset
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "default@test.com").first()
        assert user.password_change_required == False
        assert verify_password(new_password, user.password_hash)
        db.close()
    
    def test_change_password_validates_strength(self, user_without_password_change_required):
        """Changing password should validate password strength"""
        # Login
        login_response = client.post("/login", data={
            "email": "normal@test.com",
            "password": "StrongPassword123!"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Try to change to weak password
        weak_passwords = [
            "short",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoNumbers!",  # No numbers
            "NoSpecialChars123",  # No special characters
        ]
        
        for weak_password in weak_passwords:
            response = client.post("/reset-password", 
                                  json={
                                      "current_password": "StrongPassword123!",
                                      "new_password": weak_password
                                  },
                                  headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 422, f"Weak password '{weak_password}' should be rejected"
        
        # Change to strong password should succeed
        response = client.post("/reset-password", 
                              json={
                                  "current_password": "StrongPassword123!",
                                  "new_password": "AnotherStrongPassword456@"
                              },
                              headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200


class TestPasswordStrengthValidation:
    """Tests for password strength validation"""
    
    def test_validate_password_strength_weak_passwords(self):
        """Test that weak passwords are rejected"""
        weak_passwords = [
            "short",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoNumbers!",  # No numbers
            "NoSpecialChars123",  # No special characters
        ]
        
        for weak_password in weak_passwords:
            with pytest.raises(InvalidPasswordError):
                validate_password_strength(weak_password, allow_weak=False)
    
    def test_validate_password_strength_strong_passwords(self):
        """Test that strong passwords are accepted"""
        strong_passwords = [
            "StrongPassword123!",
            "AnotherStrong456@",
            "MySecurePass789#",
            "ComplexP@ssw0rd!",
        ]
        
        for strong_password in strong_passwords:
            # Should not raise exception
            validate_password_strength(strong_password, allow_weak=False)
    
    def test_validate_password_strength_allow_weak(self):
        """Test that allow_weak=True bypasses validation"""
        weak_passwords = [
            "admin123",
            "short",
            "weak",
        ]
        
        for weak_password in weak_passwords:
            # Should not raise exception when allow_weak=True
            validate_password_strength(weak_password, allow_weak=True)


class TestAccountLockout:
    """Tests for account lockout functionality"""
    
    def test_account_lockout_after_failed_attempts(self, test_tenant, admin_role):
        """Account should be locked after max failed login attempts"""
        db = TestingSessionLocal()
        user = User(
            id=uuid.uuid4(),
            email="lockout@test.com",
            password_hash=get_password_hash("CorrectPassword123!"),
            name="Lockout User",
            tenant_id=test_tenant.id,
            role_id=admin_role.id,
            is_active=True,
            password_change_required=False,
            failed_login_attempts=0
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()
        
        # Make max failed attempts
        from app.config import settings
        max_attempts = settings.MAX_LOGIN_ATTEMPTS
        
        for i in range(max_attempts):
            response = client.post("/login", data={
                "email": "lockout@test.com",
                "password": "wrongpassword"
            })
            assert response.status_code == 401
        
        # Next attempt should lock the account
        response = client.post("/login", data={
            "email": "lockout@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "ACCOUNT_LOCKED"
        
        # Verify account is locked
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "lockout@test.com").first()
        assert user.locked_until is not None
        assert user.failed_login_attempts >= max_attempts
        db.close()
    
    def test_successful_login_resets_failed_attempts(self, user_without_password_change_required):
        """Successful login should reset failed login attempts"""
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "normal@test.com").first()
        user.failed_login_attempts = 3
        user.locked_until = None
        db.commit()
        db.close()
        
        # Successful login
        response = client.post("/login", data={
            "email": "normal@test.com",
            "password": "StrongPassword123!"
        })
        assert response.status_code == 200
        
        # Verify failed attempts are reset
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "normal@test.com").first()
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
        db.close()
