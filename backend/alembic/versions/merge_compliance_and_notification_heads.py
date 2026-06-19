"""Merge Alembic heads: IEC 62443 RE assessments + notification branches

Revision ID: merge_compliance_notif_heads
Revises: add_sr_assessment_re_level, add_evidence_table, add_lockout_fields
Create Date: 2026-05-26

"""

from alembic import op


revision = "merge_compliance_notif_heads"
down_revision = ("add_sr_assessment_re_level", "add_evidence_table", "add_lockout_fields")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
