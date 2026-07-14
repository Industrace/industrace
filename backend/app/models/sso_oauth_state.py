import uuid
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class SsoOAuthState(Base):
    """Short-lived OAuth2/PKCE state shared across API workers."""

    __tablename__ = "sso_oauth_states"

    state = Column(String(128), primary_key=True)
    code_verifier = Column(String(256), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
