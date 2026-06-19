"""Allow asset object_type on sr_assessments

Revision ID: extend_sr_assessment_asset
Revises: add_requirement_enhancements
Create Date: 2026-05-22

"""

from alembic import op


revision = "extend_sr_assessment_asset"
down_revision = "add_requirement_enhancements"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("check_object_type_values", "sr_assessments", type_="check")
    op.create_check_constraint(
        "check_object_type_values",
        "sr_assessments",
        "object_type IN ('zone', 'conduit', 'asset')",
    )


def downgrade():
    op.drop_constraint("check_object_type_values", "sr_assessments", type_="check")
    op.create_check_constraint(
        "check_object_type_values",
        "sr_assessments",
        "object_type IN ('zone', 'conduit')",
    )
