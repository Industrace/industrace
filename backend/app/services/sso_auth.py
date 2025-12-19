# backend/app/services/sso_auth.py
"""
Service per Enterprise Authentication (OAuth2/OIDC).
Supporta Azure AD (EntraID), Google Workspace, Okta, e provider OIDC generici.
"""
from typing import Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import secrets
import base64
import hashlib
import httpx
import json
from urllib.parse import urlencode, parse_qs

from app.models import User, TenantSSOConfig, Tenant, Role
from app.crud import users as crud_users
from app.services.sso_encryption import encrypt_secret, decrypt_secret
from app.services.auth import create_access_token
from app.config import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class SSOAuthService:
    """
    Service per gestire OAuth2/OIDC authentication flow.
    """
    
    @staticmethod
    def generate_pkce() -> Tuple[str, str]:
        """
        Generate PKCE code verifier and challenge for OAuth2 flow.
        Returns: (code_verifier, code_challenge)
        """
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode().rstrip('=')
        
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        return code_verifier, code_challenge
    
    @staticmethod
    def generate_state() -> str:
        """Generate random state for OAuth flow"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_azure_ad_discovery_url(tenant_domain: str) -> str:
        """
        Get Azure AD OIDC discovery URL.
        tenant_domain can be tenant ID (UUID) or domain name.
        """
        if tenant_domain:
            return f"https://login.microsoftonline.com/{tenant_domain}/v2.0/.well-known/openid-configuration"
        return "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration"
    
    @staticmethod
    async def fetch_oidc_discovery(url: str) -> Dict[str, Any]:
        """Fetch OIDC discovery document"""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    def get_authorization_url(
        config: TenantSSOConfig,
        redirect_uri: str,
        state: str,
        code_challenge: Optional[str] = None
    ) -> str:
        """
        Generate OAuth2 authorization URL.
        """
        if config.provider_type == "azure_ad":
            # Azure AD specific
            tenant = config.tenant_domain or "common"
            authority = f"https://login.microsoftonline.com/{tenant}"
            auth_url = f"{authority}/oauth2/v2.0/authorize"
            
            params = {
                "client_id": config.client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "response_mode": "query",
                "scope": " ".join(config.scopes or ["openid", "profile", "email"]),
                "state": state,
            }
            
            if code_challenge:
                params["code_challenge"] = code_challenge
                params["code_challenge_method"] = "S256"
            
            return f"{auth_url}?{urlencode(params)}"
        
        elif config.authorization_endpoint:
            # Generic OIDC
            params = {
                "client_id": config.client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "scope": " ".join(config.scopes or ["openid", "profile", "email"]),
                "state": state,
            }
            
            if code_challenge:
                params["code_challenge"] = code_challenge
                params["code_challenge_method"] = "S256"
            
            return f"{config.authorization_endpoint}?{urlencode(params)}"
        
        else:
            raise ValueError(f"Invalid configuration for provider {config.provider_type}")
    
    @staticmethod
    async def exchange_code_for_token(
        config: TenantSSOConfig,
        code: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        """
        client_secret = decrypt_secret(config.client_secret_encrypted)
        
        if config.provider_type == "azure_ad":
            tenant = config.tenant_domain or "common"
            token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        elif config.token_endpoint:
            token_url = config.token_endpoint
        else:
            raise ValueError(f"Token endpoint not configured for {config.provider_type}")
        
        data = {
            "client_id": config.client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        
        if code_verifier:
            data["code_verifier"] = code_verifier
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_user_info(
        config: TenantSSOConfig,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Get user information from identity provider.
        """
        if config.provider_type == "azure_ad":
            # Microsoft Graph API
            userinfo_url = "https://graph.microsoft.com/v1.0/me"
            headers = {"Authorization": f"Bearer {access_token}"}
        elif config.userinfo_endpoint:
            userinfo_url = config.userinfo_endpoint
            headers = {"Authorization": f"Bearer {access_token}"}
        else:
            # Try to decode JWT token for user info
            try:
                import jwt
                decoded = jwt.decode(access_token, options={"verify_signature": False})
                return decoded
            except:
                raise ValueError(f"UserInfo endpoint not configured for {config.provider_type}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(userinfo_url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    def find_or_create_user(
        db: Session,
        user_info: Dict[str, Any],
        tenant_id: uuid.UUID,
        config: TenantSSOConfig
    ) -> User:
        """
        Find existing user or create new one based on SSO user info.
        Implements auto-provisioning logic.
        """
        # Extract user info based on provider
        if config.provider_type == "azure_ad":
            external_id = user_info.get("id") or user_info.get("sub")
            email = user_info.get("mail") or user_info.get("userPrincipalName")
            name = user_info.get("displayName") or user_info.get("name", "")
            sso_email = user_info.get("userPrincipalName")
        else:
            # Generic OIDC
            external_id = user_info.get("sub")
            email = user_info.get("email")
            name = user_info.get("name", "")
            sso_email = user_info.get("email")
        
        if not email:
            raise ValueError("Email not found in user info")
        
        # Check domain restriction
        if config.domain_restriction:
            domain = email.split("@")[-1] if "@" in email else ""
            if domain.lower() != config.domain_restriction.lower():
                raise ValueError(f"Email domain {domain} not allowed. Only {config.domain_restriction} allowed.")
        
        # Try to find existing user
        # 1. By external_id (already linked)
        if external_id:
            user = db.query(User).filter(
                User.external_id == external_id,
                User.tenant_id == tenant_id
            ).first()
            if user:
                # Update last SSO login
                user.last_sso_login = datetime.now()
                user.sso_email = sso_email
                if not user.auth_provider:
                    user.auth_provider = config.provider_type
                db.commit()
                db.refresh(user)
                return user
        
        # 2. By email (matching existing user)
        user = db.query(User).filter(
            User.email == email.lower(),
            User.tenant_id == tenant_id,
            User.deleted_at == None
        ).first()
        
        if user:
            # Link existing user to SSO
            user.external_id = external_id
            user.sso_email = sso_email
            user.auth_provider = config.provider_type
            user.last_sso_login = datetime.now()
            user.sso_metadata = user_info
            db.commit()
            db.refresh(user)
            return user
        
        # 3. Auto-provisioning (if enabled)
        if not config.auto_provision_enabled:
            raise ValueError("Auto-provisioning is disabled. User not found and cannot be created.")
        
        # Create new user
        default_role_id = config.default_role_id
        if not default_role_id:
            # Get default 'viewer' role
            viewer_role = db.query(Role).filter(
                Role.name == "viewer",
                Role.tenant_id == tenant_id
            ).first()
            if viewer_role:
                default_role_id = viewer_role.id
        
        new_user = User(
            tenant_id=tenant_id,
            email=email.lower(),
            name=name,
            password_hash=None,  # SSO-only user
            auth_provider=config.provider_type,
            external_id=external_id,
            sso_email=sso_email,
            last_sso_login=datetime.now(),
            sso_metadata=user_info,
            role_id=default_role_id,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"Auto-provisioned user {email} via {config.provider_type}")
        return new_user
    
    @staticmethod
    def create_sso_token(user: User) -> str:
        """
        Create JWT token for SSO-authenticated user.
        Same format as local login tokens.
        """
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "tenant_id": str(user.tenant_id)},
            expires_delta=access_token_expires,
        )
        return access_token

