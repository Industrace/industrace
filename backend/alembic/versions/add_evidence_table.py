"""add_evidence_table

Revision ID: add_evidence_table
Revises: add_notif_enabled
Create Date: 2025-12-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_evidence_table'
down_revision: Union[str, None] = 'add_notif_enabled'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add evidence table for ISA/IEC 62443 Evidence management"""
    op.create_table(
        'evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('type', sa.String(50), nullable=True),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('raw_data', postgresql.JSONB, nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('zone_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_zones.id', ondelete='SET NULL'), nullable=True),
        sa.Column('conduit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conduits.id', ondelete='SET NULL'), nullable=True),
        sa.Column('capability_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_capabilities.id', ondelete='SET NULL'), nullable=True),
        sa.Column('sr_assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sr_assessments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="check_confidence_range"),
        sa.CheckConstraint("source IN ('manual', 'document', 'import', 'probe')", name="check_source_values"),
    )
    op.create_index('idx_evidence_tenant', 'evidence', ['tenant_id'])
    op.create_index('idx_evidence_asset', 'evidence', ['asset_id'])
    op.create_index('idx_evidence_zone', 'evidence', ['zone_id'])
    op.create_index('idx_evidence_capability', 'evidence', ['capability_id'])
    op.create_index('idx_evidence_sr_assessment', 'evidence', ['sr_assessment_id'])


def downgrade() -> None:
    """Remove evidence table"""
    op.drop_index('idx_evidence_sr_assessment', table_name='evidence')
    op.drop_index('idx_evidence_capability', table_name='evidence')
    op.drop_index('idx_evidence_zone', table_name='evidence')
    op.drop_index('idx_evidence_asset', table_name='evidence')
    op.drop_index('idx_evidence_tenant', table_name='evidence')
    op.drop_table('evidence')

