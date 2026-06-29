# File: backend/main.py

import logging
import json
import math

from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError, ExpiredSignatureError

logger = logging.getLogger(__name__)

# Custom JSON encoder to handle inf and NaN values
class SafeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            if math.isnan(obj):
                return None
            if math.isinf(obj):
                return None
        return super().default(obj)

def clean_data_for_json(data):
    """Clean data to remove inf and NaN values before JSON serialization"""
    if isinstance(data, dict):
        return {k: clean_data_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data_for_json(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    else:
        return data


from fastapi import FastAPI, Depends, HTTPException, Form, Request, Cookie

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode

from app.database import get_db
from app.models import User, Asset
from app.schemas import UserRead as UserSchema, LocationCreate as LocationCreate
from app.services.auth import (
    get_current_user,
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.services.audit_log import create_audit_log, resolve_audit_language
from app.services.rate_limiter import check_rate_limit_strict, add_rate_limit_headers_strict
from app.services.security_logging import (
    log_failed_login,
    log_successful_login,
    log_unauthorized_access,
    log_rate_limit_exceeded
)
from app.config import settings
from app.logging_config import setup_logging


def get_cors_origin(request: Request) -> str:
    """
    Determines the correct CORS origin based on the request.
    Returns the origin if it's in the list of allowed origins,
    otherwise returns the first configured origin or empty string.
    """
    allowed_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
    
    if not allowed_origins:
        return ""
    
    # Get the origin from the request
    origin = request.headers.get("origin")
    
    # If the origin is in the allowed list, use it
    if origin and origin in allowed_origins:
        return origin
    
    # Otherwise, use the first configured origin (fallback)
    # In production, this should be the main domain
    return allowed_origins[0] if allowed_origins else ""


def get_cors_headers(request: Request) -> dict:
    """
    Generates the correct CORS headers for a response.
    Uses configured origins instead of "*".
    """
    origin = get_cors_origin(request)
    
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-Key",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Expose-Headers": "X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset",
    }


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    This ensures security headers are present even if nginx is bypassed.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # X-Frame-Options: Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options: Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection: Enable XSS filter (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy: Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content-Security-Policy: Prevent XSS attacks
        # Note: 'unsafe-inline' is needed for some frontend frameworks
        # Consider tightening this based on your frontend requirements
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Strict-Transport-Security: Force HTTPS in production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

from app.routers import users
from app.routers import suppliers
from app.routers import manufacturers
from app.routers import locations
from app.routers import areas
from app.routers import assets
from app.routers import asset_photos
from app.routers import asset_documents
from app.routers import asset_connections
from app.routers import global_connections
from app.routers import asset_interfaces
from app.routers import sites
from app.routers import tenants
from app.routers import locations_floormap
from app.routers import asset_types
from app.routers import dashboards
from app.routers import pcap
from app.routers import asset_statuses
from app.routers import contacts
from app.routers import audit_logs
from app.routers import roles
from app.routers import smtp_config
from app.routers import syslog_config
from app.routers import search
from app.routers import print as print_router
from app.routers import api_keys
from app.routers import external_api
from app.routers import setup
from app.routers import asset_reviews
from app.routers import notifications
from app.routers import security_zones
from app.routers import conduits
from app.routers import compliance
from app.routers import asset_dependencies
from app.routers import vulnerabilities
from app.routers import sso
from app.routers import asset_capabilities
from app.routers import evidence
from app.routers import network_probes
from app.routers import discovered_devices
from app.routers import tenant_features
from app.crud import sso as crud_sso
from app.setup_system import setup_system
from app.database import SessionLocal
from app.models import Tenant, User, Role

# Setup logging
setup_logging()

app = FastAPI(
    title="Industrace Multi-Tenant",
    description="Configuration Management Database for Industrial Control Systems",
    version="1.0.0",
    openapi_tags=[
        {"name": "assets", "description": "Industrial asset operations"},
        {"name": "external-api", "description": "Secure API for external integrations"},
        {"name": "api-keys", "description": "API Keys management for third parties"},
        {"name": "users", "description": "User management and authentication"},
        {"name": "tenants", "description": "Multi-tenant management"},
    ],
    docs_url="/docs" if settings.EXTERNAL_API_DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.EXTERNAL_API_DOCS_ENABLED else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
# This ensures security headers are present even if nginx is bypassed
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(tenants.router, tags=["tenants"])
app.include_router(suppliers.router, tags=["suppliers"])
app.include_router(manufacturers.router, tags=["manufacturers"])
app.include_router(locations.router, tags=["locations"])
app.include_router(areas.router, tags=["areas"])
app.include_router(assets.router, tags=["assets"])
app.include_router(asset_reviews.router, tags=["asset_reviews"])
app.include_router(notifications.router, tags=["notifications"])
app.include_router(security_zones.router, tags=["security_zones"])
app.include_router(conduits.router, tags=["conduits"])
app.include_router(compliance.router, tags=["compliance"])
app.include_router(asset_dependencies.router, tags=["asset_dependencies"])
app.include_router(vulnerabilities.router, tags=["vulnerabilities"])
app.include_router(asset_capabilities.router, tags=["asset-capabilities"])
app.include_router(evidence.router, tags=["evidence"])
app.include_router(sso.router, tags=["sso"])
app.include_router(network_probes.router, tags=["network-probes"])
app.include_router(discovered_devices.router, tags=["discovered-devices"])
app.include_router(asset_photos.router, tags=["asset_photo"])
app.include_router(asset_documents.router, tags=["asset_document"])
app.include_router(asset_types.router, tags=["asset_type"])
app.include_router(sites.router, tags=["sites"])
app.include_router(asset_interfaces.router, tags=["asset_interfaces"])
app.include_router(asset_connections.router, tags=["asset_connection"])
app.include_router(global_connections.router, tags=["connections"])
app.include_router(locations_floormap.router, tags=["locations_floormap"])
app.include_router(users.router, tags=["users"])
app.include_router(dashboards.router, tags=["dashboards"])
app.include_router(pcap.router, tags=["pcap"])
app.include_router(asset_statuses.router, tags=["asset_statuses"])
app.include_router(contacts.router, tags=["contacts"])
app.include_router(audit_logs.router)
app.include_router(roles.router, tags=["roles"])
app.include_router(smtp_config.router, tags=["smtp-config"])
app.include_router(syslog_config.router, tags=["syslog-config"])
app.include_router(tenant_features.router, tags=["tenant-features"])
app.include_router(search.router, tags=["search"])
app.include_router(print_router.router, tags=["print"])
app.include_router(api_keys.router, tags=["api-keys"])
if settings.EXTERNAL_API_ENABLED:
    app.include_router(external_api.router, tags=["external-api"])
app.include_router(setup.router, tags=["setup"])

# Performance testing router (solo in development)
if settings.ENVIRONMENT != "production":
    from app.routers import performance_test
    app.include_router(performance_test.router, tags=["performance"])


@app.on_event("startup")
async def startup_event():
    """Initializes the database if empty"""
    try:
        # Check and apply database migrations only if needed
        import subprocess
        import os
        import time
        
        logger.info("Checking database migrations...")
        
        # Wait a bit for database to be ready
        time.sleep(2)
        
        try:
            # Always try to upgrade to head (handles multiple heads with 'heads' command)
            logger.info("Applying database migrations...")
            result = subprocess.run(["alembic", "upgrade", "heads"], check=True, capture_output=True, text=True)
            if result.stdout:
                logger.info(result.stdout)
            logger.info("Database migrations applied successfully!")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error applying database migrations: {e}")
            if e.stderr:
                logger.error(f"Error details: {e.stderr}")
            # Try with single head as fallback (for backward compatibility)
            try:
                logger.info("Attempting to apply migrations with 'head' (single) as fallback...")
                subprocess.run(["alembic", "upgrade", "head"], check=True, capture_output=True, text=True)
                logger.info("Database migrations applied successfully!")
            except subprocess.CalledProcessError as e2:
                logger.error(f"Fallback migration failed: {e2}")
                if e2.stderr:
                    logger.error(f"Error details: {e2.stderr}")
                # Continue anyway, it might be that the migrations are already applied
                logger.warning("Continuing startup despite migration errors (migrations may already be applied)")
        
        # Wait a moment for migrations to fully commit
        time.sleep(1)
        
        db = SessionLocal()
        try:
            # Controlla se esistono tenant, utenti e ruoli
            tenant_count = db.query(Tenant).count()
            user_count = db.query(User).count()
            role_count = db.query(Role).count()
        except Exception as e:
            logger.error(f"Error checking database: {e}")
            db.close()
            return
        
        if tenant_count == 0 and user_count == 0 and role_count == 0:
            logger.info("Empty database detected. Initializing system...")
            setup_system()
            # Credentials are printed by setup_system()
        elif user_count == 0 or role_count == 0:
            logger.info("Partially configured database. Completing initialization...")
            setup_system()
            # Credentials are printed by setup_system()
        else:
            logger.info(f"Database already configured (tenant: {tenant_count}, users: {user_count}, roles: {role_count})")
            # Initialize notification templates if not present (system-wide)
            try:
                from app.models import NotificationTemplate
                from app.init_data.init_notification_templates import init_notification_templates
                template_count = db.query(NotificationTemplate).count()
                if template_count == 0:
                    logger.info("Initializing notification templates...")
                    init_notification_templates(db)
                    logger.info("Notification templates initialized")
            except Exception as e:
                logger.error(f"Notification templates initialization failed: {e}")
            
            # Initialize ISA/IEC 62443 Security Requirements if not present (system-wide)
            try:
                from app.models import SecurityRequirement
                from app.init_data.init_security_requirements import init_security_requirements
                req_count = db.query(SecurityRequirement).count()
                if req_count == 0:
                    logger.info("Initializing ISA/IEC 62443 Security Requirements...")
                    created = init_security_requirements(db)
                    logger.info(f"ISA/IEC 62443 Security Requirements initialized ({created} created)")
                else:
                    logger.debug(f"ISA/IEC 62443 Security Requirements already exist ({req_count} found)")
                    missing_sr = (
                        db.query(SecurityRequirement)
                        .filter(SecurityRequirement.requirement_id == "SR 2.13")
                        .first()
                    )
                    if not missing_sr:
                        logger.info("Syncing ISA/IEC 62443 Security Requirements catalog...")
                        init_security_requirements(db)
            except Exception as e:
                logger.error(f"Security Requirements initialization failed: {e}", exc_info=True)
            
            # Initialize ISA/IEC 62443 Security Capabilities if not present (system-wide)
            try:
                from app.models.security_capability import SecurityCapability
                from app.init_data.init_security_capabilities import init_security_capabilities
                cap_count = db.query(SecurityCapability).count()
                if cap_count == 0:
                    logger.info("Initializing ISA/IEC 62443 Security Capabilities...")
                    created = init_security_capabilities(db)
                    logger.info(f"ISA/IEC 62443 Security Capabilities initialized ({created} created)")
                else:
                    logger.debug(f"ISA/IEC 62443 Security Capabilities already exist ({cap_count} found)")
            except Exception as e:
                logger.error(f"Security Capabilities initialization failed: {e}", exc_info=True)
            
            # Initialize ISA/IEC 62443 SR-Capability Mappings if not present (system-wide)
            try:
                from app.models.sr_capability import SRCapability
                from app.init_data.init_sr_capability_mappings import init_sr_capability_mappings
                mapping_count = db.query(SRCapability).count()
                if mapping_count == 0:
                    logger.info("Initializing ISA/IEC 62443 SR-Capability Mappings...")
                    created = init_sr_capability_mappings(db)
                    logger.info(f"ISA/IEC 62443 SR-Capability Mappings initialized ({created} created)")
                else:
                    logger.debug(f"ISA/IEC 62443 SR-Capability Mappings already exist ({mapping_count} found)")
                    from app.models.security_requirement import SecurityRequirement
                    from app.init_data.init_sr_capability_mappings import init_sr_capability_mappings
                    if (
                        db.query(SecurityRequirement)
                        .filter(SecurityRequirement.requirement_id == "SR 2.13")
                        .first()
                    ):
                        init_sr_capability_mappings(db)
            except Exception as e:
                logger.error(f"SR-Capability Mappings initialization failed: {e}", exc_info=True)

            try:
                from app.models import RequirementEnhancement, SecurityRequirement
                from app.init_data.init_requirement_enhancements import init_requirement_enhancements
                sr_count = db.query(SecurityRequirement).filter(
                    SecurityRequirement.requirement_category == "SR"
                ).count()
                re_count = db.query(RequirementEnhancement).count()
                if sr_count > 0:
                    created_re = init_requirement_enhancements(db)
                    if created_re:
                        logger.info(f"Requirement Enhancements: {created_re} new rows")
            except Exception as e:
                logger.error(f"Requirement Enhancements initialization failed: {e}", exc_info=True)
            
            # Check if demo data exists and seed if no assets found (first initialization)
            # This ensures demo data is created even in production during first setup
            from app.config import settings
            from app.models import Asset
            asset_count = db.query(Asset).count()
            
            if asset_count == 0:
                try:
                    from app.init_demo_data import seed_demo_data
                    logger.info("No assets found. Seeding demo data...")
                    seed_demo_data()
                    logger.info("Demo data seeding completed successfully!")
                except Exception as e:
                    logger.error(f"Demo data seeding failed: {e}", exc_info=True)
            else:
                logger.info(f"Demo data already exists ({asset_count} assets found)")
        
        db.close()
        
        # Start background tasks for notifications
        try:
            from app.services.background_tasks import BackgroundTaskManager
            BackgroundTaskManager.start()
            logger.info("Background tasks started (email queue processor, asset review checker)")
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error during database initialization: {e}", exc_info=True)
        # Don't block app startup in case of error


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        from app.services.background_tasks import BackgroundTaskManager
        BackgroundTaskManager.stop()
        logger.info("Background tasks stopped")
    except Exception as e:
        logger.error(f"Error stopping background tasks: {e}", exc_info=True)


from app.errors.validation_errors import ValidationError, InvalidVATNumberError, InvalidTaxCodeError, InvalidURLError, InvalidPhoneError, InvalidEmailError, InvalidIPAddressError, InvalidMACAddressError, InvalidVLANError, InvalidImpactValueError, InvalidPurdueLevelError, InvalidRiskScoreError, InvalidBusinessCriticalityError, InvalidRemoteAccessTypeError, InvalidPhysicalAccessEaseError, InvalidTenantSlugError, InvalidPasswordError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, validation_exc: RequestValidationError
):
    # Extract specific error messages
    validation_errors = []
    for error in validation_exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        
        # Handle our custom exceptions
        error_msg = error["msg"]
        
        # Extract the error code from the message
        if "INVALID_VAT_NUMBER" in error_msg:
            error_code = "INVALID_VAT_NUMBER"
        elif "INVALID_TAX_CODE" in error_msg:
            error_code = "INVALID_TAX_CODE"
        elif "INVALID_URL" in error_msg:
            error_code = "INVALID_URL"
        elif "INVALID_PHONE" in error_msg:
            error_code = "INVALID_PHONE"
        elif "INVALID_EMAIL" in error_msg:
            error_code = "INVALID_EMAIL"
        elif "INVALID_IP_ADDRESS" in error_msg:
            error_code = "INVALID_IP_ADDRESS"
        elif "INVALID_MAC_ADDRESS" in error_msg:
            error_code = "INVALID_MAC_ADDRESS"
        elif "INVALID_SERIAL_NUMBER" in error_msg:
            error_code = "INVALID_SERIAL_NUMBER"
        elif "INVALID_DATE" in error_msg:
            error_code = "INVALID_DATE"
        elif "INVALID_TIME" in error_msg:
            error_code = "INVALID_TIME"
        elif "INVALID_PORT" in error_msg:
            error_code = "INVALID_PORT"
        elif "INVALID_VLAN" in error_msg:
            error_code = "INVALID_VLAN"
        elif "INVALID_SUBNET_MASK" in error_msg:
            error_code = "INVALID_SUBNET_MASK"
        elif "INVALID_DEFAULT_GATEWAY" in error_msg:
            error_code = "INVALID_DEFAULT_GATEWAY"
        elif "INVALID_IMPACT_VALUE" in error_msg:
            error_code = "INVALID_IMPACT_VALUE"
        elif "INVALID_PURDUE_LEVEL" in error_msg:
            error_code = "INVALID_PURDUE_LEVEL"
        elif "INVALID_RISK_SCORE" in error_msg:
            error_code = "INVALID_RISK_SCORE"
        elif "INVALID_BUSINESS_CRITICALITY" in error_msg:
            error_code = "INVALID_BUSINESS_CRITICALITY"
        elif "INVALID_REMOTE_ACCESS_TYPE" in error_msg:
            error_code = "INVALID_REMOTE_ACCESS_TYPE"
        elif "INVALID_PHYSICAL_ACCESS_EASE" in error_msg:
            error_code = "INVALID_PHYSICAL_ACCESS_EASE"
        elif "INVALID_TENANT_SLUG" in error_msg:
            error_code = "INVALID_TENANT_SLUG"
        elif "INVALID_PASSWORD" in error_msg:
            error_code = "INVALID_PASSWORD"
        else:
            error_code = "VALIDATION_ERROR"
        
        validation_errors.append({
            "field": field,
            "error_code": error_code,
            "type": error["type"]
        })
    
    # Return the validation error details
    # Add CORS headers to allow frontend to read the response
    cors_headers = get_cors_headers(request)
    
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR", 
            "detail": "Invalid input data",
            "validation_errors": validation_errors
        },
        headers=cors_headers
    )


