"""create_asset_dependencies

Revision ID: 0487021cac20
Revises: create_isa62443_models
Create Date: 2025-12-05 09:11:11.957914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0487021cac20'
down_revision: Union[str, None] = 'create_isa62443_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create asset_dependencies table.
    
    This migration creates:
    - asset_dependencies: Logical/functional dependencies between assets
    
    No downtime required.
    Estimated time: < 1 second for typical database sizes.
    """
    op.create_table(
        'asset_dependencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('dependent_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dependency_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dependency_type', sa.String(50), nullable=False, server_default='logical'),
        sa.Column('criticality', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_bidirectional', sa.String(20), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True)
    )
    
    # Indexes
    op.create_index('idx_asset_dependencies_dependent', 'asset_dependencies', ['dependent_asset_id', 'dependency_type'])
    op.create_index('idx_asset_dependencies_dependency', 'asset_dependencies', ['dependency_asset_id', 'dependency_type'])
    op.create_index('idx_asset_dependencies_tenant_type', 'asset_dependencies', ['tenant_id', 'dependency_type'])
    op.create_index('idx_asset_dependencies_tenant', 'asset_dependencies', ['tenant_id'])
    
    # Constraints
    op.create_check_constraint(
        'ck_asset_dependency_no_self_reference',
        'asset_dependencies',
        'dependent_asset_id != dependency_asset_id'
    )
    op.create_check_constraint(
        'ck_asset_dependency_type',
        'asset_dependencies',
        "dependency_type IN ('logical', 'functional', 'data_flow', 'control_flow')"
    )
    op.create_check_constraint(
        'ck_asset_dependency_criticality',
        'asset_dependencies',
        "criticality IN ('low', 'medium', 'high', 'critical')"
    )


def downgrade() -> None:
    """Drop asset_dependencies table."""
    op.drop_constraint('ck_asset_dependency_criticality', 'asset_dependencies', type_='check')
    op.drop_constraint('ck_asset_dependency_type', 'asset_dependencies', type_='check')
    op.drop_constraint('ck_asset_dependency_no_self_reference', 'asset_dependencies', type_='check')
    op.drop_index('idx_asset_dependencies_tenant', table_name='asset_dependencies')
    op.drop_index('idx_asset_dependencies_tenant_type', table_name='asset_dependencies')
    op.drop_index('idx_asset_dependencies_dependency', table_name='asset_dependencies')
    op.drop_index('idx_asset_dependencies_dependent', table_name='asset_dependencies')
    op.drop_table('asset_dependencies')
