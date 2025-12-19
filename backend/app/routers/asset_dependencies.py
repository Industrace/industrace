# backend/app/routers/asset_dependencies.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Asset
from app.services.auth import get_current_user
from app.services.audit_decorator import audit_log_action
from app import crud
from app.crud import asset_dependencies as crud_dependencies
from app.schemas.asset_dependency import (
    AssetDependencyCreate,
    AssetDependencyUpdate,
    AssetDependencyRead,
    AssetDependencyWithAssets,
    ImpactAnalysis,
    DependencyChain
)
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.services.risk_propagation import RiskPropagationService
from app.services.connection_dependency_analyzer import ConnectionDependencyAnalyzer

router = APIRouter(
    prefix="/asset-dependencies",
    tags=["asset_dependencies"],
)


@router.get("", response_model=List[AssetDependencyRead])
def list_asset_dependencies(
    asset_id: Optional[uuid.UUID] = Query(None, description="Filter by asset ID (dependent or dependency)"),
    dependency_type: Optional[str] = Query(None, description="Filter by dependency type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all asset dependencies with optional filters"""
    dependencies = crud_dependencies.get_asset_dependencies(
        db,
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit,
        asset_id=asset_id,
        dependency_type=dependency_type
    )
    return dependencies


@router.get("/{dependency_id}", response_model=AssetDependencyRead)
def get_asset_dependency(
    dependency_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single asset dependency by ID"""
    dependency = crud_dependencies.get_asset_dependency(
        db, dependency_id, current_user.tenant_id
    )
    if not dependency:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="Asset dependency not found"
        )
    return dependency


@router.post("", response_model=AssetDependencyRead, status_code=201)
@audit_log_action("create", "AssetDependency")
def create_asset_dependency(
    dependency: AssetDependencyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new asset dependency"""
    try:
        db_dependency = crud_dependencies.create_asset_dependency(
            db,
            dependency,
            tenant_id=current_user.tenant_id,
            created_by=current_user.id
        )
        # Invalida la cache del rischio per l'asset dipendente
        from app.services.risk_cache import risk_cache
        risk_cache.invalidate_asset(str(current_user.tenant_id), str(dependency.dependent_asset_id))
        return db_dependency
    except ValueError as e:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=str(e)
        )


@router.put("/{dependency_id}", response_model=AssetDependencyRead)
@audit_log_action("update", "AssetDependency")
def update_asset_dependency(
    dependency_id: uuid.UUID,
    dependency_update: AssetDependencyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing asset dependency"""
    # Recupera la dipendenza prima di aggiornarla per invalidare la cache
    existing_dep = crud_dependencies.get_asset_dependency(
        db, dependency_id, current_user.tenant_id
    )
    
    db_dependency = crud_dependencies.update_asset_dependency(
        db, dependency_id, dependency_update, current_user.tenant_id
    )
    if not db_dependency:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="Asset dependency not found"
        )
    
    # Invalida la cache del rischio per l'asset dipendente
    from app.services.risk_cache import risk_cache
    if existing_dep:
        risk_cache.invalidate_asset(str(current_user.tenant_id), str(existing_dep.dependent_asset_id))
    
    return db_dependency


@router.delete("/{dependency_id}", status_code=204)
@audit_log_action("delete", "AssetDependency")
def delete_asset_dependency(
    dependency_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an asset dependency"""
    # Recupera la dipendenza prima di eliminarla per invalidare la cache
    existing_dep = crud_dependencies.get_asset_dependency(
        db, dependency_id, current_user.tenant_id
    )
    
    success = crud_dependencies.delete_asset_dependency(
        db, dependency_id, current_user.tenant_id
    )
    if not success:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="Asset dependency not found"
        )
    
    # Invalida la cache del rischio per l'asset dipendente
    from app.services.risk_cache import risk_cache
    if existing_dep:
        risk_cache.invalidate_asset(str(current_user.tenant_id), str(existing_dep.dependent_asset_id))


@router.get("/assets/{asset_id}/dependencies", response_model=List[AssetDependencyWithAssets])
def get_asset_dependencies_as_dependent(
    asset_id: uuid.UUID,
    dependency_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all dependencies where this asset depends on others"""
    # Verify asset exists and belongs to tenant
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.deleted_at == None
    ).first()
    if not asset:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )
    
    dependencies = crud_dependencies.get_asset_dependencies_as_dependent(
        db, asset_id, current_user.tenant_id, dependency_type
    )
    
    # Convert to dict with asset data
    result = []
    for dep in dependencies:
        result.append({
            'id': dep.id,
            'tenant_id': dep.tenant_id,
            'dependent_asset_id': dep.dependent_asset_id,
            'dependency_asset_id': dep.dependency_asset_id,
            'dependency_type': dep.dependency_type,
            'criticality': dep.criticality,
            'description': dep.description,
            'is_bidirectional': dep.is_bidirectional,
            'created_at': dep.created_at,
            'updated_at': dep.updated_at,
            'created_by': dep.created_by,
            'dependent_asset': {
                'id': str(dep.dependent_asset.id) if dep.dependent_asset else None,
                'name': dep.dependent_asset.name if dep.dependent_asset else None
            } if dep.dependent_asset else None,
            'dependency_asset': {
                'id': str(dep.dependency_asset.id) if dep.dependency_asset else None,
                'name': dep.dependency_asset.name if dep.dependency_asset else None
            } if dep.dependency_asset else None
        })
    
    return result


@router.get("/assets/{asset_id}/dependents", response_model=List[AssetDependencyWithAssets])
def get_asset_dependencies_as_dependency(
    asset_id: uuid.UUID,
    dependency_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all dependencies where other assets depend on this one"""
    # Verify asset exists and belongs to tenant
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.deleted_at == None
    ).first()
    if not asset:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )
    
    dependencies = crud_dependencies.get_asset_dependencies_as_dependency(
        db, asset_id, current_user.tenant_id, dependency_type
    )
    
    # Convert to dict with asset data
    result = []
    for dep in dependencies:
        result.append({
            'id': dep.id,
            'tenant_id': dep.tenant_id,
            'dependent_asset_id': dep.dependent_asset_id,
            'dependency_asset_id': dep.dependency_asset_id,
            'dependency_type': dep.dependency_type,
            'criticality': dep.criticality,
            'description': dep.description,
            'is_bidirectional': dep.is_bidirectional,
            'created_at': dep.created_at,
            'updated_at': dep.updated_at,
            'created_by': dep.created_by,
            'dependent_asset': {
                'id': str(dep.dependent_asset.id) if dep.dependent_asset else None,
                'name': dep.dependent_asset.name if dep.dependent_asset else None
            } if dep.dependent_asset else None,
            'dependency_asset': {
                'id': str(dep.dependency_asset.id) if dep.dependency_asset else None,
                'name': dep.dependency_asset.name if dep.dependency_asset else None
            } if dep.dependency_asset else None
        })
    
    return result


@router.get("/assets/{asset_id}/risk-propagation")
def get_risk_propagation(
    asset_id: uuid.UUID,
    max_depth: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate risk propagation from an asset through dependencies"""
    # Verify asset exists
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.deleted_at == None
    ).first()
    if not asset:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )
    
    try:
        result = RiskPropagationService.calculate_risk_propagation(
            db, asset_id, current_user.tenant_id, max_depth
        )
        return result
    except ValueError as e:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=str(e)
        )


@router.get("/assets/{asset_id}/risk-from-dependencies")
def get_risk_from_dependencies(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Calculate how much of this asset's risk comes from its dependencies.
    Returns detailed breakdown of risk contribution from each dependency.
    """
    # Verify asset exists
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.deleted_at == None
    ).first()
    if not asset:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )
    
    # Get dependencies where this asset depends on others
    dependencies = crud_dependencies.get_asset_dependencies_as_dependent(
        db, asset_id, current_user.tenant_id
    )
    
    if not dependencies:
        return {
            "asset_id": str(asset_id),
            "asset_name": asset.name,
            "total_risk_from_dependencies": 0.0,
            "base_risk_score": asset.risk_score or 0.0,
            "dependencies_risk_breakdown": []
        }
    
    # Calculate risk contribution from each dependency
    breakdown = []
    total_risk_from_deps = 0.0
    
    for dep in dependencies:
        # Get the dependency asset
        dep_asset = db.query(Asset).filter(
            Asset.id == dep.dependency_asset_id,
            Asset.tenant_id == current_user.tenant_id,
            Asset.deleted_at == None
        ).first()
        
        if not dep_asset:
            continue
        
        dep_risk = dep_asset.risk_score or 0.0
        
        # Calculate adjustment based on dependency risk and criticality
        criticality_weight = RiskPropagationService.CRITICALITY_WEIGHTS.get(
            dep.criticality, 0.5
        )
        dependency_weight = RiskPropagationService.DEPENDENCY_TYPE_WEIGHTS.get(
            dep.dependency_type, 0.5
        )
        
        # Risk contribution formula (same as in risk propagation)
        # Use same formula as calculate_risk_propagation for consistency
        # Depth is always 1 for direct dependencies
        depth_decay = 1.0  # No decay for direct dependencies
        risk_contribution = (
            dep_risk * criticality_weight * dependency_weight * depth_decay
        )
        
        # Cap at reasonable maximum (e.g., 50% of source risk)
        risk_contribution = min(risk_contribution, dep_risk * 0.5)
        
        total_risk_from_deps += risk_contribution
        
        breakdown.append({
            "dependency_id": str(dep.id),
            "dependency_asset_id": str(dep.dependency_asset_id),
            "dependency_asset_name": dep_asset.name,
            "dependency_asset_risk_score": dep_risk,
            "dependency_type": dep.dependency_type,
            "criticality": dep.criticality,
            "risk_contribution": round(risk_contribution, 2),
            "description": dep.description
        })
    
    # Cap total risk from dependencies so that total risk doesn't exceed 10.0
    base_risk = asset.risk_score or 0.0
    max_allowed_deps_risk = max(0.0, 10.0 - base_risk)
    total_risk_from_deps = min(total_risk_from_deps, max_allowed_deps_risk)
    
    return {
        "asset_id": str(asset_id),
        "asset_name": asset.name,
        "base_risk_score": asset.risk_score or 0.0,
        "total_risk_from_dependencies": round(total_risk_from_deps, 2),
        "dependencies_risk_breakdown": breakdown
    }


