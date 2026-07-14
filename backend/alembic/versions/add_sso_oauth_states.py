"""Add sso_oauth_states table for shared OAuth PKCE state

Revision ID: add_sso_oauth_states
Revises: add_discovered_mac_unique
Create Date: 2026-07-14

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "add_sso_oauth_states"
down_revision = "add_discovered_mac_unique"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sso_oauth_states",
        sa.Column("state", sa.String(length=128), primary_key=True),
        sa.Column("code_verifier", sa.String(length=256), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_sso_oauth_states_tenant_id",
        "sso_oauth_states",
        ["tenant_id"],
    )
    op.create_index(
        "ix_sso_oauth_states_expires_at",
        "sso_oauth_states",
        ["expires_at"],
    )


def downgrade():
    op.drop_index("ix_sso_oauth_states_expires_at", table_name="sso_oauth_states")
    op.drop_index("ix_sso_oauth_states_tenant_id", table_name="sso_oauth_states")
    op.drop_table("sso_oauth_states")
