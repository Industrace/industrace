# backend/app/models/asset_dependency.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AssetDependency(Base):
    """
    Asset Dependency: Relazioni logiche/funzionali tra asset.
    Distinto da AssetConnection (connessioni fisiche di rete).
    
    Esempi:
    - Asset A dipende da Asset B (logical dependency)
    - Asset A riceve dati da Asset B (data_flow dependency)
    - Asset A è controllato da Asset B (control_flow dependency)
    """
    __tablename__ = "asset_dependencies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Self-referential relationship: Asset → Asset
    dependent_asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Asset che dipende (from)"
    )
    dependency_asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Asset da cui dipende (to)"
    )
    
    # Dependency Type
    dependency_type = Column(
        String(50),
        nullable=False,
        default="logical",
        index=True,
        comment="Type: logical, functional, data_flow, control_flow"
    )
    
    # Criticality
    criticality = Column(
        String(20),
        nullable=False,
        default="medium",
        comment="Criticality: low, medium, high, critical"
    )
    
    # Confidence and Source
    confidence = Column(
        String(20),
        nullable=False,
        default="medium",
        index=True,
        comment="Confidence level: low (hypothesis), medium (probable), high (certain)"
    )
    
    source = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Source: manual, assessment, import, template"
    )
    
    # Description
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Direction (optional, per documentare direzione del flusso)
    is_bidirectional = Column(
        String(20),
        nullable=True,
        default="false",
        comment="true se la dipendenza è bidirezionale"
    )
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    dependent_asset = relationship(
        "Asset",
        foreign_keys=[dependent_asset_id],
        backref="dependencies_as_dependent"
    )
    dependency_asset = relationship(
        "Asset",
        foreign_keys=[dependency_asset_id],
        backref="dependencies_as_dependency"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "dependent_asset_id != dependency_asset_id",
            name="ck_asset_dependency_no_self_reference"
        ),
        CheckConstraint(
            "dependency_type IN ('logical', 'functional', 'data_flow', 'control_flow')",
            name="ck_asset_dependency_type"
        ),
        CheckConstraint(
            "criticality IN ('low', 'medium', 'high', 'critical')",
            name="ck_asset_dependency_criticality"
        ),
        CheckConstraint(
            "confidence IN ('low', 'medium', 'high')",
            name="ck_asset_dependency_confidence"
        ),
        CheckConstraint(
            "source IS NULL OR source IN ('manual', 'assessment', 'import', 'template')",
            name="ck_asset_dependency_source"
        )
    )

