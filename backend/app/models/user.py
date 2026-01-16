# backend/models/user.py
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # ⬅️ Diventa nullable per SSO-only users
    name = Column(String(255), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Notification preferences
    notifications_enabled = Column(Boolean, default=True)  # Global setting to enable/disable all notifications
    
    # SSO fields
    auth_provider = Column(String(50), nullable=True, index=True)  # 'local', 'azure_ad', 'google', 'okta'
    external_id = Column(String(255), nullable=True, index=True)  # ID utente nel provider esterno
    sso_email = Column(String(255), nullable=True)  # Email dal provider (può differire)
    last_sso_login = Column(DateTime, nullable=True)
    sso_metadata = Column(JSONB, nullable=True)  # Dati aggiuntivi dal provider
    
    # Account lockout fields
    failed_login_attempts = Column(Integer, default=0)  # Number of consecutive failed login attempts
    locked_until = Column(DateTime, nullable=True)  # Timestamp when account lockout expires
    
    # Password change required flag
    password_change_required = Column(Boolean, default=False)  # Force password change on next login
    
    role = relationship("Role", back_populates="users", lazy="joined")
    tenant = relationship("Tenant", lazy="joined")