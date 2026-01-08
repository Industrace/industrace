"""add_deleted_at_to_manufacturers

Revision ID: add_deleted_at_manufacturers
Revises: merge_vuln_status_change
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_deleted_at_manufacturers'
down_revision: Union[str, None] = 'merge_vuln_status_change'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('manufacturers', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('manufacturers', 'deleted_at')

