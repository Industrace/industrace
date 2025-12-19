"""add_role_to_asset_contacts

Revision ID: add_role_asset_contacts
Revises: f5b3589a115e
Create Date: 2025-12-04 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_role_asset_contacts'
down_revision: Union[str, None] = 'add_performance_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add role column to asset_contacts table.
    
    This migration adds a 'role' column to the asset_contacts many-to-many
    table to support multiple owners and points-of-contact per asset.
    
    Existing records will be set to role='other' to maintain compatibility.
    
    No downtime required.
    Estimated time: < 1 second for typical database sizes.
    """
    # 1. Add column as nullable first
    op.add_column('asset_contacts',
        sa.Column('role', sa.String(50), nullable=True))
    
    # 2. Populate existing records with default value
    op.execute("""
        UPDATE asset_contacts 
        SET role = 'other' 
        WHERE role IS NULL
    """)
    
    # 3. Make column NOT NULL with server default
    op.alter_column('asset_contacts', 'role',
                   nullable=False,
                   server_default='other')
    
    # 4. Add check constraint for valid role values
    op.create_check_constraint(
        'ck_asset_contacts_role',
        'asset_contacts',
        "role IN ('owner', 'point_of_contact', 'other', 'technical', 'administrative')"
    )
    
    # 5. Add index for performance (queries by asset_id and role)
    op.create_index(
        'idx_asset_contacts_asset_role',
        'asset_contacts',
        ['asset_id', 'role']
    )


def downgrade() -> None:
    """Remove role column from asset_contacts table."""
    # Remove index first
    op.drop_index('idx_asset_contacts_asset_role', 'asset_contacts')
    
    # Remove check constraint
    op.drop_constraint('ck_asset_contacts_role', 'asset_contacts', type_='check')
    
    # Remove column
    op.drop_column('asset_contacts', 'role')

