"""add_mfa_totp_fields

Revision ID: add_mfa_totp
Revises: add_sso_oauth_states
Create Date: 2026-07-21 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "add_mfa_totp"
down_revision: Union[str, None] = "add_sso_oauth_states"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("totp_secret_encrypted", sa.String(length=500), nullable=True))
    op.add_column(
        "users",
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("users", sa.Column("totp_verified_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("totp_enrolled_at", sa.DateTime(), nullable=True))
    op.add_column(
        "users",
        sa.Column("failed_mfa_attempts", sa.Integer(), nullable=True, server_default="0"),
    )
    op.add_column("users", sa.Column("mfa_locked_until", sa.DateTime(), nullable=True))
    op.create_index("ix_users_totp_enabled", "users", ["totp_enabled"], unique=False)

    op.create_table(
        "user_backup_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_backup_codes_user_id", "user_backup_codes", ["user_id"], unique=False)
    op.create_index(
        "ix_user_backup_codes_user_id_used_at",
        "user_backup_codes",
        ["user_id", "used_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_backup_codes_user_id_used_at", table_name="user_backup_codes")
    op.drop_index("ix_user_backup_codes_user_id", table_name="user_backup_codes")
    op.drop_table("user_backup_codes")
    op.drop_index("ix_users_totp_enabled", table_name="users")
    op.drop_column("users", "mfa_locked_until")
    op.drop_column("users", "failed_mfa_attempts")
    op.drop_column("users", "totp_enrolled_at")
    op.drop_column("users", "totp_verified_at")
    op.drop_column("users", "totp_enabled")
    op.drop_column("users", "totp_secret_encrypted")
