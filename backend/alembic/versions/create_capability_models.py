"""create_security_capability_models

Revision ID: create_capability_models
Revises: d2b57c3dd204
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'create_capability_models'
down_revision: Union[str, None] = 'd2b57c3dd204'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Security Capability models.
    
    This migration creates:
    - security_capabilities: System-wide reference data for security capabilities
    - sr_capabilities: Mapping between Security Requirements and Capabilities
    - asset_capabilities: Assessment of capabilities on assets
    - sr_assessments: Assessment of SRs for zones/conduits
    - sr_assessment_evidence: Evidence linking assets and capabilities to assessments
    - conduit_assets: Association between conduits and assets with roles
    
    No downtime required.
    Estimated time: < 5 seconds for typical database sizes.
    """
    # 1. Create security_capabilities table (system-wide, no tenant_id)
    op.create_table(
        'security_capabilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(100), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('applies_to_asset', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('applies_to_zone', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('applies_to_conduit', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('typical_roles', postgresql.JSONB(), server_default='[]', nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('idx_security_capabilities_code', 'security_capabilities', ['code'])
    
    # 2. Create sr_capabilities table (mapping SR -> Capability)
    op.create_table(
        'sr_capabilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sr_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_requirements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('capability_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_capabilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('importance', sa.String(20), nullable=False, server_default='primary'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint("importance IN ('primary', 'supporting')", name='check_importance_values')
    )
    op.create_index('idx_sr_capabilities_sr', 'sr_capabilities', ['sr_id'])
    op.create_index('idx_sr_capabilities_capability', 'sr_capabilities', ['capability_id'])
    op.create_unique_constraint('uq_sr_capability', 'sr_capabilities', ['sr_id', 'capability_id', 'importance'])
    
    # 3. Create asset_capabilities table
    op.create_table(
        'asset_capabilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('capability_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_capabilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('support_level', sa.String(20), nullable=False, server_default='unknown'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('evidence_ref', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint("support_level IN ('supported', 'not_supported', 'unknown')", name='check_support_level_values')
    )
    op.create_index('idx_asset_capabilities_asset', 'asset_capabilities', ['asset_id'])
    op.create_index('idx_asset_capabilities_capability', 'asset_capabilities', ['capability_id'])
    op.create_index('idx_asset_capabilities_tenant', 'asset_capabilities', ['tenant_id'])
    op.create_unique_constraint('uq_asset_capability', 'asset_capabilities', ['asset_id', 'capability_id'])
    
    # 4. Create sr_assessments table
    op.create_table(
        'sr_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('sr_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_requirements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('object_type', sa.String(20), nullable=False),
        sa.Column('object_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='insufficient_info'),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('assessor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('assessed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint("object_type IN ('zone', 'conduit')", name='check_object_type_values'),
        sa.CheckConstraint("status IN ('compliant', 'non_compliant', 'partial', 'not_applicable', 'insufficient_info')", name='check_status_values')
    )
    op.create_index('idx_sr_assessments_sr', 'sr_assessments', ['sr_id'])
    op.create_index('idx_sr_assessments_object', 'sr_assessments', ['object_type', 'object_id'])
    op.create_index('idx_sr_assessments_tenant', 'sr_assessments', ['tenant_id'])
    op.create_unique_constraint('uq_sr_assessment', 'sr_assessments', ['sr_id', 'object_type', 'object_id', 'tenant_id'])
    
    # 5. Create sr_assessment_evidence table
    op.create_table(
        'sr_assessment_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('sr_assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sr_assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('capability_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_capabilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('idx_sr_assessment_evidence_assessment', 'sr_assessment_evidence', ['sr_assessment_id'])
    op.create_index('idx_sr_assessment_evidence_asset', 'sr_assessment_evidence', ['asset_id'])
    op.create_index('idx_sr_assessment_evidence_capability', 'sr_assessment_evidence', ['capability_id'])
    op.create_index('idx_sr_assessment_evidence_tenant', 'sr_assessment_evidence', ['tenant_id'])
    
    # 6. Create conduit_assets table
    op.create_table(
        'conduit_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('conduit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conduits.id', ondelete='CASCADE'), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='enforcement'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('idx_conduit_assets_conduit', 'conduit_assets', ['conduit_id'])
    op.create_index('idx_conduit_assets_asset', 'conduit_assets', ['asset_id'])
    op.create_index('idx_conduit_assets_tenant', 'conduit_assets', ['tenant_id'])


def downgrade() -> None:
    """Drop Security Capability models."""
    op.drop_table('conduit_assets')
    op.drop_table('sr_assessment_evidence')
    op.drop_table('sr_assessments')
    op.drop_table('asset_capabilities')
    op.drop_table('sr_capabilities')
    op.drop_table('security_capabilities')

