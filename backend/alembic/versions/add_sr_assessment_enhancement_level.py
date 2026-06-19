"""Add enhancement_level to sr_assessments for per-RE evaluation

Revision ID: add_sr_assessment_re_level
Revises: extend_sr_assessment_asset
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa


revision = "add_sr_assessment_re_level"
down_revision = "extend_sr_assessment_asset"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "sr_assessments",
        sa.Column("enhancement_level", sa.Integer(), nullable=True),
    )
    op.drop_constraint("uq_sr_assessment", "sr_assessments", type_="unique")
    op.create_index(
        "uq_sr_assessment_legacy",
        "sr_assessments",
        ["sr_id", "object_type", "object_id", "tenant_id"],
        unique=True,
        postgresql_where=sa.text("enhancement_level IS NULL"),
    )
    op.create_index(
        "uq_sr_assessment_re",
        "sr_assessments",
        ["sr_id", "object_type", "object_id", "tenant_id", "enhancement_level"],
        unique=True,
        postgresql_where=sa.text("enhancement_level IS NOT NULL"),
    )
    op.create_check_constraint(
        "check_enhancement_level_range",
        "sr_assessments",
        "enhancement_level IS NULL OR (enhancement_level >= 1 AND enhancement_level <= 4)",
    )


def downgrade():
    op.drop_constraint("check_enhancement_level_range", "sr_assessments", type_="check")
    op.drop_index("uq_sr_assessment_re", table_name="sr_assessments")
    op.drop_index("uq_sr_assessment_legacy", table_name="sr_assessments")
    op.drop_column("sr_assessments", "enhancement_level")
    op.create_unique_constraint(
        "uq_sr_assessment",
        "sr_assessments",
        ["sr_id", "object_type", "object_id", "tenant_id"],
    )
