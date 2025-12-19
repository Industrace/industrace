"""Add review configuration fields to tenants

Revision ID: add_review_config_fields
Revises: 6506702f1285
Create Date: 2025-12-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_review_config_fields'
down_revision = '6506702f1285'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add review configuration fields to tenants table
    op.add_column('tenants', sa.Column('review_due_days_ahead', sa.Integer(), server_default='30', nullable=False))
    op.add_column('tenants', sa.Column('review_upcoming_days_ahead', sa.Integer(), server_default='30', nullable=False))


def downgrade() -> None:
    op.drop_column('tenants', 'review_upcoming_days_ahead')
    op.drop_column('tenants', 'review_due_days_ahead')

