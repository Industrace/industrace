"""merge_capability_heads

Revision ID: 7c13b475af01
Revises: create_capability_models
Create Date: 2025-12-18 15:49:28.673724

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c13b475af01'
down_revision: Union[str, None] = 'create_capability_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
