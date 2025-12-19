"""create_isa62443_models

Revision ID: create_isa62443_models
Revises: create_notification_system
Create Date: 2025-12-05 09:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'create_isa62443_models'
down_revision: Union[str, None] = 'create_notification_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ISA/IEC 62443 models.
    
    This migration creates:
    - security_requirements: System-wide reference data for ISA/IEC 62443 requirements
    - security_zones: Logical security zones
    - security_zone_locations: Many-to-many mapping between zones and locations
    - conduits: Communication paths between zones
    - security_requirement_compliance: Compliance tracking
    - Adds security_zone_id and ISA/IEC 62443 fields to assets
    
    No downtime required.
    Estimated time: < 2 seconds for typical database sizes.
    """
    # 1. Create security_requirements table (system-wide, no tenant_id)
    op.create_table(
        'security_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('requirement_id', sa.String(50), unique=True, nullable=False),
        sa.Column('requirement_category', sa.String(50), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('requirement_text', sa.Text(), nullable=True),
        sa.Column('applies_to_zones', sa.Boolean(), default=True),
        sa.Column('applies_to_conduits', sa.Boolean(), default=True),
        sa.Column('applies_to_assets', sa.Boolean(), default=False),
        sa.Column('min_security_level', sa.Integer(), nullable=True),
        sa.Column('max_security_level', sa.Integer(), nullable=True),
        sa.Column('standard_version', sa.String(20), nullable=True),
        sa.Column('section_reference', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('idx_security_requirements_id', 'security_requirements', ['requirement_id'])
    
    # 2. Create security_zones table
    op.create_table(
        'security_zones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sites.id'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('zone_type', sa.String(50), nullable=True),
        sa.Column('security_level_target', sa.Integer(), nullable=True),
        sa.Column('security_level_achieved', sa.Integer(), nullable=True),
        sa.Column('security_level_capability', sa.Integer(), nullable=True),
        sa.Column('is_dmz', sa.Boolean(), default=False),
        sa.Column('is_air_gapped', sa.Boolean(), default=False),
        sa.Column('network_segment', sa.String(100), nullable=True),
        sa.Column('compliance_status', sa.String(20), default='not_assessed'),
        sa.Column('last_assessment_date', sa.DateTime(), nullable=True),
        sa.Column('next_assessment_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )
    op.create_index('idx_security_zones_tenant', 'security_zones', ['tenant_id', 'site_id'])
    op.create_index('idx_security_zones_deleted', 'security_zones', ['deleted_at'])
    
    # 3. Create security_zone_locations many-to-many table
    op.create_table(
        'security_zone_locations',
        sa.Column('security_zone_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_zones.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('locations.id', ondelete='CASCADE'), primary_key=True)
    )
    
    # 4. Create conduits table
    op.create_table(
        'conduits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('from_zone_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_zones.id'), nullable=False),
        sa.Column('to_zone_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_zones.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('conduit_type', sa.String(50), nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), default=False),
        sa.Column('encryption_type', sa.String(50), nullable=True),
        sa.Column('authentication_required', sa.Boolean(), default=True),
        sa.Column('authentication_method', sa.String(50), nullable=True),
        sa.Column('protocol', sa.String(50), nullable=True),
        sa.Column('port_range', sa.String(100), nullable=True),
        sa.Column('allowed_direction', sa.String(20), default='bidirectional'),
        sa.Column('security_level_target', sa.Integer(), nullable=True),
        sa.Column('security_level_achieved', sa.Integer(), nullable=True),
        sa.Column('compliance_status', sa.String(20), default='not_assessed'),
        sa.Column('last_assessment_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )
    op.create_index('idx_conduits_zones', 'conduits', ['from_zone_id', 'to_zone_id'])
    op.create_index('idx_conduits_tenant', 'conduits', ['tenant_id'])
    
    # 5. Create security_requirement_compliance table
    op.create_table(
        'security_requirement_compliance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_requirements.id'), nullable=False),
        sa.Column('zone_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_zones.id'), nullable=True),
        sa.Column('conduit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conduits.id'), nullable=True),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id'), nullable=True),
        sa.Column('compliance_status', sa.String(20), nullable=False),
        sa.Column('compliance_percentage', sa.Integer(), nullable=True),
        sa.Column('assessed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('assessment_date', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('assessment_notes', sa.Text(), nullable=True),
        sa.Column('evidence_documents', postgresql.JSONB(), nullable=True),
        sa.Column('evidence_notes', sa.Text(), nullable=True),
        sa.Column('remediation_required', sa.Boolean(), default=False),
        sa.Column('remediation_plan', sa.Text(), nullable=True),
        sa.Column('remediation_deadline', sa.DateTime(), nullable=True),
        sa.Column('remediation_status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('idx_compliance_zone', 'security_requirement_compliance', ['tenant_id', 'zone_id'])
    op.create_index('idx_compliance_asset', 'security_requirement_compliance', ['tenant_id', 'asset_id'])
    op.create_index('idx_compliance_requirement', 'security_requirement_compliance', ['requirement_id'])
    
    # 6. Add ISA/IEC 62443 fields to assets
    op.add_column('assets', sa.Column('security_zone_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('assets', sa.Column('security_level_target', sa.Integer(), nullable=True))
    op.add_column('assets', sa.Column('security_level_achieved', sa.Integer(), nullable=True))
    op.add_column('assets', sa.Column('isa62443_compliance_status', sa.String(20), nullable=True))
    op.add_column('assets', sa.Column('isa62443_last_assessment', sa.DateTime(), nullable=True))
    
    # Add foreign key and index
    op.create_foreign_key(
        'fk_assets_security_zone',
        'assets', 'security_zones',
        ['security_zone_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_assets_security_zone', 'assets', ['security_zone_id'])


def downgrade() -> None:
    """Remove ISA/IEC 62443 models."""
    # Remove foreign key and index from assets
    op.drop_index('idx_assets_security_zone', 'assets')
    op.drop_constraint('fk_assets_security_zone', 'assets', type_='foreignkey')
    
    # Remove columns from assets
    op.drop_column('assets', 'isa62443_last_assessment')
    op.drop_column('assets', 'isa62443_compliance_status')
    op.drop_column('assets', 'security_level_achieved')
    op.drop_column('assets', 'security_level_target')
    op.drop_column('assets', 'security_zone_id')
    
    # Drop compliance table
    op.drop_index('idx_compliance_requirement', 'security_requirement_compliance')
    op.drop_index('idx_compliance_asset', 'security_requirement_compliance')
    op.drop_index('idx_compliance_zone', 'security_requirement_compliance')
    op.drop_table('security_requirement_compliance')
    
    # Drop conduits table
    op.drop_index('idx_conduits_tenant', 'conduits')
    op.drop_index('idx_conduits_zones', 'conduits')
    op.drop_table('conduits')
    
    # Drop zone-locations mapping
    op.drop_table('security_zone_locations')
    
    # Drop security_zones table
    op.drop_index('idx_security_zones_deleted', 'security_zones')
    op.drop_index('idx_security_zones_tenant', 'security_zones')
    op.drop_table('security_zones')
    
    # Drop security_requirements table
    op.drop_index('idx_security_requirements_id', 'security_requirements')
    op.drop_table('security_requirements')

