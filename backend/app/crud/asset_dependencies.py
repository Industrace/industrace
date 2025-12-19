# backend/app/crud/asset_dependencies.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid
from app.models.asset_dependency import AssetDependency
from app.models.asset import Asset
from app.schemas.asset_dependency import AssetDependencyCreate, AssetDependencyUpdate


def get_asset_dependency(
    db: Session,
    dependency_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> Optional[AssetDependency]:
    """Get a single asset dependency by ID"""
    return db.query(AssetDependency).filter(
        AssetDependency.id == dependency_id,
        AssetDependency.tenant_id == tenant_id
    ).first()


def get_asset_dependencies(
    db: Session,
    tenant_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    asset_id: Optional[uuid.UUID] = None,
    dependency_type: Optional[str] = None
) -> List[AssetDependency]:
    """Get list of asset dependencies with optional filters"""
    query = db.query(AssetDependency).filter(
        AssetDependency.tenant_id == tenant_id
    )
    
    if asset_id:
        query = query.filter(
            or_(
                AssetDependency.dependent_asset_id == asset_id,
                AssetDependency.dependency_asset_id == asset_id
            )
        )
    
    if dependency_type:
        query = query.filter(AssetDependency.dependency_type == dependency_type)
    
    return query.offset(skip).limit(limit).all()


def get_asset_dependencies_as_dependent(
    db: Session,
    asset_id: uuid.UUID,
    tenant_id: uuid.UUID,
    dependency_type: Optional[str] = None
) -> List[AssetDependency]:
    """Get all dependencies where this asset is the dependent (depends on others)"""
    from sqlalchemy.orm import joinedload
    query = (
        db.query(AssetDependency)
        .options(
            joinedload(AssetDependency.dependent_asset),
            joinedload(AssetDependency.dependency_asset)
        )
        .filter(
            AssetDependency.dependent_asset_id == asset_id,
            AssetDependency.tenant_id == tenant_id
        )
    )
    
    if dependency_type:
        query = query.filter(AssetDependency.dependency_type == dependency_type)
    
    return query.all()


def get_asset_dependencies_as_dependency(
    db: Session,
    asset_id: uuid.UUID,
    tenant_id: uuid.UUID,
    dependency_type: Optional[str] = None
) -> List[AssetDependency]:
    """Get all dependencies where this asset is the dependency (others depend on it)"""
    from sqlalchemy.orm import joinedload
    query = (
        db.query(AssetDependency)
        .options(
            joinedload(AssetDependency.dependent_asset),
            joinedload(AssetDependency.dependency_asset)
        )
        .filter(
            AssetDependency.dependency_asset_id == asset_id,
            AssetDependency.tenant_id == tenant_id
        )
    )
    
    if dependency_type:
        query = query.filter(AssetDependency.dependency_type == dependency_type)
    
    return query.all()


def create_asset_dependency(
    db: Session,
    dependency: AssetDependencyCreate,
    tenant_id: uuid.UUID,
    created_by: Optional[uuid.UUID] = None
) -> AssetDependency:
    """Create a new asset dependency"""
    # Validate that assets exist and belong to tenant
    dependent_asset = db.query(Asset).filter(
        Asset.id == dependency.dependent_asset_id,
        Asset.tenant_id == tenant_id,
        Asset.deleted_at == None
    ).first()
    
    if not dependent_asset:
        raise ValueError(f"Dependent asset {dependency.dependent_asset_id} not found")
    
    dependency_asset = db.query(Asset).filter(
        Asset.id == dependency.dependency_asset_id,
        Asset.tenant_id == tenant_id,
        Asset.deleted_at == None
    ).first()
    
    if not dependency_asset:
        raise ValueError(f"Dependency asset {dependency.dependency_asset_id} not found")
    
    # Check for duplicate
    existing = db.query(AssetDependency).filter(
        AssetDependency.tenant_id == tenant_id,
        AssetDependency.dependent_asset_id == dependency.dependent_asset_id,
        AssetDependency.dependency_asset_id == dependency.dependency_asset_id,
        AssetDependency.dependency_type == dependency.dependency_type
    ).first()
    
    if existing:
        raise ValueError("Dependency already exists")
    
    db_dependency = AssetDependency(
        **dependency.dict(),
        tenant_id=tenant_id,
        created_by=created_by
    )
    db.add(db_dependency)
    db.commit()
    db.refresh(db_dependency)
    return db_dependency


def update_asset_dependency(
    db: Session,
    dependency_id: uuid.UUID,
    dependency_update: AssetDependencyUpdate,
    tenant_id: uuid.UUID
) -> Optional[AssetDependency]:
    """Update an existing asset dependency"""
    db_dependency = get_asset_dependency(db, dependency_id, tenant_id)
    if not db_dependency:
        return None
    
    update_data = dependency_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_dependency, field, value)
    
    db.commit()
    db.refresh(db_dependency)
    return db_dependency


