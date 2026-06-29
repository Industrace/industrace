import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models import Role, User
from app.schemas.role import RoleRead, RoleCreate, RoleUpdate
from app.services.auth import get_current_user
from app.services.rbac import require_permission
from app.services.audit_decorator import audit_log_action
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.crud import roles as crud_roles

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
)


@router.get("", response_model=List[Dict[str, Any]])
def list_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("roles", 1)),
):
    """List all roles with effective permissions"""
    return crud_roles.list_roles_with_effective_permissions(db, skip=skip, limit=limit, tenant_id=current_user.tenant_id)


@router.get("/{role_id}", response_model=Dict[str, Any])
def get_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("roles", 1)),
):
    """Get role with effective permissions"""
    role = crud_roles.get_role_with_effective_permissions(db, role_id)
    if not role:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ROLE_NOT_FOUND)
    # Verify tenant access
    if role.get("tenant_id") != current_user.tenant_id:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ROLE_NOT_FOUND)
    return role


@router.get("/{role_id}/hierarchy", response_model=Dict[str, Any])
def get_role_hierarchy(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("roles", 1)),
):
    """Get role hierarchy (parent and children)"""
    hierarchy = crud_roles.get_role_hierarchy(db, role_id)
    if not hierarchy:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ROLE_NOT_FOUND)
    return hierarchy


@router.get("/available/parents", response_model=List[RoleRead])
def get_available_parent_roles(
    exclude_role_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("roles", 1)),
):
    """Get available roles that can be used as parent roles"""
    return crud_roles.get_available_parent_roles(db, exclude_role_id, tenant_id=current_user.tenant_id)


@router.post("", response_model=RoleRead, status_code=201)
@audit_log_action("create", "Role", model_class=Role)
def create_role(
    role_in: RoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("roles", 2)),
):
    # Check if a role with the same name already exists in the same tenant
    existing_role = crud_roles.get_role_by_name(db, role_in.name, tenant_id=current_user.tenant_id)
    if existing_role:
        raise ErrorCodeException(
            status_code=400, error_code=ErrorCode.INVALID_ROLE_CREATION
        )

    # Validate parent role hierarchy if specified
    if role_in.parent_role_id:
        if not crud_roles.validate_role_hierarchy(db, role_id=None, parent_role_id=role_in.parent_role_id):
            raise ErrorCodeException(
                status_code=400, error_code=ErrorCode.INVALID_ROLE_HIERARCHY
            )

    # Add tenant_id to role data
    role_data = role_in.model_dump()
    role_data["tenant_id"] = current_user.tenant_id
    return crud_roles.create_role(db, role_data)


@router.put("/{role_id}", response_model=RoleRead)
@audit_log_action("update", "Role", model_class=Role)
def update_role(
    role_id: uuid.UUID,
    role_in: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("roles", 2)),
):
    role = crud_roles.get_role(db, role_id)
    if not role:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ROLE_NOT_FOUND)
    
    # Verify tenant access
    if role.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ROLE_NOT_FOUND)

    # Validate parent role hierarchy if specified
    if role_in.parent_role_id:
        if not crud_roles.validate_role_hierarchy(db, role_id, role_in.parent_role_id):
            raise ErrorCodeException(
                status_code=400, error_code=ErrorCode.INVALID_ROLE_HIERARCHY
            )

    return crud_roles.update_role(db, role, role_in)


@router.delete("/{role_id}", status_code=204)
@audit_log_action("delete", "Role", model_class=Role)
def delete_role(
    role_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("roles", 3)),
):
    role = crud_roles.get_role(db, role_id)
    if not role:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ROLE_NOT_FOUND)
    
    # Verify tenant access
    if role.tenant_id != current_user.tenant_id:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.ROLE_NOT_FOUND)

    try:
        crud_roles.delete_role(db, role)
    except ValueError as e:
        raise ErrorCodeException(
            status_code=400, error_code=ErrorCode.ROLE_DELETE_CONSTRAINT
        )
    
    return


@router.get("/test/permissions")
def test_user_permissions(current_user: User = Depends(get_current_user)):
    """Test endpoint to verify the user's permissions"""
    effective_permissions = {}
    if current_user.role:
        effective_permissions = current_user.role.get_effective_permissions()
    
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "role_name": current_user.role.name if current_user.role else None,
        "direct_permissions": current_user.role.permissions if current_user.role else {},
        "effective_permissions": effective_permissions,
        "is_admin": current_user.role.name == "admin" if current_user.role else False,
    }
