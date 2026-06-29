# backend/app/schemas/sso.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import uuid
from datetime import datetime


class TenantSSOConfigBase(BaseModel):
    """Base schema for TenantSSOConfig"""
    provider_type: str = Field(..., pattern="^(azure_ad|google|okta|generic_oidc)$")
    enabled: bool = False
    client_id: str
    client_secret: str  # Will be encrypted before storage
    tenant_domain: Optional[str] = None
    authority_url: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    scopes: List[str] = Field(default=["openid", "profile", "email"])
    auto_provision_enabled: bool = True
    default_role_id: Optional[uuid.UUID] = None
    domain_restriction: Optional[str] = None
    redirect_uri: Optional[str] = None


class TenantSSOConfigCreate(TenantSSOConfigBase):
    """Schema for creating a new TenantSSOConfig"""
    pass


class TenantSSOConfigUpdate(BaseModel):
    """Schema for updating a TenantSSOConfig"""
    enabled: Optional[bool] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_domain: Optional[str] = None
    authority_url: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    scopes: Optional[List[str]] = None
    auto_provision_enabled: Optional[bool] = None
    default_role_id: Optional[uuid.UUID] = None
    domain_restriction: Optional[str] = None
    redirect_uri: Optional[str] = None


class TenantSSOConfigRead(BaseModel):
    """Schema for reading a TenantSSOConfig (without client_secret)"""
    tenant_id: uuid.UUID
    provider_type: str
    enabled: bool
    client_id: str
    # client_secret NOT included for security
    tenant_domain: Optional[str] = None
    authority_url: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    scopes: List[str]
    auto_provision_enabled: bool
    default_role_id: Optional[uuid.UUID] = None
    domain_restriction: Optional[str] = None
    redirect_uri: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_test_at: Optional[datetime] = None
    last_test_status: Optional[str] = None
    last_test_error: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class SSOConnectStart(BaseModel):
    """Schema for starting SSO connect workflow"""
    provider_type: str = Field(..., pattern="^(azure_ad|google|okta|generic_oidc)$")
    redirect_uri: Optional[str] = None


class SSOConnectCallback(BaseModel):
    """Schema for SSO connect callback"""
    code: str
    state: str
    tenant_id: Optional[uuid.UUID] = None


class SSOAuthorizationResponse(BaseModel):
    """Response for SSO authorization URL"""
    authorization_url: str
    state: str


class SSOTestResponse(BaseModel):
    """Response for SSO connection test"""
    status: str  # 'success', 'failed'
    message: str
    error: Optional[str] = None


class UserAuthMethods(BaseModel):
    """User authentication methods"""
    local: bool  # Has password
    sso: List[str]  # List of SSO providers (e.g., ['azure_ad'])


class AzureADUser(BaseModel):
    """Azure AD user from Microsoft Graph API"""
    id: str
    displayName: Optional[str] = None
    mail: Optional[str] = None
    userPrincipalName: Optional[str] = None
    accountEnabled: Optional[bool] = True
    jobTitle: Optional[str] = None
    department: Optional[str] = None


class AzureADUserListResponse(BaseModel):
    """Response for Azure AD user list"""
    users: List[AzureADUser]
    total: int


class ImportUsersRequest(BaseModel):
    """Request to import users from Azure AD"""
    user_ids: List[str] = Field(..., description="List of Azure AD user IDs to import")
    role_id: uuid.UUID = Field(..., description="Role to assign to imported users")
    send_invitation: bool = Field(False, description="Send invitation email to imported users")


class ImportUsersResponse(BaseModel):
    """Response for user import"""
    imported: int
    skipped: int
    errors: List[Dict[str, Any]]
    users: List[str]  # List of imported user IDs (as strings)

