"""add_notifications_enabled_to_users

Revision ID: add_notif_enabled
Revises: merge_all_heads
Create Date: 2025-01-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_notif_enabled'
down_revision: Union[str, None] = 'merge_all_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add notifications_enabled column to users table"""
    op.add_column('users', sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    """Remove notifications_enabled column from users table"""
    op.drop_column('users', 'notifications_enabled')

