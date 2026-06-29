import uuid
from typing import List

from fastapi import APIRouter, Depends, Request, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.user import UserCreate, UserUpdate, UserRead, PasswordChange
from app.services.auth import get_current_user, get_password_hash
from app.services.audit_decorator import audit_log_action
from app.services.rbac import require_permission, require_section_access
from app.crud import users as crud_users
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from sqlalchemy.exc import IntegrityError
import secrets

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[
        Depends(
            require_section_access(
                "users",
                skip_path_contains=("/users/me", "/users/reset-password"),
            )
        )
    ],
)


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user profile with tenant information"""
    # Refresh user to ensure relationships are loaded
    from sqlalchemy.orm import joinedload
    user = db.query(User).options(
        joinedload(User.tenant),
        joinedload(User.role)
    ).filter(User.id == current_user.id).first()
    
    if not user:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.USER_NOT_FOUND)

    from app.services.tenant_features import get_tenant_features
    tenant_features = get_tenant_features(user.tenant.settings if user.tenant else None)
    
    # Create response dict with full_name
    user_dict = {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "name": user.name,
        "full_name": user.name,  # Set full_name from name
        "role_id": user.role_id,
        "role": user.role,
        "tenant": user.tenant,
        "is_active": user.is_active,
        "notifications_enabled": user.notifications_enabled,
        "created_at": user.created_at,
        "last_login": user.last_login,
        "password_change_required": user.password_change_required or False,
        "features": tenant_features,
    }
    
    return user_dict


class NotificationPreferenceUpdate(BaseModel):
    notifications_enabled: bool


@router.patch("/me/notifications", response_model=UserRead)
@audit_log_action("update", "User", model_class=User)
def update_notifications_preference(
    preference: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user's global notification preference"""
    import logging
    logger = logging.getLogger(__name__)
    
    old_value = current_user.notifications_enabled
    current_user.notifications_enabled = preference.notifications_enabled
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"Updated notifications_enabled for user {current_user.id}: {old_value} -> {current_user.notifications_enabled}")
    
    return current_user


@router.post("", response_model=UserRead)
@audit_log_action("create", "User", model_class=User)
def create_user(
    user: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.schemas.validators import validate_password_strength
    
    try:
        # Validate password strength
        # Allow weak passwords only if password_change_required is True
        allow_weak = user.password_change_required if hasattr(user, 'password_change_required') else False
        validate_password_strength(user.password, allow_weak=allow_weak)
        
        hashed_password = get_password_hash(user.password)
        db_user = User(
            tenant_id=current_user.tenant_id,
            email=user.email,
            password_hash=hashed_password,
            name=user.name,
            role_id=user.role_id,
            is_active=user.is_active if user.is_active is not None else True,
            password_change_required=user.password_change_required if hasattr(user, 'password_change_required') else False,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_USER_CREATION,
        )
    except Exception as e:
        db.rollback()
        raise ErrorCodeException(
            status_code=500,
            error_code=ErrorCode.INVALID_USER_CREATION,
        )


@router.delete("/{user_id}")
@audit_log_action("delete", "User", model_class=User)
def delete_user(
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = crud_users.get_user(db, user_id, current_user.tenant_id)
    if not user:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.USER_NOT_FOUND)
    crud_users.delete_user(db, user)
    return None


@router.put("/{user_id}", response_model=UserRead)
@audit_log_action("update", "User", model_class=User)
def update_user(
    user_id: uuid.UUID,
    user: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_user = crud_users.get_user(db, user_id, current_user.tenant_id)
    if not db_user:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.USER_NOT_FOUND)
    return crud_users.update_user(db, db_user, user)


@router.get("/{user_id}", response_model=UserRead)
@audit_log_action("get", "User", model_class=User)
def get_user(
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = crud_users.get_user(db, user_id, current_user.tenant_id)
    if not user:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.USER_NOT_FOUND)
    return user


@router.get("", response_model=List[UserRead])
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
):
    return crud_users.get_users(db, current_user.tenant_id, skip=skip, limit=limit)


@router.post("/{user_id}/reset-password")
@audit_log_action("reset_password", "User", model_class=User)
def reset_password(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("reset_user_password", 1)),
):
    user = (
        db.query(User)
        .filter(User.id == user_id, User.tenant_id == current_user.tenant_id)
        .first()
    )
    if not user:
        raise ErrorCodeException(status_code=404, error_code=ErrorCode.USER_NOT_FOUND)
    
    # Generate temporary password
    new_password = secrets.token_urlsafe(10)
    user.password_hash = get_password_hash(new_password)
    db.commit()
    
    # Return the temporary password to the admin
    return {
        "detail": "Password reset successfully",
        "temporary_password": new_password,
        "user_email": user.email
    }


@router.post("/reset-password")
def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allow the user to change their password"""
    from app.services.auth import verify_password, get_password_hash
    from app.schemas.validators import validate_password_strength

    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise ErrorCodeException(
            status_code=400, error_code=ErrorCode.INVALID_CREDENTIALS
        )

    # Validate new password strength (always enforce strong passwords)
    validate_password_strength(password_data.new_password, allow_weak=False)

    # Update password and reset password_change_required flag
    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.password_change_required = False
    db.commit()

    return {"detail": "Password updated successfully"}