@router.get("/assets/{asset_id}/impact-analysis", response_model=ImpactAnalysis)
def get_impact_analysis(
    asset_id: uuid.UUID,
    max_depth: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Analyze impact if this asset fails"""
    # Verify asset exists
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.deleted_at == None
    ).first()
    if not asset:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )
    
    try:
        result = RiskPropagationService.calculate_impact_analysis(
            db, asset_id, current_user.tenant_id, max_depth
        )
        return result
    except ValueError as e:
        raise ErrorCodeException(
            status_code=400,
            error_code=ErrorCode.INVALID_INPUT,
            detail=str(e)
        )


@router.get("/assets/{asset_id}/dependency-chain")
def get_dependency_chain(
    asset_id: uuid.UUID,
    max_depth: int = Query(10, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dependency chain starting from an asset"""
    # Verify asset exists
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.deleted_at == None
    ).first()
    if not asset:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )
    
    chain = crud_dependencies.get_dependency_chain(
        db, asset_id, current_user.tenant_id, max_depth
    )
    return {"chain": chain, "total_items": len(chain)}


@router.get("/assets/{asset_id}/affected-assets")
def get_affected_assets(
    asset_id: uuid.UUID,
    max_depth: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all assets that would be affected if this asset fails"""
    # Verify asset exists
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.tenant_id == current_user.tenant_id,
        Asset.deleted_at == None
    ).first()
    if not asset:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND
        )
    
    affected = RiskPropagationService.get_all_affected_assets(
        db, asset_id, current_user.tenant_id, max_depth
    )
    return {"affected_assets": affected, "total_count": len(affected)}


@router.get("/{dependency_id}/connection-status")
def get_dependency_connection_status(
    dependency_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get connection status for a dependency (if there's a corresponding AssetConnection)"""
    dependency = crud_dependencies.get_asset_dependency(
        db, dependency_id, current_user.tenant_id
    )
    if not dependency:
        raise ErrorCodeException(
            status_code=404,
            error_code=ErrorCode.ASSET_NOT_FOUND,
            detail="Asset dependency not found"
        )
    
    connection_status = ConnectionDependencyAnalyzer.get_dependency_connection_status(
        db, dependency
    )
    return connection_status

