# Configuration

This guide explains how to configure Industrace 2.x for different environments and use cases. For installation, see [INSTALLATION.md](INSTALLATION.md).

## Optional modules (per tenant)

Some capabilities can be enabled or disabled per tenant via **Setup → Optional modules** (or during the setup wizard).

### ISA/IEC 62443 (`iec62443`)

When **disabled**, the UI hides compliance menus (zones, conduits, compliance dashboard, IEC 62443 asset tab) and related API routes return `403` with `FEATURE_DISABLED`. Core CMDB, assets, and risk scoring continue to work (zone-based risk factors are skipped when disabled).

| Where to configure | Notes |
|--------------------|-------|
| Setup wizard | Checkbox **ISA/IEC 62443** (default: off for new installs) |
| Setup → Optional modules | Toggle after initial setup (admin) |

Stored in `tenant.settings.features.iec62443` (boolean). Existing tenants without the key default to **enabled** for backward compatibility.

See [IEC62443.md](IEC62443.md) for scope and limits when the module is enabled.

---

## Environment configuration

### Deployment Types

Industrace supports two main deployment scenarios with automatic configuration:

#### **Production Local** (Recommended for first time)
- **Frontend**: https://localhost (Nginx + self-signed certificates)
- **Backend**: https://localhost/api (Nginx proxy)
- **CORS**: Configured for localhost and industrace.local
- **Cookies**: Secure, SameSite=strict
- **Proxy**: Nginx + self-signed certificates

#### **Production Cloud** (HTTPS with Traefik)
- **Frontend**: https://industrace.local (Traefik)
- **Backend**: https://industrace.local/api (Traefik proxy)
- **CORS**: Configured for production domain
- **Cookies**: Secure, SameSite=strict
- **Proxy**: Traefik + Let's Encrypt

#### **Custom Certificates** (HTTPS with Nginx)
- **Frontend**: https://yourdomain.com (nginx)
- **Backend**: https://yourdomain.com/api (nginx proxy)
- **CORS**: Configured for custom domain
- **Cookies**: Secure, SameSite=strict
- **Proxy**: Nginx + Custom certificates

### Environment Variables

Industrace uses environment variables for configuration. The system automatically manages these based on your deployment type:

```bash
# Show current configuration
make config

# Show Traefik information
make traefik
```

### Core Configuration

#### Database Settings
```bash
# PostgreSQL connection
DATABASE_URL=postgresql://user:password@localhost/industrace

# Database pool settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
```

