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
        
        elif config.provider_type == "google":
            # Google Workspace
            auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
            
            params = {
                "client_id": config.client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "scope": " ".join(config.scopes or ["openid", "profile", "email"]),
                "state": state,
                "access_type": "offline",  # For refresh tokens
                "prompt": "consent",
            }
            
            if code_challenge:
                params["code_challenge"] = code_challenge
                params["code_challenge_method"] = "S256"
            
            return f"{auth_url}?{urlencode(params)}"
        
        elif config.provider_type == "okta":
            # Okta - use discovery URL or direct endpoint
            if config.authorization_endpoint:
                auth_url = config.authorization_endpoint
            else:
                # Try to construct from tenant_domain
                if config.tenant_domain:
                    auth_url = f"https://{config.tenant_domain}/oauth2/v1/authorize"
                else:
                    raise ValueError("Okta requires authorization_endpoint or tenant_domain")
            
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
        logger.info(f"Exchanging code for token for provider {config.provider_type}")
        
        try:
            client_secret = decrypt_secret(config.client_secret_encrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt client secret: {e}")
            raise ValueError("Failed to decrypt client secret. The client secret may have been encrypted with a different ENCRYPTION_KEY. Please reconfigure the SSO settings with a new client secret.")
        
        if config.provider_type == "azure_ad":
            tenant = config.tenant_domain or "common"
            token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        elif config.provider_type == "google":
            token_url = "https://oauth2.googleapis.com/token"
        elif config.provider_type == "okta":
            if config.token_endpoint:
                token_url = config.token_endpoint
            elif config.tenant_domain:
                token_url = f"https://{config.tenant_domain}/oauth2/v1/token"
            else:
                logger.error(f"Token endpoint not configured for Okta provider")
                raise ValueError("Okta requires token_endpoint or tenant_domain")
        elif config.token_endpoint:
            token_url = config.token_endpoint
        else:
            logger.error(f"Token endpoint not configured for provider {config.provider_type}")
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
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0
                )
                response.raise_for_status()
                token_data = response.json()
                logger.info(f"Successfully exchanged code for token for provider {config.provider_type}")
                return token_data
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            logger.error(f"HTTP error exchanging code for token: {e.response.status_code} - {error_detail}")
            raise ValueError(f"Failed to exchange code for token: {e.response.status_code} - {error_detail}")
        except httpx.RequestError as e:
            logger.error(f"Request error exchanging code for token: {e}")
            raise ValueError(f"Network error during token exchange: {str(e)}")
    
    @staticmethod
    async def get_user_info(
        config: TenantSSOConfig,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Get user information from identity provider.
        """
        logger.info(f"Getting user info for provider {config.provider_type}")
        
        if config.provider_type == "azure_ad":
            # Microsoft Graph API
            userinfo_url = "https://graph.microsoft.com/v1.0/me"
            headers = {"Authorization": f"Bearer {access_token}"}
        elif config.provider_type == "google":
            # Google UserInfo API
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
        elif config.provider_type == "okta":
            if config.userinfo_endpoint:
                userinfo_url = config.userinfo_endpoint
            elif config.tenant_domain:
                userinfo_url = f"https://{config.tenant_domain}/oauth2/v1/userinfo"
            else:
                logger.error(f"UserInfo endpoint not configured for Okta provider")
                raise ValueError("Okta requires userinfo_endpoint or tenant_domain")
            headers = {"Authorization": f"Bearer {access_token}"}
        elif config.userinfo_endpoint:
            userinfo_url = config.userinfo_endpoint
            headers = {"Authorization": f"Bearer {access_token}"}
        else:
            # Try to decode JWT token for user info
            try:
                import jwt
                decoded = jwt.decode(access_token, options={"verify_signature": False})
                logger.info("Successfully decoded user info from JWT token")
                return decoded
            except Exception as e:
                logger.error(f"Failed to decode JWT token: {e}")
                raise ValueError(f"UserInfo endpoint not configured for {config.provider_type} and JWT decode failed")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(userinfo_url, headers=headers, timeout=10.0)
                response.raise_for_status()
                user_info = response.json()
                logger.info(f"Successfully retrieved user info for provider {config.provider_type}")
                return user_info
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            logger.error(f"HTTP error getting user info: {e.response.status_code} - {error_detail}")
            raise ValueError(f"Failed to get user info: {e.response.status_code} - {error_detail}")
        except httpx.RequestError as e:
            logger.error(f"Request error getting user info: {e}")
            raise ValueError(f"Network error getting user info: {str(e)}")
    
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
        logger.info(f"Finding or creating user for tenant {tenant_id}, provider {config.provider_type}")
        
        # Extract user info based on provider
        if config.provider_type == "azure_ad":
            external_id = user_info.get("id") or user_info.get("sub")
            email = user_info.get("mail") or user_info.get("userPrincipalName")
            name = user_info.get("displayName") or user_info.get("name", "")
            sso_email = user_info.get("userPrincipalName")
        elif config.provider_type == "google":
            external_id = user_info.get("sub") or user_info.get("id")
            email = user_info.get("email")
            name = user_info.get("name", "")
            sso_email = user_info.get("email")
        elif config.provider_type == "okta":
            external_id = user_info.get("sub")
            email = user_info.get("email")
            name = user_info.get("name", "") or f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip()
            sso_email = user_info.get("email")
        else:
            # Generic OIDC
            external_id = user_info.get("sub")
            email = user_info.get("email")
            name = user_info.get("name", "")
            sso_email = user_info.get("email")
        
        if not email:
            logger.error("Email not found in user info")
            raise ValueError("Email not found in user info")
        
        logger.info(f"Processing SSO login for email: {email}, external_id: {external_id}")
        
        # Check domain restriction
        if config.domain_restriction:
            domain = email.split("@")[-1] if "@" in email else ""
            if domain.lower() != config.domain_restriction.lower():
                logger.warning(f"Domain restriction violation: {domain} not allowed (required: {config.domain_restriction})")
                raise ValueError(f"Email domain {domain} not allowed. Only {config.domain_restriction} allowed.")
            logger.info(f"Domain restriction check passed: {domain}")
        else:
            if config.auto_provision_enabled:
                logger.warning(f"Auto-provisioning enabled without domain restriction for tenant {tenant_id}. This is a security risk!")
        
        # Try to find existing user
        # 1. By external_id (already linked)
        if external_id:
            user = db.query(User).filter(
                User.external_id == external_id,
                User.tenant_id == tenant_id
            ).first()
            if user:
                logger.info(f"Found existing user by external_id: {user.id} ({user.email})")
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
            logger.info(f"Found existing user by email: {user.id} ({user.email}), linking to SSO")
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
            logger.warning(f"Auto-provisioning disabled. User {email} not found and cannot be created.")
            raise ValueError("Auto-provisioning is disabled. User not found and cannot be created.")
        
        logger.info(f"Auto-provisioning enabled. Creating new user for {email}")
        
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
                logger.info(f"Using default 'viewer' role for new user: {default_role_id}")
            else:
                logger.warning(f"No default role configured and 'viewer' role not found for tenant {tenant_id}")
        
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
        
        logger.info(f"Auto-provisioned user {email} (id: {new_user.id}) via {config.provider_type} with role {default_role_id}")
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

