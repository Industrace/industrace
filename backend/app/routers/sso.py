# backend/app/routers/sso.py
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Tenant
from app.services.auth import get_current_user
from app.services.audit_decorator import audit_log_action
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
from app.services.audit_log import create_audit_log
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth/sso",
    tags=["sso"],
)


# SSO Configuration Management
@router.get("/config", response_model=TenantSSOConfigRead)
def get_sso_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
):
    """Create SSO configuration for current tenant (admin only)"""
    if current_user.role.name != "admin":
        raise ErrorCodeException(
            status_code=403,
            error_code=ErrorCode.ACCESS_DENIED,
            detail="Only admins can configure SSO"
        )
    
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
):
    """Update SSO configuration for current tenant (admin only)"""
    if current_user.role.name != "admin":
        raise ErrorCodeException(
            status_code=403,
            error_code=ErrorCode.ACCESS_DENIED,
            detail="Only admins can configure SSO"
        )
    
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
):
    """Delete SSO configuration for current tenant (admin only)"""
    if current_user.role.name != "admin":
        raise ErrorCodeException(
            status_code=403,
            error_code=ErrorCode.ACCESS_DENIED,
            detail="Only admins can configure SSO"
        )
    
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
):
    """Start SSO connect workflow (admin only)"""
    if current_user.role.name != "admin":
        raise ErrorCodeException(
            status_code=403,
            error_code=ErrorCode.ACCESS_DENIED,
            detail="Only admins can configure SSO"
        )
    
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
    
    # Store state and code_verifier (in production, use Redis or session)
    # For now, we'll include in state (not ideal, but works)
    # In production: store in Redis with expiry
    
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
    
    # Store state and code_verifier (in production, use Redis)
    # For now, encode in state (not secure, but works for MVP)
    # Format: base64(state|code_verifier|tenant_id)
    import base64
    state_data = f"{state}|{code_verifier}|{str(tenant_id)}"
    encoded_state = base64.urlsafe_b64encode(state_data.encode()).decode()
    
    redirect_uri = redirect_uri or sso_config.redirect_uri or settings.SSO_REDIRECT_URI
    
    auth_url = SSOAuthService.get_authorization_url(
        sso_config,
        redirect_uri,
        encoded_state,  # Use encoded state
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
    if error:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=f"OAuth error: {error}"
        )
    
    # Decode state to get code_verifier and tenant_id
    try:
        import base64
        state_data = base64.urlsafe_b64decode(state.encode()).decode()
        state_parts = state_data.split("|")
        if len(state_parts) != 3:
            raise ValueError("Invalid state format")
        original_state, code_verifier, tenant_id_str = state_parts
        tenant_id = uuid.UUID(tenant_id_str)
    except Exception as e:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=f"Invalid state: {str(e)}"
        )
    
    sso_config = crud_sso.get_sso_config(db, tenant_id)
    if not sso_config or not sso_config.enabled:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="SSO not configured or not enabled"
        )
    
    redirect_uri = sso_config.redirect_uri or settings.SSO_REDIRECT_URI
    
    try:
        # Exchange code for token
        token_response = await SSOAuthService.exchange_code_for_token(
            sso_config,
            code,
            redirect_uri,
            code_verifier
        )
        
        access_token = token_response.get("access_token")
        if not access_token:
            raise ValueError("No access token in response")
        
        # Get user info
        user_info = await SSOAuthService.get_user_info(sso_config, access_token)
        
        # Find or create user
        user = SSOAuthService.find_or_create_user(
            db, user_info, tenant_id, sso_config
        )
        
        # Create JWT token
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
            description=f"SSO login via {provider}",
            ip_address=ip_address,
            commit=True,
        )
        
        # Redirect to frontend with token
        # In production, use secure cookie instead of query param
        frontend_url = settings.SSO_REDIRECT_URI.replace("/auth/sso/callback", "")
        redirect_url = f"{frontend_url}/auth/sso/success?token={sso_token}"
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"SSO callback error: {e}", exc_info=True)
        frontend_url = settings.SSO_REDIRECT_URI.replace("/auth/sso/callback", "")
        redirect_url = f"{frontend_url}/auth/sso/error?error={str(e)}"
        return RedirectResponse(url=redirect_url)


