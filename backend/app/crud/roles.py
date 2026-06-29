from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict, Any
import uuid
from app.models import Role
from app.schemas.role import RoleCreate, RoleUpdate


def create_role(db: Session, role_in: RoleCreate | Dict[str, Any]) -> Role:
    """Create a new role"""
    if isinstance(role_in, dict):
        role_data = role_in
    else:
        role_data = role_in.model_dump()
    
    role = Role(**role_data)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def get_role(db: Session, role_id: uuid.UUID) -> Optional[Role]:
    """Retrieve a role by ID with parent role loaded"""
    return db.query(Role).options(
        joinedload(Role.parent_role)
    ).filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str, tenant_id: Optional[uuid.UUID] = None) -> Optional[Role]:
    """Retrieve a role by name with parent role loaded"""
    query = db.query(Role).options(
        joinedload(Role.parent_role)
    ).filter(Role.name == name)
    if tenant_id:
        query = query.filter(Role.tenant_id == tenant_id)
    return query.first()


def list_roles(db: Session, skip: int = 0, limit: int = 100, include_inactive: bool = False, tenant_id: Optional[uuid.UUID] = None) -> List[Role]:
    """List all roles with pagination and parent role loaded"""
    query = db.query(Role).options(joinedload(Role.parent_role))
    
    # Filter by tenant if specified
    if tenant_id:
        query = query.filter(Role.tenant_id == tenant_id)
    
    if not include_inactive:
        query = query.filter(Role.is_active == True)
    
    return query.offset(skip).limit(limit).all()


def get_role_with_effective_permissions(db: Session, role_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Get role with effective permissions (including inheritance)"""
    role = get_role(db, role_id)
    if not role:
        return None
    
    effective_permissions = role.get_effective_permissions()
    
    return {
        "id": role.id,
        "tenant_id": role.tenant_id,
        "name": role.name,
        "description": role.description,
        "permissions": role.permissions,
        "effective_permissions": effective_permissions,
        "is_inheritable": role.is_inheritable,
        "parent_role_id": role.parent_role_id,
        "parent_role_name": role.parent_role.name if role.parent_role else None,
        "is_active": role.is_active,
        "created_at": role.created_at,
        "updated_at": role.updated_at
    }


def list_roles_with_effective_permissions(db: Session, skip: int = 0, limit: int = 100, tenant_id: Optional[uuid.UUID] = None) -> List[Dict[str, Any]]:
    """List all roles with effective permissions"""
    roles = list_roles(db, skip, limit, tenant_id=tenant_id)
    
    result = []
    for role in roles:
        effective_permissions = role.get_effective_permissions()
        
        result.append({
            "id": role.id,
            "tenant_id": role.tenant_id,
            "name": role.name,
            "description": role.description,
            "permissions": role.permissions,
            "effective_permissions": effective_permissions,
            "is_inheritable": role.is_inheritable,
            "parent_role_id": role.parent_role_id,
            "parent_role_name": role.parent_role.name if role.parent_role else None,
            "is_active": role.is_active,
            "created_at": role.created_at,
            "updated_at": role.updated_at
        })
    
    return result


def get_role_hierarchy(db: Session, role_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Get role hierarchy (parent and children)"""
    role = get_role(db, role_id)
    if not role:
        return None
    
    # Get children roles
    children = db.query(Role).filter(Role.parent_role_id == role_id).all()
    
    return {
        "role": {
            "id": role.id,
            "name": role.name,
            "description": role.description
        },
        "parent": {
            "id": role.parent_role.id,
            "name": role.parent_role.name,
            "description": role.parent_role.description
        } if role.parent_role else None,
        "children": [
            {
                "id": child.id,
                "name": child.name,
                "description": child.description
            } for child in children
        ]
    }


def update_role(db: Session, role: Role, update_data: RoleUpdate) -> Role:
    """Update an existing role"""
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(role, key, value)
    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role: Role) -> None:
    """Delete a role"""
    # Check if role has children
    children_count = db.query(Role).filter(Role.parent_role_id == role.id).count()
    if children_count > 0:
        raise ValueError(f"Cannot delete role '{role.name}' because it has {children_count} child roles")
    
    # Check if role is assigned to users
    users_count = len(role.users)
    if users_count > 0:
        raise ValueError(f"Cannot delete role '{role.name}' because it is assigned to {users_count} users")
    
    db.delete(role)
    db.commit()


def get_available_parent_roles(db: Session, exclude_role_id: Optional[uuid.UUID] = None, tenant_id: Optional[uuid.UUID] = None) -> List[Role]:
    """Get available roles that can be used as parent roles"""
    query = db.query(Role).filter(Role.is_active == True)
    
    if tenant_id:
        query = query.filter(Role.tenant_id == tenant_id)
    
    if exclude_role_id:
        query = query.filter(Role.id != exclude_role_id)
    
    return query.all()


def validate_role_hierarchy(db: Session, role_id: Optional[uuid.UUID], parent_role_id: uuid.UUID) -> bool:
    """Validate that setting parent_role_id doesn't create circular references"""
    if role_id and role_id == parent_role_id:
        return False
    
    # Check if the new parent is a descendant of this role
    current_parent_id = parent_role_id
    visited = set()
    
    while current_parent_id:
        if current_parent_id in visited:
            return False  # Circular reference detected
        
        visited.add(current_parent_id)
        parent_role = db.query(Role).filter(Role.id == current_parent_id).first()
        
        if not parent_role:
            break
            
        current_parent_id = parent_role.parent_role_id
    
    return True
