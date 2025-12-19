"""create_notification_system

Revision ID: create_notification_system
Revises: add_asset_review_fields
Create Date: 2025-12-05 09:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'create_notification_system'
down_revision: Union[str, None] = 'add_asset_review_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create notification system tables.
    
    This migration creates:
    - notification_templates: Email templates for notifications
    - notification_preferences: User preferences for notifications
    - notification_queue: Queue for pending notifications
    - notification_logs: Log of sent notifications
    
    No downtime required.
    Estimated time: < 1 second for typical database sizes.
    """
    # 1. Create notification_templates table
    op.create_table(
        'notification_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('template_code', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('subject_template', sa.String(500), nullable=False),
        sa.Column('body_template_html', sa.Text(), nullable=False),
        sa.Column('body_template_text', sa.Text(), nullable=True),
        sa.Column('variables', postgresql.JSONB(), nullable=True),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('idx_notification_templates_code', 'notification_templates', ['template_code'])
    op.create_index('idx_notification_templates_tenant', 'notification_templates', ['tenant_id'])
    
    # 2. Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('email_enabled', sa.Boolean(), default=True),
        sa.Column('in_app_enabled', sa.Boolean(), default=True),
        sa.Column('frequency', sa.String(20), default='immediate'),
        sa.Column('severity_min', sa.Integer(), nullable=True),
        sa.Column('filters', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('idx_notification_preferences_user', 'notification_preferences', ['user_id', 'tenant_id'])
    op.create_unique_constraint('uq_user_notification_type', 'notification_preferences', ['user_id', 'notification_type'])
    
    # 3. Create notification_queue table
    op.create_table(
        'notification_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('notification_templates.id'), nullable=True),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=False),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('context_data', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('attempts', sa.Integer(), default=0),
        sa.Column('last_attempt_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('scheduled_for', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    op.create_index('idx_notification_queue_scheduled', 'notification_queue', ['status', 'scheduled_for'])
    op.create_index('idx_notification_queue_user', 'notification_queue', ['user_id'])
    
    # 4. Create notification_logs table
    op.create_table(
        'notification_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('context_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    op.create_index('idx_notification_logs_created', 'notification_logs', ['created_at'])
    op.create_index('idx_notification_logs_user_type', 'notification_logs', ['user_id', 'notification_type'])


def downgrade() -> None:
    """Remove notification system tables."""
    op.drop_index('idx_notification_logs_user_type', 'notification_logs')
    op.drop_index('idx_notification_logs_created', 'notification_logs')
    op.drop_table('notification_logs')
    
    op.drop_index('idx_notification_queue_user', 'notification_queue')
    op.drop_index('idx_notification_queue_scheduled', 'notification_queue')
    op.drop_table('notification_queue')
    
    op.drop_constraint('uq_user_notification_type', 'notification_preferences', type_='unique')
    op.drop_index('idx_notification_preferences_user', 'notification_preferences')
    op.drop_table('notification_preferences')
    
    op.drop_index('idx_notification_templates_tenant', 'notification_templates')
    op.drop_index('idx_notification_templates_code', 'notification_templates')
    op.drop_table('notification_templates')

