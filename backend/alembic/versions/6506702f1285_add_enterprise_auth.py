"""add_enterprise_auth

Revision ID: 6506702f1285
Revises: fa0b3e6f2d60
Create Date: 2025-12-05 09:37:42.730421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6506702f1285'
down_revision: Union[str, None] = 'fa0b3e6f2d60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add enterprise authentication support.
    
    This migration:
    - Extends User model with SSO fields (auth_provider, external_id, etc.)
    - Makes password_hash nullable (for SSO-only users)
    - Creates tenant_sso_config table for OAuth2/OIDC configuration
    - Sets auth_provider='local' for existing users
    
    No downtime required.
    Estimated time: < 2 seconds for typical database sizes.
    """
    # 1. Add SSO fields to users table
    op.add_column('users', sa.Column('auth_provider', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('external_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('sso_email', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('last_sso_login', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('sso_metadata', postgresql.JSONB(), nullable=True))
    
    # 2. Make password_hash nullable (for SSO-only users)
    # First, ensure no NULL passwords exist (set a placeholder for existing users)
    op.execute("UPDATE users SET password_hash = password_hash WHERE password_hash IS NULL")
    op.alter_column('users', 'password_hash', nullable=True)
    
    # 3. Set auth_provider='local' for existing users
    op.execute("UPDATE users SET auth_provider = 'local' WHERE auth_provider IS NULL")
    
    # 4. Create indexes for SSO fields
    op.create_index('idx_users_auth_provider', 'users', ['auth_provider'])
    op.create_index('idx_users_external_id', 'users', ['external_id'])
    
    # 5. Create tenant_sso_config table
    op.create_table(
        'tenant_sso_config',
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), primary_key=True),
        sa.Column('provider_type', sa.String(50), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='false'),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('client_secret_encrypted', sa.String(500), nullable=False),
        sa.Column('tenant_domain', sa.String(255), nullable=True),
        sa.Column('authority_url', sa.String(500), nullable=True),
        sa.Column('authorization_endpoint', sa.String(500), nullable=True),
        sa.Column('token_endpoint', sa.String(500), nullable=True),
        sa.Column('userinfo_endpoint', sa.String(500), nullable=True),
        sa.Column('jwks_uri', sa.String(500), nullable=True),
        sa.Column('scopes', postgresql.JSONB(), server_default='["openid", "profile", "email"]'),
        sa.Column('auto_provision_enabled', sa.Boolean(), server_default='true'),
        sa.Column('default_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id'), nullable=True),
        sa.Column('domain_restriction', sa.String(255), nullable=True),
        sa.Column('redirect_uri', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('last_test_at', sa.DateTime(), nullable=True),
        sa.Column('last_test_status', sa.String(20), nullable=True),
        sa.Column('last_test_error', sa.Text(), nullable=True)
    )
    op.create_index('idx_sso_config_enabled', 'tenant_sso_config', ['enabled'])


def downgrade() -> None:
    """Remove enterprise authentication support."""
    op.drop_index('idx_sso_config_enabled', table_name='tenant_sso_config')
    op.drop_table('tenant_sso_config')
    
    op.drop_index('idx_users_external_id', table_name='users')
    op.drop_index('idx_users_auth_provider', table_name='users')
    
    op.drop_column('users', 'sso_metadata')
    op.drop_column('users', 'last_sso_login')
    op.drop_column('users', 'sso_email')
    op.drop_column('users', 'external_id')
    op.drop_column('users', 'auth_provider')
    
    # Restore password_hash NOT NULL (set placeholder for NULL values)
    op.execute("UPDATE users SET password_hash = '' WHERE password_hash IS NULL")
    op.alter_column('users', 'password_hash', nullable=False)
