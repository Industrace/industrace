"""Add requirement_enhancements (IEC 62443 RE 1-4)

Revision ID: add_requirement_enhancements
Revises: add_network_probe_models
Create Date: 2026-05-22

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "add_requirement_enhancements"
down_revision = "add_network_probe_models"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "requirement_enhancements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "security_requirement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("security_requirements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("enhancement_level", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("standard_version", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "security_requirement_id",
            "enhancement_level",
            name="uq_sr_enhancement_level",
        ),
    )
    op.create_index(
        "idx_requirement_enhancements_sr",
        "requirement_enhancements",
        ["security_requirement_id"],
    )


def downgrade():
    op.drop_index("idx_requirement_enhancements_sr", table_name="requirement_enhancements")
    op.drop_table("requirement_enhancements")
