# backend/routers/external_api.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asset, User
from app.schemas import AssetRead as AssetSchema
from app.services.api_auth import (
    get_api_key_user,
    require_read_scope,
    require_write_scope,
)
from app.services.rate_limiter import add_rate_limit_headers, check_rate_limit
from app.services.security_logging import log_api_key_usage
from app.crud import assets as crud_assets
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode

router = APIRouter(
    prefix="/external/v1",
    tags=["external-api"],
)


# Middleware to add rate limiting headers
async def add_rate_limit_headers_middleware(
    request: Request, response: Response, api_key=None
):
    """Middleware to add rate limiting headers"""
    return add_rate_limit_headers(response, request, api_key)


# Endpoint to get information about the API
@router.get("/info")
async def get_api_info():
    """Information about the external API"""
    return {
        "name": "Industrace External API",
        "version": "1.0.0",
        "description": "Secure API for external integrations",
        "authentication": "API Key (X-API-Key header)",
        "rate_limiting": "Configurable per API Key",
        "documentation": "/docs",
    }


# Endpoint to verify the API Key status
@router.get("/auth/verify")
async def verify_api_key(api_key=Depends(require_read_scope)):
    """Verify the validity of the API Key"""
    return {
        "valid": True,
        "api_key_id": str(api_key.id),
        "name": api_key.name,
        "scopes": api_key.scopes,
        "rate_limit": api_key.rate_limit,
        "expires_at": api_key.expires_at,
    }


# Endpoint to get assets (read-only)
@router.get("/assets", response_model=List[AssetSchema])
async def list_assets_external(
    skip: int = 0,
    limit: int = 100,
    status_id: Optional[uuid.UUID] = None,
    site_id: Optional[uuid.UUID] = None,
    api_key=Depends(require_read_scope),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """List of tenant assets (external API)"""
    # Log API key usage
    log_api_key_usage(str(api_key.id), str(api_key.tenant_id), "/assets", request)
    
    # Verify rate limit
    if not check_rate_limit(request, api_key):
        raise ErrorCodeException(
            status_code=429, error_code=ErrorCode.RATE_LIMIT_EXCEEDED
        )

    # Filter by tenant of the API Key
    query = db.query(Asset).filter(
        Asset.tenant_id == api_key.tenant_id, Asset.deleted_at == None
    )

    if status_id:
        query = query.filter(Asset.status_id == status_id)
    if site_id:
        query = query.filter(Asset.site_id == site_id)

    assets = query.offset(skip).limit(limit).all()
    return assets


# Endpoint to get a specific asset
@router.get("/assets/{asset_id}", response_model=AssetSchema)
async def get_asset_external(
    asset_id: uuid.UUID,
    api_key=Depends(require_read_scope),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """Get a specific asset (external API)"""
    # Verify rate limit
    if not check_rate_limit(request, api_key):
        raise ErrorCodeException(
            status_code=429, error_code=ErrorCode.RATE_LIMIT_EXCEEDED
        )

    asset = crud_assets.get_asset(db, asset_id)
    if not asset or asset.tenant_id != api_key.tenant_id:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ASSET_NOT_FOUND)

    return asset


# Endpoint to get asset statistics
@router.get("/assets/stats/overview")
async def get_assets_stats(
    api_key=Depends(require_read_scope),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """General asset statistics (external API)"""
    # Verify rate limit
    if not check_rate_limit(request, api_key):
        raise ErrorCodeException(
            status_code=429, error_code=ErrorCode.RATE_LIMIT_EXCEEDED
        )

    from sqlalchemy import func

    # Count total assets
    total_assets = (
        db.query(func.count(Asset.id))
        .filter(Asset.tenant_id == api_key.tenant_id, Asset.deleted_at == None)
        .scalar()
    )

    # Count by status
    status_counts = (
        db.query(Asset.status_id, func.count(Asset.id))
        .filter(Asset.tenant_id == api_key.tenant_id, Asset.deleted_at == None)
        .group_by(Asset.status_id)
        .all()
    )

    # Count by business criticality
    criticality_counts = (
        db.query(Asset.business_criticality, func.count(Asset.id))
        .filter(Asset.tenant_id == api_key.tenant_id, Asset.deleted_at == None)
        .group_by(Asset.business_criticality)
        .all()
    )

    return {
        "total_assets": total_assets,
        "by_status": dict(status_counts),
        "by_criticality": dict(criticality_counts),
        "tenant_id": str(api_key.tenant_id),
    }


# Endpoint to get high risk assets
@router.get("/assets/risk/high")
async def get_high_risk_assets(
    limit: int = 10,
    api_key=Depends(require_read_scope),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """Get high risk assets (external API)"""
    # Verify rate limit
    if not check_rate_limit(request, api_key):
        raise ErrorCodeException(
            status_code=429, error_code=ErrorCode.RATE_LIMIT_EXCEEDED
        )

    high_risk_assets = (
        db.query(Asset)
        .filter(
            Asset.tenant_id == api_key.tenant_id,
            Asset.deleted_at == None,
            Asset.risk_score >= 7,
        )
        .order_by(Asset.risk_score.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(asset.id),
            "name": asset.name,
            "risk_score": asset.risk_score,
            "business_criticality": asset.business_criticality,
            "site_name": asset.site.name if asset.site else None,
        }
        for asset in high_risk_assets
    ]


# Endpoint to check health
@router.get("/health")
async def health_check():
    """Health check of the external API"""
    return {
        "status": "healthy",
        "service": "industrace-external-api",
        "version": "1.0.0",
    }
