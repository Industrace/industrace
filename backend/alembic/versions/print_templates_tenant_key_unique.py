"""Allow the same print template key per tenant.

Revision ID: print_tpl_tenant_key
Revises: add_mfa_totp
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op


revision: str = "print_tpl_tenant_key"
down_revision: Union[str, None] = "add_mfa_totp"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_print_templates_key", table_name="print_templates")
    op.create_index("ix_print_templates_key", "print_templates", ["key"], unique=False)
    op.create_unique_constraint(
        "uq_print_templates_tenant_key",
        "print_templates",
        ["tenant_id", "key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_print_templates_tenant_key", "print_templates", type_="unique"
    )
    op.drop_index("ix_print_templates_key", table_name="print_templates")
    op.create_index("ix_print_templates_key", "print_templates", ["key"], unique=True)
