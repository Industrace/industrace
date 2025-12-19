"""add_confidence_source_to_asset_dependencies

Revision ID: add_confidence_source_deps
Revises: merge_heads_2025
Create Date: 2025-01-XX 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_confidence_source_deps'
down_revision: Union[str, None] = 'merge_heads_2025'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add confidence and source fields to asset_dependencies table.
    
    This migration adds:
    - confidence: Confidence level of the dependency (low, medium, high)
    - source: Source of the dependency (manual, assessment, import, template)
    - notes: Additional notes field
    
    No downtime required.
    Estimated time: < 1 second for typical database sizes.
    """
    # Add columns
    op.add_column('asset_dependencies', sa.Column('confidence', sa.String(20), nullable=False, server_default='medium'))
    op.add_column('asset_dependencies', sa.Column('source', sa.String(50), nullable=True))
    op.add_column('asset_dependencies', sa.Column('notes', sa.Text(), nullable=True))
    
    # Add indexes for filtering
    op.create_index('idx_asset_dependencies_confidence', 'asset_dependencies', ['confidence'])
    op.create_index('idx_asset_dependencies_source', 'asset_dependencies', ['source'])
    
    # Add check constraints
    op.create_check_constraint(
        'ck_asset_dependency_confidence',
        'asset_dependencies',
        "confidence IN ('low', 'medium', 'high')"
    )
    op.create_check_constraint(
        'ck_asset_dependency_source',
        'asset_dependencies',
        "source IS NULL OR source IN ('manual', 'assessment', 'import', 'template')"
    )


def downgrade() -> None:
    """Remove confidence and source fields from asset_dependencies table."""
    # Drop constraints
    op.drop_constraint('ck_asset_dependency_source', 'asset_dependencies', type_='check')
    op.drop_constraint('ck_asset_dependency_confidence', 'asset_dependencies', type_='check')
    
    # Drop indexes
    op.drop_index('idx_asset_dependencies_source', table_name='asset_dependencies')
    op.drop_index('idx_asset_dependencies_confidence', table_name='asset_dependencies')
    
    # Drop columns
    op.drop_column('asset_dependencies', 'notes')
    op.drop_column('asset_dependencies', 'source')
    op.drop_column('asset_dependencies', 'confidence')