@app.exception_handler(ValidationError)
async def custom_validation_exception_handler(
    request: Request, validation_exc: ValidationError
):
    # Return the custom validation error
    # Use configured origins instead of "*" for security
    cors_headers = get_cors_headers(request)
    
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "detail": "Invalid input data",
            "validation_errors": [{
                "field": validation_exc.field,
                "error_code": validation_exc.error_code,
                "type": "validation_error"
            }]
        },
        headers=cors_headers
    )


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Industrace API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.post("/admin/seed-demo-data")
def seed_demo_data_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Force seed demo data (development only)"""
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=403, detail="Demo data seeding only available in development")
    
    if current_user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Only admins can seed demo data")
    
    try:
        from app.init_demo_data import seed_demo_data
        seed_demo_data()
        return {"message": "Demo data seeded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo data seeding failed: {str(e)}")


# Auth endpoints
@app.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    request: Request = None,
):
    # Rate limiting to prevent brute force attacks
    # Uses stricter limit for login (10/minute by default)
    if not check_rate_limit_strict(request, settings.RATE_LIMIT_STRICT):
        log_rate_limit_exceeded(f"ip:{request.client.host if request.client else 'unknown'}", settings.RATE_LIMIT_STRICT, request)
        raise ErrorCodeException(
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            detail="Troppi tentativi di login. Riprova più tardi."
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        log_failed_login(email, request, "USER_NOT_FOUND")
        raise ErrorCodeException(status_code=401, error_code="INVALID_CREDENTIALS")
    
    # Check if user is deleted
    if user.deleted_at is not None:
        log_failed_login(email, request, "USER_DELETED")
        raise ErrorCodeException(status_code=401, error_code="INVALID_CREDENTIALS")
    
    # Check if user has password (SSO-only users cannot login with password)
    if not user.password_hash:
        # Check if SSO is configured and enabled for this tenant
        sso_config = crud_sso.get_sso_config(db, user.tenant_id)
        if sso_config and sso_config.enabled:
            log_failed_login(email, request, "SSO_REQUIRED")
            raise ErrorCodeException(
                status_code=401,
                error_code="SSO_REQUIRED",
                detail=f"This user can only login via SSO. Please use SSO authentication."
            )
        else:
            log_failed_login(email, request, "SSO_NOT_CONFIGURED")
            raise ErrorCodeException(
                status_code=401,
                error_code="INVALID_CREDENTIALS",
                detail="This user can only login via SSO, but SSO is not configured"
            )
    
    if not verify_password(password, user.password_hash):
        log_failed_login(email, request, "INVALID_PASSWORD")
        
        # Increment failed login attempts
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        # Lock account if max attempts exceeded
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            db.commit()
            raise ErrorCodeException(
                status_code=403,
                error_code="ACCOUNT_LOCKED",
                detail=f"Account locked due to too many failed login attempts. Try again after {user.locked_until.isoformat()}."
            )
        else:
            db.commit()
            raise ErrorCodeException(status_code=401, error_code="INVALID_CREDENTIALS")
    
    # Check if user is active
    if not user.is_active:
        log_failed_login(email, request, "USER_INACTIVE")
        raise ErrorCodeException(status_code=401, error_code="INVALID_CREDENTIALS")
    
    # Check account lockout
    if user.locked_until and user.locked_until > datetime.utcnow():
        log_failed_login(email, request, "ACCOUNT_LOCKED")
        raise ErrorCodeException(
            status_code=403,
            error_code="ACCOUNT_LOCKED",
            detail=f"Account locked until {user.locked_until.isoformat()}. Please try again later."
        )
    
    # Check if password change is required
    if user.password_change_required:
        log_failed_login(email, request, "PASSWORD_CHANGE_REQUIRED")
        raise ErrorCodeException(
            status_code=403,
            error_code="PASSWORD_CHANGE_REQUIRED"
        )
    
    # Reset failed attempts and lockout on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "tenant_id": str(user.tenant_id)},
        expires_delta=access_token_expires,
    )

    # Security logging for successful login
    log_successful_login(str(user.id), str(user.tenant_id), user.email, request)
    
    # Audit log for login
    ip_address = request.client.host if request and request.client else None
    create_audit_log(
        db=db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        action="login",
        entity="User",
        entity_id=user.id,
        ip_address=ip_address,
        commit=True,
        language=resolve_audit_language(user, request),
    )

    response = JSONResponse(
        content={"access_token": access_token, "token_type": "bearer"}
    )
    # Add rate limit headers with strict limit for login
    add_rate_limit_headers_strict(response, request, settings.RATE_LIMIT_STRICT)
    # Secure cookie for frontend
    response.set_cookie(
        key="access_token_cookie",
        value=access_token,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite=settings.SAME_SITE_COOKIES,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@app.post("/refresh")
async def refresh_token(
    access_token_cookie: Optional[str] = Cookie(None), db: Session = Depends(get_db)
):
    if not access_token_cookie:
        raise ErrorCodeException(status_code=401, error_code="UNEXISTENT_TOKEN")

    try:
        payload = jwt.decode(
            access_token_cookie,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")

        # Verify that the token is of the correct type
        token_type = payload.get("type")
        if token_type != "access":
            raise ErrorCodeException(status_code=401, error_code="INVALID_TOKEN_TYPE")

        if user_id is None or tenant_id is None:
            raise ErrorCodeException(status_code=401, error_code="INVALID_TOKEN")
    except ExpiredSignatureError:
        raise ErrorCodeException(status_code=401, error_code="EXPIRED_TOKEN")
    except JWTError:
        raise ErrorCodeException(status_code=401, error_code="INVALID_TOKEN")

    new_token = create_access_token(
        data={"sub": user_id, "tenant_id": tenant_id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response = JSONResponse(
        content={
            "msg": "Token renewed",
            "access_token": new_token,
            "token_type": "bearer",
        }
    )
    response.set_cookie(
        key="access_token_cookie",
        value=new_token,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite=settings.SAME_SITE_COOKIES,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@app.post("/logout")
async def logout(
    response: JSONResponse, 
    db: Session = Depends(get_db), 
    request: Request = None,
    access_token_cookie: Optional[str] = Cookie(None)
):
    # Delete cookie with same settings as when it was created
    # This ensures it's properly deleted regardless of cookie settings
    response.delete_cookie(
        key="access_token_cookie",
        path="/",
        domain=None,  # Don't specify domain to match cookie creation
        secure=settings.SECURE_COOKIES,
        samesite=settings.SAME_SITE_COOKIES,
        httponly=True
    )
    
    # Try to get current user for audit log, but don't fail if token is invalid
    current_user = None
    ip_address = request.client.host if request and request.client else None
    
    if access_token_cookie:
        try:
            # Decode token manually for logout audit
            payload = jwt.decode(
                access_token_cookie,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
            )
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            
            if user_id:
                # Get user from database
                current_user = db.query(User).filter(User.id == user_id).first()
        except (JWTError, ExpiredSignatureError):
            # Token is invalid or expired, but we still want to log the logout attempt
            pass
    
    # Audit log for logout
    if current_user:
        create_audit_log(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="logout",
            entity="User",
            entity_id=current_user.id,
            ip_address=ip_address,
            commit=True,
            language=resolve_audit_language(current_user, request),
        )
    else:
        # For anonymous logout, we can't create audit log since user_id is required
        # Just log to console for debugging
        logger.info(f"Anonymous logout attempt from IP: {ip_address}")
    
    return {"msg": "Logout successful"}


@app.exception_handler(ErrorCodeException)
async def error_code_exception_handler(request: Request, exc: ErrorCodeException):
    # Use the translations if available
    from app.errors.translations import messages
    
    # Try to determine the language from the request headers
    language = "en"  # default
    try:
        # Use the Accept-Language header to determine language
        accept_language = request.headers.get("accept-language", "en")
        if "it" in accept_language.lower():
            language = "it"
    except Exception:
        # If header parsing fails, use default language
        pass
    
    # Get the translated message (custom detail overrides catalog)
    translated_message = exc.message_detail or messages.get(language, {}).get(
        exc.error_code, exc.error_code
    )
    
    # Add CORS headers to allow frontend to read the response
    cors_headers = get_cors_headers(request)
    
    return JSONResponse(
        status_code=exc.status_code, 
        content={"error_code": exc.error_code, "detail": translated_message},
        headers=cors_headers
    )


# Configure base logging
logging.basicConfig(level=logging.ERROR)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log the error for debugging
    logging.error(f"Error 500 on {request.url}: {exc}", exc_info=True)
    
    # Add CORS headers to allow frontend to read the response
    cors_headers = get_cors_headers(request)
    
    # Handle JSON serialization errors specifically
    if isinstance(exc, ValueError) and "Out of range float values are not JSON compliant" in str(exc):
        logger.error("JSON serialization error with inf/NaN values detected")
        return JSONResponse(
            status_code=500,
            content={"error_code": "SERIALIZATION_ERROR", "detail": "Data serialization error - invalid numeric values detected"},
            headers=cors_headers
        )
    
    # For the user, return only a generic message
    return JSONResponse(
        status_code=500, 
        content={"error_code": "INTERNAL_ERROR", "detail": "Internal server error"},
        headers=cors_headers
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
