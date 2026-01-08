"""merge_conduit_review_areas_heads

Revision ID: merge_heads_2025
Revises: add_conduit_governance, add_review_config_fields, f5b3589a115e
Create Date: 2025-12-05 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_heads_2025'
down_revision: Union[str, tuple, None] = ('add_conduit_governance', 'add_review_config_fields', 'f5b3589a115e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge multiple head revisions.
    
    This is a merge migration that combines:
    - add_conduit_governance (conduit governance fields)
    - add_review_config_fields (review configuration fields)
    - f5b3589a115e (deleted_at to areas)
    
    No actual schema changes, just merges the branches.
    """
    pass


def downgrade() -> None:
    """Downgrade merge migration."""
    pass









