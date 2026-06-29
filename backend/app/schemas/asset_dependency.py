# backend/app/schemas/asset_dependency.py
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
import uuid
from datetime import datetime


class AssetDependencyBase(BaseModel):
    """Base schema for AssetDependency"""
    dependent_asset_id: uuid.UUID
    dependency_asset_id: uuid.UUID
    dependency_type: str = Field(
        default="logical",
        pattern="^(logical|functional|data_flow|control_flow)$",
        description="Type of dependency"
    )
    criticality: str = Field(
        default="medium",
        pattern="^(low|medium|high|critical)$",
        description="Criticality level"
    )
    confidence: str = Field(
        default="medium",
        pattern="^(low|medium|high)$",
        description="Confidence level: low (hypothesis), medium (probable), high (certain)"
    )
    source: Optional[str] = Field(
        default=None,
        pattern="^(manual|assessment|import|template)$",
        description="Source: manual, assessment, import, template"
    )
    description: Optional[str] = None
    notes: Optional[str] = None
    is_bidirectional: Optional[str] = Field(default="false", pattern="^(true|false)$")


class AssetDependencyCreate(AssetDependencyBase):
    """Schema for creating a new AssetDependency"""
    pass


class AssetDependencyUpdate(BaseModel):
    """Schema for updating an AssetDependency"""
    dependency_type: Optional[str] = Field(
        None,
        pattern="^(logical|functional|data_flow|control_flow)$"
    )
    criticality: Optional[str] = Field(
        None,
        pattern="^(low|medium|high|critical)$"
    )
    confidence: Optional[str] = Field(
        None,
        pattern="^(low|medium|high)$"
    )
    source: Optional[str] = Field(
        None,
        pattern="^(manual|assessment|import|template)$"
    )
    description: Optional[str] = None
    notes: Optional[str] = None
    is_bidirectional: Optional[str] = Field(None, pattern="^(true|false)$")


class AssetDependencyRead(AssetDependencyBase):
    """Schema for reading an AssetDependency"""
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class AssetDependencyWithAssets(AssetDependencyRead):
    """Schema for AssetDependency with related asset details"""
    dependent_asset: Optional[dict] = None  # AssetSummary will be loaded separately
    dependency_asset: Optional[dict] = None  # AssetSummary will be loaded separately
    
    model_config = ConfigDict(from_attributes=True)


class DependencyChainItem(BaseModel):
    """Item in a dependency chain"""
    asset_id: uuid.UUID
    asset_name: str
    dependency_type: str
    criticality: str
    depth: int


class DependencyChain(BaseModel):
    """Dependency chain analysis result"""
    chain: List[DependencyChainItem]
    total_depth: int
    max_criticality: str
    affected_assets_count: int


class ImpactAnalysis(BaseModel):
    """Impact analysis result for an asset failure"""
    asset_id: uuid.UUID
    asset_name: str
    direct_dependents: int
    total_affected_assets: int
    critical_dependencies: int
    dependency_chains: List[DependencyChain]
    estimated_impact_score: float

