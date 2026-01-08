"""merge_all_heads

Revision ID: merge_all_heads
Revises: ('add_deleted_at_manufacturers', 'fix_notification_template_unique_constraint')
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'merge_all_heads'
down_revision: Union[str, tuple, None] = ('add_deleted_at_manufacturers', 'fix_notif_template_unique')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge all heads - no schema changes, just merge migration branches."""
    pass


def downgrade() -> None:
    """No-op for merge migration."""
    pass

