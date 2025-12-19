"""add_asset_review_fields

Revision ID: add_asset_review_fields
Revises: add_role_asset_contacts
Create Date: 2025-12-05 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_asset_review_fields'
down_revision: Union[str, None] = 'add_role_asset_contacts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add review and maintenance fields to Asset, Tenant, and Site models.
    
    This migration adds:
    - Review fields to assets (last_review_date, next_review_date, review_status, review_notes, review_interval_months)
    - Default review interval to tenants
    - Site-specific review interval override
    
    No downtime required.
    Estimated time: < 1 second for typical database sizes.
    """
    # 1. Add review fields to assets table
    op.add_column('assets', sa.Column('last_review_date', sa.DateTime(), nullable=True))
    op.add_column('assets', sa.Column('next_review_date', sa.DateTime(), nullable=True))
    op.add_column('assets', sa.Column('review_status', sa.String(20), nullable=False, server_default='pending'))
    op.add_column('assets', sa.Column('review_notes', sa.Text(), nullable=True))
    op.add_column('assets', sa.Column('review_interval_months', sa.Integer(), nullable=False, server_default='6'))
    
    # 2. Add indexes for performance (review queries)
    op.create_index(
        'idx_assets_next_review_date',
        'assets',
        ['next_review_date'],
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    op.create_index(
        'idx_assets_review_status',
        'assets',
        ['review_status', 'next_review_date'],
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    
    # 3. Add default review interval to tenants
    op.add_column('tenants', sa.Column('default_review_interval_months', sa.Integer(), nullable=False, server_default='6'))
    
    # 4. Add review interval override to sites
    op.add_column('sites', sa.Column('review_interval_months', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove review fields from Asset, Tenant, and Site models."""
    # Remove indexes
    op.drop_index('idx_assets_review_status', 'assets')
    op.drop_index('idx_assets_next_review_date', 'assets')
    
    # Remove columns from assets
    op.drop_column('assets', 'review_interval_months')
    op.drop_column('assets', 'review_notes')
    op.drop_column('assets', 'review_status')
    op.drop_column('assets', 'next_review_date')
    op.drop_column('assets', 'last_review_date')
    
    # Remove columns from tenants
    op.drop_column('tenants', 'default_review_interval_months')
    
    # Remove columns from sites
    op.drop_column('sites', 'review_interval_months')