# SSO Test
@router.post("/test", response_model=SSOTestResponse)
async def test_sso_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test SSO connection (admin only)"""
    if current_user.role.name != "admin":
        raise ErrorCodeException(
            status_code=403,
            error_code=ErrorCode.ACCESS_DENIED,
            detail="Only admins can test SSO"
        )
    
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
):
    """Get authentication methods available for a user"""
    # Only admins or the user themselves
    if current_user.role.name != "admin" and current_user.id != user_id:
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
):
    """
    List users from Azure AD (Entra ID) for import.
    Requires SSO configuration to be set up.
    """
    if current_user.role.name != "admin":
        raise ErrorCodeException(
            status_code=403,
            error_code=ErrorCode.ACCESS_DENIED,
            detail="Only admins can import users"
        )
    
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
        users = await AzureADService.list_users(
            config=sso_config,
            filter_query=filter_query,
            top=top
        )
        
        # Convert to response format
        azure_users = [
            AzureADUser(
                id=u.get("id"),
                displayName=u.get("displayName"),
                mail=u.get("mail"),
                userPrincipalName=u.get("userPrincipalName"),
                accountEnabled=u.get("accountEnabled", True),
                jobTitle=u.get("jobTitle"),
                department=u.get("department")
            )
            for u in users
        ]
        
        return AzureADUserListResponse(
            users=azure_users,
            total=len(azure_users)
        )
    except Exception as e:
        logger.error(f"Error listing Azure AD users: {e}", exc_info=True)
        raise ErrorCodeException(
            status_code=500,
            error_code=ErrorCode.INTERNAL_ERROR,
            detail=f"Failed to list Azure AD users: {str(e)}"
        )


@router.post("/azure-ad/import", response_model=ImportUsersResponse)
@audit_log_action("import_users_from_azure_ad", "User")
async def import_azure_ad_users(
    import_request: ImportUsersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Import selected users from Azure AD into the system.
    Users will be created with SSO authentication only (no password).
    """
    if current_user.role.name != "admin":
        raise ErrorCodeException(
            status_code=403,
            error_code=ErrorCode.ACCESS_DENIED,
            detail="Only admins can import users"
        )
    
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
    
    imported = 0
    skipped = 0
    errors = []
    imported_user_ids = []
    
    try:
        # Get user details from Azure AD
        for azure_user_id in import_request.user_ids:
            try:
                # Get user info from Azure AD
                azure_user = await AzureADService.get_user_by_id(sso_config, azure_user_id)
                
                external_id = azure_user.get("id")
                email = azure_user.get("mail") or azure_user.get("userPrincipalName")
                name = azure_user.get("displayName") or email.split("@")[0] if email else "Unknown"
                sso_email = azure_user.get("userPrincipalName")
                
                if not email:
                    errors.append({
                        "user_id": azure_user_id,
                        "error": "Email not found in Azure AD user"
                    })
                    skipped += 1
                    continue
                
                # Check domain restriction
                if sso_config.domain_restriction:
                    domain = email.split("@")[-1] if "@" in email else ""
                    if domain.lower() != sso_config.domain_restriction.lower():
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
                    existing_user.external_id = external_id
                    existing_user.sso_email = sso_email
                    existing_user.auth_provider = "azure_ad"
                    existing_user.role_id = import_request.role_id
                    existing_user.sso_metadata = azure_user
                    if not existing_user.name or existing_user.name == "Unknown":
                        existing_user.name = name
                    db.commit()
                    imported_user_ids.append(str(existing_user.id))
                    imported += 1
                else:
                    # Create new user
                    new_user = User(
                        tenant_id=current_user.tenant_id,
                        email=email.lower(),
                        name=name,
                        password_hash=None,  # SSO-only user
                        auth_provider="azure_ad",
                        external_id=external_id,
                        sso_email=sso_email,
                        sso_metadata=azure_user,
                        role_id=import_request.role_id,
                        is_active=True
                    )
                    db.add(new_user)
                    db.commit()
                    db.refresh(new_user)
                    imported_user_ids.append(str(new_user.id))
                    imported += 1
                    
                    logger.info(f"Imported user {email} from Azure AD")
                
            except Exception as e:
                logger.error(f"Error importing user {azure_user_id}: {e}", exc_info=True)
                errors.append({
                    "user_id": azure_user_id,
                    "error": str(e)
                })
                skipped += 1
        
        # Audit log
        create_audit_log(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="import_users_from_azure_ad",
            entity="User",
            entity_id=None,
            description=f"Imported {imported} users from Azure AD, skipped {skipped}",
            commit=True
        )
        
        return ImportUsersResponse(
            imported=imported,
            skipped=skipped,
            errors=errors,
            users=imported_user_ids
        )
        
    except Exception as e:
        logger.error(f"Error in import process: {e}", exc_info=True)
        raise ErrorCodeException(
            status_code=500,
            error_code=ErrorCode.INTERNAL_ERROR,
            detail=f"Import failed: {str(e)}"
        )

