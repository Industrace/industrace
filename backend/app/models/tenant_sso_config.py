# backend/app/models/tenant_sso_config.py
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class TenantSSOConfig(Base):
    """
    Tenant SSO Configuration: Configurazione OAuth2/OIDC per ogni tenant.
    Supporta Azure AD (EntraID), Google Workspace, Okta, e altri provider OIDC.
    """
    __tablename__ = "tenant_sso_config"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), primary_key=True)
    
    # Provider Info
    provider_type = Column(String(50), nullable=False)  # 'azure_ad', 'google', 'okta', 'generic_oidc'
    enabled = Column(Boolean, default=False, index=True)
    
    # OAuth2/OIDC Configuration
    client_id = Column(String(255), nullable=False)
    client_secret_encrypted = Column(String(500), nullable=False)  # Encrypted client secret
    tenant_domain = Column(String(255), nullable=True)  # Per Azure AD: tenant ID o domain
    authority_url = Column(String(500), nullable=True)  # OIDC discovery URL
    authorization_endpoint = Column(String(500), nullable=True)
    token_endpoint = Column(String(500), nullable=True)
    userinfo_endpoint = Column(String(500), nullable=True)
    jwks_uri = Column(String(500), nullable=True)  # JWKS endpoint per token verification
    
    # Scopes
    scopes = Column(JSONB, default=["openid", "profile", "email"])
    
    # Auto-provisioning
    auto_provision_enabled = Column(Boolean, default=True)
    default_role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)  # Role per nuovi utenti
    domain_restriction = Column(String(255), nullable=True)  # Solo utenti da questo dominio (es: "company.com")
    
    # Redirect URIs
    redirect_uri = Column(String(500), nullable=True)  # Callback URL
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_test_at = Column(DateTime, nullable=True)
    last_test_status = Column(String(20), nullable=True)  # 'success', 'failed'
    last_test_error = Column(Text, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="sso_config")
    default_role = relationship("Role", foreign_keys=[default_role_id])

