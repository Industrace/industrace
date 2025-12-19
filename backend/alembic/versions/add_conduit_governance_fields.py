"""add_conduit_governance_fields

Revision ID: add_conduit_governance
Revises: 6506702f1285
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_conduit_governance'
down_revision: Union[str, None] = '6506702f1285'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add governance fields to conduits table.
    
    This migration adds:
    - flow_justification: Text field for justifying the flow (least privilege principle)
    - ownership: String field for conduit maintenance responsibility
    - Increases allowed_direction column size from 20 to 50 to support 'request_response'
    
    No downtime required.
    """
    # 1. Increase allowed_direction column size
    op.alter_column('conduits', 'allowed_direction',
                   existing_type=sa.String(20),
                   type_=sa.String(50),
                   existing_nullable=True)
    
    # 2. Add flow_justification column
    op.add_column('conduits',
        sa.Column('flow_justification', sa.Text(), nullable=True))
    
    # 3. Add ownership column
    op.add_column('conduits',
        sa.Column('ownership', sa.String(255), nullable=True))


def downgrade() -> None:
    """Remove governance fields from conduits table."""
    # Remove columns
    op.drop_column('conduits', 'ownership')
    op.drop_column('conduits', 'flow_justification')
    
    # Restore allowed_direction column size
    op.alter_column('conduits', 'allowed_direction',
                   existing_type=sa.String(50),
                   type_=sa.String(20),
                   existing_nullable=True)






