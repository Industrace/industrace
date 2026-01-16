"""add_account_lockout_fields

Revision ID: add_lockout_fields
Revises: add_notif_enabled
Create Date: 2025-01-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_lockout_fields'
down_revision: Union[str, None] = 'add_notif_enabled'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add account lockout fields and password_change_required to users table"""
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('password_change_required', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    """Remove account lockout fields and password_change_required from users table"""
    op.drop_column('users', 'password_change_required')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
