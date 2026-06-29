# backend/crud/users.py
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.models import User
from app.schemas.user import UserCreate, UserUpdate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user(db: Session, user_id: uuid.UUID, tenant_id: uuid.UUID = None) -> Optional[User]:
    """Retrieve a user by ID, optionally filtered by tenant"""
    query = db.query(User).filter(User.id == user_id)
    if tenant_id:
        query = query.filter(User.tenant_id == tenant_id)
    return query.first()


def get_user_by_email(db: Session, email: str, tenant_id: uuid.UUID = None) -> Optional[User]:
    """Retrieve a user by email, optionally filtered by tenant"""
    query = db.query(User).filter(User.email == email)
    if tenant_id:
        query = query.filter(User.tenant_id == tenant_id)
    return query.first()


def get_users(
    db: Session, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[User]:
    """List all users of a tenant with pagination"""
    return (
        db.query(User)
        .filter(User.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_user(db: Session, user: UserCreate, tenant_id: uuid.UUID) -> User:
    """Create a new user"""
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        tenant_id=tenant_id,
        email=user.email,
        name=user.name,
        role_id=user.role_id,
        password_hash=hashed_password,
        is_active=user.is_active,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str, tenant_id: uuid.UUID = None) -> Optional[User]:
    """Authenticate a user"""
    user = get_user_by_email(db, email, tenant_id)
    if not user or not pwd_context.verify(password, user.password_hash):
        return None
    return user


def update_user(db: Session, db_user: User, user_update: UserUpdate) -> Optional[User]:
    """Update an existing user"""
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = pwd_context.hash(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user: User) -> bool:
    """Delete a user"""
    db.delete(user)
    db.commit()
    return True
