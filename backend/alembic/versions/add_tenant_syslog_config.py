"""Add tenant_syslog_config for external audit log (syslog)

Revision ID: add_tenant_syslog
Revises: create_capability_models
Create Date: 2025-02-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "add_tenant_syslog"
down_revision = "create_capability_models"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tenant_syslog_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("host", sa.String(255), nullable=True),
        sa.Column("port", sa.Integer(), nullable=False, server_default="514"),
        sa.Column("protocol", sa.String(10), nullable=False, server_default="udp"),
        sa.Column("facility", sa.Integer(), nullable=False, server_default="16"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_tenant_syslog_config_tenant_id",
        "tenant_syslog_config",
        ["tenant_id"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_tenant_syslog_config_tenant_id", table_name="tenant_syslog_config")
    op.drop_table("tenant_syslog_config")
