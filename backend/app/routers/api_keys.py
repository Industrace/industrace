# backend/routers/api_keys.py
import uuid
from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas.api_key import ApiKeyCreate, ApiKeyRead, ApiKeyUpdate, ApiKeyResponse
from app.services.auth import get_current_user
from app.services.rbac import require_section_access
from app.services.audit_decorator import audit_log_action
from app.crud import api_keys as crud_api_keys
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
import json

router = APIRouter(
    prefix="/api-keys",
    tags=["api-keys"],
    dependencies=[Depends(require_section_access("api_keys"))],
)


@router.post("", response_model=ApiKeyResponse)
@audit_log_action("create", "ApiKey")
def create_api_key(
    api_key_data: ApiKeyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new API Key for external integrations"""
    try:
        api_key, raw_key = crud_api_keys.create_api_key(
            db, api_key_data, current_user.tenant_id, current_user.id
        )

        # Prepare the response with the raw key (only for creation)
        response_data = {
            "id": api_key.id,
            "name": api_key.name,
            "key": raw_key,  # Raw key only for creation
            "scopes": json.loads(api_key.scopes),
            "rate_limit": api_key.rate_limit,
            "expires_at": api_key.expires_at,
            "created_at": api_key.created_at,
        }

        return ApiKeyResponse(**response_data)

    except Exception as e:
        raise ErrorCodeException(
            status_code=500,
            error_code=ErrorCode.INVALID_USER_CREATION,  # Reuse for now
        )


@router.get("", response_model=List[ApiKeyRead])
def list_api_keys(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all API Keys for the tenant"""
    api_keys = crud_api_keys.get_api_keys_by_tenant(
        db, current_user.tenant_id, skip, limit
    )
    return api_keys


@router.get("/{api_key_id}", response_model=ApiKeyRead)
def get_api_key(
    api_key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the details of an API Key"""
    api_key = crud_api_keys.get_api_key(db, api_key_id, current_user.tenant_id)
    if not api_key:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.USER_NOT_FOUND)
    return api_key


@router.put("/{api_key_id}", response_model=ApiKeyRead)
@audit_log_action("update", "ApiKey")
def update_api_key(
    api_key_id: uuid.UUID,
    api_key_update: ApiKeyUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an API Key"""
    api_key = crud_api_keys.update_api_key(
        db, api_key_id, current_user.tenant_id, api_key_update
    )
    if not api_key:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.USER_NOT_FOUND)
    return api_key


@router.delete("/{api_key_id}")
@audit_log_action("delete", "ApiKey")
def delete_api_key(
    api_key_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an API Key"""
    success = crud_api_keys.delete_api_key(db, api_key_id, current_user.tenant_id)
    if not success:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.USER_NOT_FOUND)
    return {"message": "API Key deleted successfully"}


@router.patch("/{api_key_id}/deactivate")
@audit_log_action("deactivate", "ApiKey")
def deactivate_api_key(
    api_key_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deactivate an API Key"""
    api_key = crud_api_keys.deactivate_api_key(db, api_key_id, current_user.tenant_id)
    if not api_key:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.USER_NOT_FOUND)
    return {"message": "API Key deactivated successfully"}


@router.patch("/{api_key_id}/activate")
@audit_log_action("activate", "ApiKey")
def activate_api_key(
    api_key_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reactivate an API Key"""
    api_key = crud_api_keys.activate_api_key(db, api_key_id, current_user.tenant_id)
    if not api_key:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.USER_NOT_FOUND)
    return {"message": "API Key reactivated successfully"}


@router.post("/cleanup-expired")
def cleanup_expired_api_keys(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Clean up all expired API Keys"""
    count = crud_api_keys.cleanup_expired_api_keys(db)
    return {"message": f"Cleanup completed", "deactivated_count": count}
