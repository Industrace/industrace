"""add_asset_zone_memberships

Revision ID: d2b57c3dd204
Revises: add_confidence_source_deps
Create Date: 2025-12-17 12:19:26.984903

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd2b57c3dd204'
down_revision: Union[str, None] = 'add_confidence_source_deps'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create asset_zone_memberships table.
    
    This migration creates the asset_zone_memberships table to support
    multiple zone memberships per asset with different roles.
    
    This is ISA/IEC 62443 compliant and allows modeling real-world scenarios
    where an asset has different interfaces that belong to different zones.
    
    Example:
    - HMI-01 in Control Zone with role "operator_interface"
    - HMI-01 in DMZ with role "data_publisher"
    
    The existing security_zone_id field in assets table is kept for
    backward compatibility but is deprecated.
    
    No downtime required.
    Estimated time: < 1 second for typical database sizes.
    """
    op.create_table(
        'asset_zone_memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('security_zone_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(100), nullable=False),
        sa.Column('interface_scope', sa.String(255), nullable=True),
        sa.Column('sl_target', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['security_zone_id'], ['security_zones.id'], ondelete='CASCADE'),
        sa.CheckConstraint('sl_target IS NULL OR (sl_target >= 1 AND sl_target <= 4)', name='check_sl_target_range'),
    )
    
    # Create indexes
    op.create_index('ix_asset_zone_memberships_asset_id', 'asset_zone_memberships', ['asset_id'])
    op.create_index('ix_asset_zone_memberships_security_zone_id', 'asset_zone_memberships', ['security_zone_id'])
    op.create_index('ix_asset_zone_memberships_tenant_id', 'asset_zone_memberships', ['tenant_id'])
    
    # Unique constraint: an asset cannot have the same role in the same zone
    # (but can have different roles in the same zone)
    # Use UNIQUE INDEX with WHERE clause for partial unique constraint
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_asset_zone_membership_asset_zone_role "
            "ON asset_zone_memberships (asset_id, security_zone_id, role) "
            "WHERE deleted_at IS NULL"
        )
    )


def downgrade() -> None:
    """Drop asset_zone_memberships table."""
    op.drop_index('uq_asset_zone_membership_asset_zone_role', 'asset_zone_memberships')
    op.drop_index('ix_asset_zone_memberships_tenant_id', table_name='asset_zone_memberships')
    op.drop_index('ix_asset_zone_memberships_security_zone_id', table_name='asset_zone_memberships')
    op.drop_index('ix_asset_zone_memberships_asset_id', table_name='asset_zone_memberships')
    op.drop_table('asset_zone_memberships')