def delete_asset_dependency(
    db: Session,
    dependency_id: uuid.UUID,
    tenant_id: uuid.UUID
) -> bool:
    """Delete an asset dependency"""
    db_dependency = get_asset_dependency(db, dependency_id, tenant_id)
    if not db_dependency:
        return False
    
    db.delete(db_dependency)
    db.commit()
    return True


def get_dependency_chain(
    db: Session,
    asset_id: uuid.UUID,
    tenant_id: uuid.UUID,
    max_depth: int = 10
) -> List[Dict[str, Any]]:
    """
    Get dependency chain starting from an asset.
    Returns list of dependencies in order (breadth-first).
    """
    visited = set()
    queue = [(asset_id, 0, None)]  # (asset_id, depth, dependency_id)
    chain = []
    
    while queue and len(chain) < max_depth * 10:  # Safety limit
        current_asset_id, depth, parent_dep_id = queue.pop(0)
        
        if current_asset_id in visited or depth >= max_depth:
            continue
        
        visited.add(current_asset_id)
        
        # Get dependencies where this asset depends on others
        dependencies = get_asset_dependencies_as_dependent(
            db, current_asset_id, tenant_id
        )
        
        for dep in dependencies:
            if dep.dependency_asset_id not in visited:
                chain.append({
                    "dependency_id": str(dep.id),
                    "from_asset_id": str(dep.dependent_asset_id),
                    "to_asset_id": str(dep.dependency_asset_id),
                    "dependency_type": dep.dependency_type,
                    "criticality": dep.criticality,
                    "depth": depth + 1,
                    "parent_dependency_id": str(parent_dep_id) if parent_dep_id else None
                })
                queue.append((dep.dependency_asset_id, depth + 1, dep.id))
    
    return chain


def get_reverse_dependency_chain(
    db: Session,
    asset_id: uuid.UUID,
    tenant_id: uuid.UUID,
    max_depth: int = 10
) -> List[Dict[str, Any]]:
    """
    Get reverse dependency chain (what depends on this asset).
    Returns list of dependencies in order (breadth-first).
    """
    visited = set()
    queue = [(asset_id, 0, None)]  # (asset_id, depth, dependency_id)
    chain = []
    
    while queue and len(chain) < max_depth * 10:  # Safety limit
        current_asset_id, depth, parent_dep_id = queue.pop(0)
        
        if current_asset_id in visited or depth >= max_depth:
            continue
        
        visited.add(current_asset_id)
        
        # Get dependencies where others depend on this asset
        dependencies = get_asset_dependencies_as_dependency(
            db, current_asset_id, tenant_id
        )
        
        for dep in dependencies:
            if dep.dependent_asset_id not in visited:
                chain.append({
                    "dependency_id": str(dep.id),
                    "from_asset_id": str(dep.dependent_asset_id),
                    "to_asset_id": str(dep.dependency_asset_id),
                    "dependency_type": dep.dependency_type,
                    "criticality": dep.criticality,
                    "depth": depth + 1,
                    "parent_dependency_id": str(parent_dep_id) if parent_dep_id else None
                })
                queue.append((dep.dependent_asset_id, depth + 1, dep.id))
    
    return chain

