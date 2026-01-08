"""fix_notification_template_unique_constraint

Revision ID: fix_notification_template_unique_constraint
Revises: add_modern_email_providers
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fix_notif_template_unique'
down_revision: Union[str, None] = 'create_notification_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix notification_templates unique constraint to allow system-wide and tenant-specific templates with same code.
    
    Changes:
    - Remove unique constraint on template_code alone
    - Add unique constraint on (template_code, tenant_id) to allow:
      * One system-wide template (tenant_id = NULL) per template_code
      * One tenant-specific template (tenant_id = UUID) per template_code per tenant
    
    No downtime required.
    Estimated time: < 1 second.
    """
    # Drop the existing unique constraint on template_code
    op.drop_constraint('notification_templates_template_code_key', 'notification_templates', type_='unique')
    
    # Create a unique constraint on (template_code, tenant_id)
    # This allows:
    # - One template with template_code='X' and tenant_id=NULL (system-wide)
    # - One template with template_code='X' and tenant_id='uuid1' (tenant-specific for tenant1)
    # - One template with template_code='X' and tenant_id='uuid2' (tenant-specific for tenant2)
    op.create_unique_constraint(
        'uq_notification_templates_code_tenant',
        'notification_templates',
        ['template_code', 'tenant_id']
    )


def downgrade() -> None:
    """Revert to unique constraint on template_code only."""
    # Drop the composite unique constraint
    op.drop_constraint('uq_notification_templates_code_tenant', 'notification_templates', type_='unique')
    
    # Restore the original unique constraint on template_code
    op.create_unique_constraint('notification_templates_template_code_key', 'notification_templates', ['template_code'])

