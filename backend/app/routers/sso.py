# backend/app/routers/sso.py
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import User, Tenant
from app.services.auth import get_current_user
from app.services.audit_decorator import audit_log_action
from app.services.rbac import require_permission
from app.crud import sso as crud_sso
from app.schemas.sso import (
    TenantSSOConfigRead,
    TenantSSOConfigCreate,
    TenantSSOConfigUpdate,
    SSOConnectStart,
    SSOAuthorizationResponse,
    SSOTestResponse,
    UserAuthMethods,
    AzureADUserListResponse,
    AzureADUser,
    ImportUsersRequest,
    ImportUsersResponse
)
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.sso_auth import SSOAuthService
from app.services.azure_ad_service import AzureADService
from app.config import settings
from app.services.audit_log import create_audit_log, resolve_audit_language
from app.services.sso_state_store import consume_sso_state, store_sso_state
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth/sso",
    tags=["sso"],
)


# Public endpoint to check if SSO is enabled (for login page)
@router.get("/enabled")
async def check_sso_enabled(
    tenant_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Public endpoint to check if SSO is enabled for a tenant.
    Used by login page to show/hide SSO button.
    """
    # If tenant_id not provided, try to get from first tenant (for testing)
    if not tenant_id:
        tenant = db.query(Tenant).first()
        if tenant:
            tenant_id = tenant.id
        else:
            return {"enabled": False, "provider": None}
    
    sso_config = crud_sso.get_sso_config(db, tenant_id)
    if not sso_config or not sso_config.enabled:
        return {"enabled": False, "provider": None}
    
    return {
        "enabled": True,
        "provider": sso_config.provider_type,
        "provider_name": "Microsoft" if sso_config.provider_type == "azure_ad" else sso_config.provider_type
    }


# SSO Configuration Management
@router.get("/config", response_model=TenantSSOConfigRead)
def get_sso_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("sso", 1)),
):
    """Get SSO configuration for current tenant"""
    sso_config = crud_sso.get_sso_config(db, current_user.tenant_id)
    if not sso_config:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="SSO configuration not found"
        )
    return sso_config


@router.post("/config", response_model=TenantSSOConfigRead, status_code=201)
@audit_log_action("create", "TenantSSOConfig")
def create_sso_config(
    sso_config: TenantSSOConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("sso", 2)),
):
    """Create SSO configuration for current tenant"""
    
    try:
        db_sso_config = crud_sso.create_sso_config(
            db, sso_config, current_user.tenant_id, current_user.id
        )
        return db_sso_config
    except ValueError as e:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=str(e)
        )


@router.put("/config", response_model=TenantSSOConfigRead)
@audit_log_action("update", "TenantSSOConfig")
def update_sso_config(
    sso_config_update: TenantSSOConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("sso", 2)),
):
    """Update SSO configuration for current tenant"""
    
    db_sso_config = crud_sso.update_sso_config(
        db, current_user.tenant_id, sso_config_update
    )
    if not db_sso_config:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="SSO configuration not found"
        )
    return db_sso_config


@router.delete("/config", status_code=204)
@audit_log_action("delete", "TenantSSOConfig")
def delete_sso_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("sso", 2)),
):
    """Delete SSO configuration for current tenant"""
    
    success = crud_sso.delete_sso_config(db, current_user.tenant_id)
    if not success:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="SSO configuration not found"
        )


# SSO Connect Workflow
@router.post("/connect/start", response_model=SSOAuthorizationResponse)
async def sso_connect_start(
    connect_start: SSOConnectStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("sso", 2)),
):
    """Start SSO connect workflow"""
    
    # For Azure AD, we need to create a temporary config or use existing
    # For now, we'll require config to exist first
    sso_config = crud_sso.get_sso_config(db, current_user.tenant_id)
    
    if not sso_config:
        # Create temporary config for connect workflow
        # This will be updated after successful callback
        from app.schemas.sso import TenantSSOConfigCreate
        temp_config = TenantSSOConfigCreate(
            provider_type=connect_start.provider_type,
            enabled=False,
            client_id="",  # Will be set after callback
            client_secret="",  # Will be set after callback
            redirect_uri=connect_start.redirect_uri or settings.SSO_REDIRECT_URI
        )
        sso_config = crud_sso.create_sso_config(
            db, temp_config, current_user.tenant_id, current_user.id
        )
    
    # Generate state and PKCE
    state = SSOAuthService.generate_state()
    code_verifier, code_challenge = SSOAuthService.generate_pkce()
    
    store_sso_state(state, code_verifier, current_user.tenant_id, db)

    redirect_uri = connect_start.redirect_uri or settings.SSO_REDIRECT_URI
    
    # Get authorization URL
    try:
        auth_url = SSOAuthService.get_authorization_url(
            sso_config,
            redirect_uri,
            state,
            code_challenge
        )
    except Exception as e:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )
    
    return SSOAuthorizationResponse(
        authorization_url=auth_url,
        state=state
    )


# SSO Authorization Flow
@router.get("/{provider}/authorize")
async def sso_authorize(
    provider: str,
    tenant_id: Optional[uuid.UUID] = Query(None),
    redirect_uri: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """OAuth2 authorization endpoint - redirects to identity provider"""
    # Get tenant from query or use default
    if not tenant_id:
        # Try to get from first tenant (for testing)
        tenant = db.query(Tenant).first()
        if not tenant:
            raise ErrorCodeException(
                status_code=400,
                error_code=ErrorCode.INVALID_INPUT,
                detail="tenant_id required"
            )
        tenant_id = tenant.id
    
    sso_config = crud_sso.get_sso_config(db, tenant_id)
    if not sso_config or not sso_config.enabled:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="SSO not configured or not enabled for this tenant"
        )
    
    if sso_config.provider_type != provider:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=f"Provider mismatch: expected {sso_config.provider_type}, got {provider}"
        )
    
    # Generate state and PKCE
    state = SSOAuthService.generate_state()
    code_verifier, code_challenge = SSOAuthService.generate_pkce()
    
    store_sso_state(state, code_verifier, tenant_id, db)
    
    redirect_uri = redirect_uri or sso_config.redirect_uri or settings.SSO_REDIRECT_URI
    
    auth_url = SSOAuthService.get_authorization_url(
        sso_config,
        redirect_uri,
        state,
        code_challenge
    )
    
    return RedirectResponse(url=auth_url)


@router.get("/{provider}/callback")
async def sso_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """OAuth2 callback endpoint - handles redirect from identity provider"""
    logger.info(f"SSO callback received for provider {provider}")
    
    if error:
        logger.error(f"OAuth error in callback: {error}")
        frontend_url = settings.SSO_REDIRECT_URI.replace("/auth/sso/callback", "")
        redirect_url = f"{frontend_url}/auth/sso/error?error={error}"
        return RedirectResponse(url=redirect_url)
    
    # Resolve state from server-side store (single use).
    state_payload = consume_sso_state(state, db)
    if not state_payload:
        logger.error("Missing or expired SSO state")
        frontend_url = settings.SSO_REDIRECT_URI.replace("/auth/sso/callback", "")
        redirect_url = f"{frontend_url}/auth/sso/error?error=Invalid+state+parameter"
        return RedirectResponse(url=redirect_url)
    code_verifier = state_payload["code_verifier"]
    tenant_id = uuid.UUID(state_payload["tenant_id"])
    logger.info(f"Resolved SSO state successfully for tenant {tenant_id}")
    
    sso_config = crud_sso.get_sso_config(db, tenant_id)
    if not sso_config or not sso_config.enabled:
        logger.warning(f"SSO not configured or not enabled for tenant {tenant_id}")
        frontend_url = settings.SSO_REDIRECT_URI.replace("/auth/sso/callback", "")
        redirect_url = f"{frontend_url}/auth/sso/error?error=SSO+not+configured+or+not+enabled"
        return RedirectResponse(url=redirect_url)
    
    if sso_config.provider_type != provider:
        logger.error(f"Provider mismatch: config has {sso_config.provider_type}, callback has {provider}")
        frontend_url = settings.SSO_REDIRECT_URI.replace("/auth/sso/callback", "")
        redirect_url = f"{frontend_url}/auth/sso/error?error=Provider+mismatch"
        return RedirectResponse(url=redirect_url)
    
    redirect_uri = sso_config.redirect_uri or settings.SSO_REDIRECT_URI
    
    try:
        # Exchange code for token
        logger.info("Exchanging authorization code for access token")
        token_response = await SSOAuthService.exchange_code_for_token(
            sso_config,
            code,
            redirect_uri,
            code_verifier
        )
        
        access_token = token_response.get("access_token")
        if not access_token:
            logger.error("No access token in token response")
            raise ValueError("No access token in response")
        
        # Get user info
        logger.info("Retrieving user info from identity provider")
        user_info = await SSOAuthService.get_user_info(sso_config, access_token)
        
        # Find or create user
        logger.info("Finding or creating user")
        user = SSOAuthService.find_or_create_user(
            db, user_info, tenant_id, sso_config
        )
        
        # Create JWT token
        logger.info(f"Creating JWT token for user {user.id}")
        sso_token = SSOAuthService.create_sso_token(user)
        
        # Audit log
        ip_address = request.client.host if request and request.client else None
        create_audit_log(
            db=db,
            user_id=user.id,
            tenant_id=user.tenant_id,
            action="sso_login",
            entity="User",
            entity_id=user.id,
            ip_address=ip_address,
            commit=True,
            language=resolve_audit_language(user, request),
            provider=provider,
        )
        
        logger.info(f"SSO login successful for user {user.id} ({user.email})")
        
        frontend_url = settings.SSO_REDIRECT_URI.replace("/auth/sso/callback", "")
        redirect_url = f"{frontend_url}/auth/sso/success"
        
        response = RedirectResponse(url=redirect_url)
        response.set_cookie(
            key="access_token_cookie",
            value=sso_token,
            httponly=True,
            secure=settings.SECURE_COOKIES,
            samesite=settings.SAME_SITE_COOKIES,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
        )
        
        return response
        
    except ValueError as e:
        # User-facing errors (domain restriction, auto-provisioning disabled, etc.)
        logger.warning(f"SSO callback user error: {e}")
        frontend_url = settings.SSO_REDIRECT_URI.replace("/auth/sso/callback", "")
        # URL encode error message
        import urllib.parse
        error_msg = urllib.parse.quote(str(e))
        redirect_url = f"{frontend_url}/auth/sso/error?error={error_msg}"
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        logger.error(f"SSO callback error: {e}", exc_info=True)
        frontend_url = settings.SSO_REDIRECT_URI.replace("/auth/sso/callback", "")
        import urllib.parse
        error_msg = urllib.parse.quote(f"SSO login failed: {str(e)}")
        redirect_url = f"{frontend_url}/auth/sso/error?error={error_msg}"
        return RedirectResponse(url=redirect_url)


# SSO Test
@router.post("/test", response_model=SSOTestResponse)
async def test_sso_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("sso", 2)),
):
    """Test SSO connection"""
    
    sso_config = crud_sso.get_sso_config(db, current_user.tenant_id)
    if not sso_config:
        return SSOTestResponse(
            status="failed",
            message="SSO not configured",
            error="No SSO configuration found"
        )
    
    try:
        # Test by trying to get discovery document
        if sso_config.provider_type == "azure_ad":
            discovery_url = SSOAuthService.get_azure_ad_discovery_url(
                sso_config.tenant_domain or "common"
            )
        elif sso_config.authority_url:
            discovery_url = f"{sso_config.authority_url}/.well-known/openid-configuration"
        else:
            return SSOTestResponse(
                status="failed",
                message="Invalid configuration",
                error="No discovery URL available"
            )
        
        discovery = await SSOAuthService.fetch_oidc_discovery(discovery_url)
        
        # Update test status
        sso_config.last_test_at = datetime.now()
        sso_config.last_test_status = "success"
        sso_config.last_test_error = None
        db.commit()
        
        return SSOTestResponse(
            status="success",
            message="SSO connection test successful"
        )
        
    except Exception as e:
        # Update test status
        sso_config.last_test_at = datetime.now()
        sso_config.last_test_status = "failed"
        sso_config.last_test_error = str(e)
        db.commit()
        
        return SSOTestResponse(
            status="failed",
            message="SSO connection test failed",
            error=str(e)
        )


# User Auth Methods
@router.get("/users/{user_id}/auth-methods", response_model=UserAuthMethods)
def get_user_auth_methods(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("sso", 1)),
):
    """Get authentication methods available for a user"""
    # Only admins or the user themselves
    from app.services.rbac import check_permission
    if not check_permission(current_user, "sso", 2) and current_user.id != user_id:
        raise ErrorCodeException(
            status_code=403,
            error_code=ErrorCode.ACCESS_DENIED
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.USER_NOT_FOUND
        )
    
    local = user.password_hash is not None
    sso = []
    if user.auth_provider and user.auth_provider != "local":
        sso.append(user.auth_provider)
    
    return UserAuthMethods(local=local, sso=sso)


# Azure AD User Import
@router.get("/azure-ad/users", response_model=AzureADUserListResponse)
async def list_azure_ad_users(
    filter_query: Optional[str] = Query(None, description="OData filter query"),
    top: int = Query(100, ge=1, le=999, description="Maximum number of users to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("sso", 3)),
):
    """
    List users from Azure AD (Entra ID) for import.
    Requires SSO configuration to be set up.
    """
    
    sso_config = crud_sso.get_sso_config(db, current_user.tenant_id)
    if not sso_config:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="SSO configuration not found. Please configure SSO first."
        )
    
    if sso_config.provider_type != "azure_ad":
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=f"This endpoint is only for Azure AD. Current provider: {sso_config.provider_type}"
        )
    
    try:
        logger.info(f"Fetching Azure AD users for tenant {current_user.tenant_id}, filter: {filter_query}, top: {top}")
        
        users = await AzureADService.list_users(
            config=sso_config,
            filter_query=filter_query,
            top=top
        )
        
        logger.info(f"Retrieved {len(users)} raw users from Azure AD")
        
        # Convert to response format, filtering out invalid users
        azure_users = []
        for u in users:
            try:
                # Ensure id is present (required field)
                user_id = u.get("id")
                if not user_id:
                    logger.warning(f"Skipping user without ID: {u}")
                    continue
                
                azure_user = AzureADUser(
                    id=user_id,
                    displayName=u.get("displayName"),
                    mail=u.get("mail"),
                    userPrincipalName=u.get("userPrincipalName"),
                    accountEnabled=u.get("accountEnabled", True),
                    jobTitle=u.get("jobTitle"),
                    department=u.get("department")
                )
                azure_users.append(azure_user)
            except Exception as user_error:
                logger.warning(f"Error processing user {u.get('id', 'unknown')}: {user_error}, skipping")
                continue
        
        logger.info(f"Successfully converted {len(azure_users)} users to response format")
        
        return AzureADUserListResponse(
            users=azure_users,
            total=len(azure_users)
        )
    except ValueError as e:
        # Errors from AzureADService (authentication, network, decryption, etc.)
        error_msg = str(e)
        logger.error(f"Azure AD service error: {error_msg}", exc_info=True)
        # If it's a decryption error, return a more specific error code/message
        if "decrypt client secret" in error_msg.lower():
            raise ErrorCodeException(
                status_code=400,
                error_code=ErrorCode.INVALID_INPUT,
                detail="Unable to decrypt client secret. Please reconfigure the SSO settings with a new client secret."
            )
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=f"Azure AD service error: {error_msg}"
        )
    except Exception as e:
        logger.error(f"Error listing Azure AD users: {e}", exc_info=True)
        raise ErrorCodeException(
            status_code=500,
            error_code=ErrorCode.INTERNAL_ERROR,
            detail=f"Failed to list Azure AD users: {str(e)}"
        )


@router.post("/azure-ad/import", response_model=ImportUsersResponse)
async def import_azure_ad_users(
    import_request: ImportUsersRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("sso", 3)),
):
    """
    Import selected users from Azure AD into the system.
    Users will be created with SSO authentication only (no password).
    """
    try:
        logger.info(f"Import request received: {len(import_request.user_ids)} users, role_id: {import_request.role_id}")
        
        sso_config = crud_sso.get_sso_config(db, current_user.tenant_id)
        if not sso_config:
            raise ErrorCodeException(
                status_code=404,
                error_code=ErrorCode.ASSET_NOT_FOUND,
                detail="SSO configuration not found"
            )
        
        if sso_config.provider_type != "azure_ad":
            raise ErrorCodeException(
                status_code=400,
                error_code=ErrorCode.INVALID_INPUT,
                detail="This endpoint is only for Azure AD"
            )
        
        # Verify role exists
        from app.models import Role
        role = db.query(Role).filter(
            Role.id == import_request.role_id,
            Role.tenant_id == current_user.tenant_id
        ).first()
        if not role:
            raise ErrorCodeException(
                status_code=404,
                error_code=ErrorCode.ASSET_NOT_FOUND,
                detail="Role not found"
            )
        
        logger.info(f"Role verified: {role.name} (id: {role.id})")
        
        imported = 0
        skipped = 0
        errors = []
        imported_user_ids = []
        
        logger.info(f"Starting import of {len(import_request.user_ids)} users from Azure AD for tenant {current_user.tenant_id}")
        
        # Get user details from Azure AD
        for azure_user_id in import_request.user_ids:
            try:
                logger.debug(f"Processing Azure AD user ID: {azure_user_id}")
                
                # Get user info from Azure AD
                azure_user = await AzureADService.get_user_by_id(sso_config, azure_user_id)
                
                if not azure_user:
                    logger.warning(f"Azure AD user {azure_user_id} not found")
                    errors.append({
                        "user_id": azure_user_id,
                        "error": "User not found in Azure AD"
                    })
                    skipped += 1
                    continue
                
                external_id = azure_user.get("id")
                email = azure_user.get("mail") or azure_user.get("userPrincipalName")
                name = azure_user.get("displayName") or (email.split("@")[0] if email else "Unknown")
                sso_email = azure_user.get("userPrincipalName")
                
                if not email:
                    logger.warning(f"Email not found for Azure AD user {azure_user_id}")
                    errors.append({
                        "user_id": azure_user_id,
                        "error": "Email not found in Azure AD user"
                    })
                    skipped += 1
                    continue
                
                if not external_id:
                    logger.warning(f"External ID not found for Azure AD user {azure_user_id}")
                    errors.append({
                        "user_id": azure_user_id,
                        "email": email,
                        "error": "External ID not found in Azure AD user"
                    })
                    skipped += 1
                    continue
                
                logger.debug(f"Processing user: {email} (external_id: {external_id})")
                
                # Check domain restriction
                if sso_config.domain_restriction:
                    domain = email.split("@")[-1] if "@" in email else ""
                    if domain.lower() != sso_config.domain_restriction.lower():
                        logger.info(f"User {email} skipped due to domain restriction: {domain} != {sso_config.domain_restriction}")
                        errors.append({
                            "user_id": azure_user_id,
                            "email": email,
                            "error": f"Domain {domain} not allowed"
                        })
                        skipped += 1
                        continue
                
                # Check if user already exists
                existing_user = db.query(User).filter(
                    User.external_id == external_id,
                    User.tenant_id == current_user.tenant_id
                ).first()
                
                if not existing_user:
                    # Check by email
                    existing_user = db.query(User).filter(
                        User.email == email.lower(),
                        User.tenant_id == current_user.tenant_id,
                        User.deleted_at == None
                    ).first()
                
                if existing_user:
                    # Update existing user
                    logger.info(f"Updating existing user {existing_user.id} ({email})")
                    existing_user.external_id = external_id
                    existing_user.sso_email = sso_email
                    existing_user.auth_provider = "azure_ad"
                    existing_user.role_id = import_request.role_id
                    existing_user.sso_metadata = azure_user
                    if not existing_user.name or existing_user.name == "Unknown":
                        existing_user.name = name
                    try:
                        db.commit()
                        db.refresh(existing_user)
                        imported_user_ids.append(str(existing_user.id))
                        imported += 1
                        logger.info(f"Updated user {email} from Azure AD")
                    except Exception as db_error:
                        logger.error(f"Database error updating user {email}: {db_error}", exc_info=True)
                        db.rollback()
                        errors.append({
                            "user_id": azure_user_id,
                            "email": email,
                            "error": f"Database error: {str(db_error)}"
                        })
                        skipped += 1
                else:
                    # Create new user
                    logger.info(f"Creating new user {email}")
                    
                    # Ensure sso_metadata is JSON-serializable
                    try:
                        import json
                        # Test if azure_user is JSON serializable
                        json.dumps(azure_user)
                        sso_metadata = azure_user
                    except (TypeError, ValueError) as json_error:
                        logger.warning(f"Azure user data not fully JSON serializable for {email}, storing minimal metadata: {json_error}")
                        # Store only essential fields
                        sso_metadata = {
                            "id": external_id,
                            "displayName": name,
                            "mail": email,
                            "userPrincipalName": sso_email
                        }
                    
                    try:
                        new_user = User(
                            tenant_id=current_user.tenant_id,
                            email=email.lower(),
                            name=name or "Unknown",
                            password_hash=None,  # SSO-only user
                            auth_provider="azure_ad",
                            external_id=external_id,
                            sso_email=sso_email,
                            sso_metadata=sso_metadata,
                            role_id=import_request.role_id,
                            is_active=True
                        )
                        db.add(new_user)
                        db.flush()  # Flush to get any immediate errors
                        db.commit()
                        db.refresh(new_user)
                        imported_user_ids.append(str(new_user.id))
                        imported += 1
                        logger.info(f"Imported user {email} from Azure AD (new user ID: {new_user.id})")
                    except IntegrityError as integrity_error:
                        logger.error(f"Integrity error creating user {email}: {integrity_error}", exc_info=True)
                        db.rollback()
                        # Check if it's a duplicate email
                        if "email" in str(integrity_error).lower() or "unique" in str(integrity_error).lower():
                            errors.append({
                                "user_id": azure_user_id,
                                "email": email,
                                "error": f"User with email {email} already exists"
                            })
                        else:
                            errors.append({
                                "user_id": azure_user_id,
                                "email": email,
                                "error": f"Database integrity error: {str(integrity_error)}"
                            })
                        skipped += 1
                    except Exception as db_error:
                        logger.error(f"Database error creating user {email}: {db_error}", exc_info=True)
                        db.rollback()
                        errors.append({
                            "user_id": azure_user_id,
                            "email": email,
                            "error": f"Database error: {str(db_error)}"
                        })
                        skipped += 1
                
            except Exception as e:
                logger.error(f"Error importing user {azure_user_id}: {e}", exc_info=True)
                errors.append({
                    "user_id": azure_user_id,
                    "error": str(e)
                })
                skipped += 1
        
        # Audit log
        try:
            create_audit_log(
                db=db,
                user_id=current_user.id,
                tenant_id=current_user.tenant_id,
                action="import_users",
                entity="User",
                entity_id=None,
                commit=True,
                language=resolve_audit_language(current_user, request),
                imported=imported,
                skipped=skipped,
            )
        except Exception as audit_error:
            logger.warning(f"Failed to create audit log for user import: {audit_error}")
        
        logger.info(f"Import completed: {imported} imported, {skipped} skipped, {len(errors)} errors")
        
        return ImportUsersResponse(
            imported=imported,
            skipped=skipped,
            errors=errors,
            users=imported_user_ids
        )
    except ErrorCodeException:
        # Re-raise ErrorCodeException as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in import_azure_ad_users endpoint: {e}", exc_info=True)
        raise ErrorCodeException(
            status_code=500,
            error_code=ErrorCode.INTERNAL_ERROR,
            detail=f"Unexpected error during import: {str(e)}"
        )