#### Security Settings
```bash
# JWT Configuration
SECRET_KEY=your-very-secure-secret-key-here
JWT_ISSUER=industrace-api
JWT_AUDIENCE=industrace-client
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Cookie Settings
SECURE_COOKIES=true
SAME_SITE_COOKIES=strict

# MFA / TOTP (optional; defaults shown)
MFA_PENDING_TOKEN_EXPIRE_MINUTES=5
MFA_MAX_ATTEMPTS=5
MFA_LOCKOUT_MINUTES=15
MFA_BACKUP_CODES_COUNT=10
MFA_ISSUER_NAME=Industrace

# Required in production for SSO secrets and MFA TOTP secret encryption
ENCRYPTION_KEY=  # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### File Upload Settings
```bash
# Upload configuration
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=image/*,application/pdf,text/plain
```

#### API Settings
```bash
# External API
EXTERNAL_API_ENABLED=true
# Disabled by default in production; enabled in development
EXTERNAL_API_DOCS_ENABLED=true
API_KEY_HEADER=X-API-Key
API_KEY_LENGTH=32
API_KEY_PREFIX=ind_

# Setup wizard protection (required in production)
# Generated automatically by 'make prod'
SETUP_TOKEN=your-setup-token-here
```

#### Rate Limiting
```bash
# Rate limiting configuration
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/hour
RATE_LIMIT_STRICT=10/minute
```

#### Email Configuration
```bash
# SMTP settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
```

## Multi-Tenant Configuration

### Tenant Isolation
```bash
# Enable multi-tenant mode
MULTI_TENANT_ENABLED=true

# Tenant-specific settings
TENANT_DEFAULT_NAME=Default Organization
TENANT_DEFAULT_DOMAIN=default.local
```

### Tenant SMTP Configuration
Each tenant can have its own SMTP configuration through the web interface or API.

## Development Configuration

### Debug Mode
```bash
# Development settings
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### CORS Settings
```bash
# Production Local CORS
CORS_ORIGINS=https://localhost,https://127.0.0.1,https://industrace.local

# Production Cloud CORS
CORS_ORIGINS=https://industrace.local,https://www.industrace.local
```

### Development CORS (Advanced)
```bash
# Development CORS (for docker-compose.dev.yml)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
```

## Production Configuration

### Security Hardening
```bash
# Production security
DEBUG=false
ENVIRONMENT=production
SECURE_COOKIES=true
SAME_SITE_COOKIES=strict

# HTTPS settings
FORCE_HTTPS=true
HSTS_MAX_AGE=31536000
```

### Performance Settings
```bash
# Database optimization
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100

# Cache settings
CACHE_ENABLED=true
CACHE_TTL=3600

# File upload limits
MAX_FILE_SIZE=52428800  # 50MB
```

### Monitoring Configuration
```bash
# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/industrace.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5

# Metrics
METRICS_ENABLED=true
METRICS_PORT=9090
```

## Docker Configuration

### Docker Environment
```bash
# Docker-specific settings
DOCKER_ENABLED=true
DOCKER_NETWORK=industrace-network
DOCKER_VOLUME_PREFIX=industrace_
```

### Container Configuration
```yaml
# docker-compose.yml environment section
environment:
  - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/industrace
  - SECRET_KEY=${SECRET_KEY}
  - CORS_ORIGINS=${CORS_ORIGINS}
  - DEBUG=${DEBUG}
```

## Database Configuration

### PostgreSQL Settings
```sql
-- Database optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Reload configuration
SELECT pg_reload_conf();
```

### Connection Pooling
```bash
# PgBouncer configuration (optional)
PGBOUNCER_ENABLED=true
PGBOUNCER_HOST=localhost
PGBOUNCER_PORT=6432
PGBOUNCER_POOL_SIZE=20
```

## Backup Configuration

### Backup Settings
```bash
# Backup configuration
BACKUP_ENABLED=true
BACKUP_DIR=/backups/industrace
BACKUP_RETENTION_DAYS=30
BACKUP_COMPRESSION=true
BACKUP_ENCRYPTION=false
```

### Automated Backups
```bash
# Cron job for daily backups
0 2 * * * cd /path/to/industrace && python scripts/backup.py --backup-dir /backups/industrace

# Cron job for weekly backups with logs
0 2 * * 0 cd /path/to/industrace && python scripts/backup.py --backup-dir /backups/industrace --include-logs
```

## Logging Configuration

### Log Levels
```bash
# Log level configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json
LOG_DATE_FORMAT=%Y-%m-%d %H:%M:%S
```

### Log Rotation
```bash
# Log rotation settings
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5
LOG_ROTATION=midnight
```

### Log Destinations
```bash
# Log output configuration
LOG_TO_FILE=true
LOG_TO_CONSOLE=true
LOG_TO_SYSLOG=false
```

## Monitoring Configuration

### Health Checks
```bash
# Health check endpoints
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10
```

### Metrics Collection
```bash
# Prometheus metrics
METRICS_ENABLED=true
METRICS_PORT=9090
METRICS_PATH=/metrics
```

### Alerting
```bash
# Alert configuration
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_RECIPIENTS=admin@company.com
ALERT_DISK_THRESHOLD=90
ALERT_MEMORY_THRESHOLD=85
```

## Customization

### Branding Configuration
```bash
# Application branding
APP_NAME=Industrace
APP_VERSION=2.1.0
APP_DESCRIPTION=Configuration Management Database for Industrial Control Systems
```

### Feature Flags
```bash
# Feature toggles
FEATURE_EXTERNAL_API=true
FEATURE_AUDIT_LOGS=true
FEATURE_PRINT_SYSTEM=true
FEATURE_NETWORK_ANALYSIS=true
FEATURE_RISK_ASSESSMENT=true
```

### Custom Fields
```bash
# Custom field configuration
CUSTOM_FIELDS_ENABLED=true
CUSTOM_FIELDS_MAX_COUNT=10
CUSTOM_FIELDS_TYPES=text,number,date,select,boolean
```

## Validation

### Configuration Validation
```bash
# Validate configuration
python -c "from app.config import settings; print('Configuration valid')"

# Check environment variables
python scripts/validate_config.py
```

### Security Validation
```bash
# Security check
python scripts/security_check.py

# Validate secrets
python scripts/validate_secrets.py
```

## Troubleshooting

### Common Configuration Issues

#### Database Connection
```bash
# Test database connection
python -c "from app.database import engine; print('Database connected')"

# Check connection string
echo $DATABASE_URL
```

#### File Permissions
```bash
# Check upload directory permissions
ls -la uploads/

# Fix permissions
chmod 755 uploads/
chown -R 1000:1000 uploads/
```

#### Environment Variables
```bash
# Check environment variables
env | grep INDUSTRACE

# Validate required variables
python scripts/check_env.py
```

### Configuration Debugging
```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Check configuration at runtime
curl https://localhost/api/health  # Production Local
curl https://industrace.local/api/health  # Production Cloud
```

## Best Practices

### Security Best Practices
1. **Use strong secrets**: Generate cryptographically secure secrets
2. **Environment separation**: Use different configurations for dev/prod
3. **Secret management**: Use secret management tools in production
4. **Regular updates**: Keep configuration templates updated
5. **Access control**: Limit access to configuration files

### Performance Best Practices
1. **Database tuning**: Optimize database settings for your workload
2. **Connection pooling**: Use appropriate connection pool sizes
3. **Caching**: Enable caching for frequently accessed data
4. **Resource limits**: Set appropriate resource limits
5. **Monitoring**: Configure comprehensive monitoring

### Maintenance Best Practices
1. **Backup configuration**: Include configuration in backups
2. **Version control**: Keep configuration in version control
3. **Documentation**: Document all configuration changes
4. **Testing**: Test configuration changes in staging
5. **Rollback plan**: Have a rollback plan for configuration changes 