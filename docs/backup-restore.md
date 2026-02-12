# Backup and Restore Guide

This guide explains how to use the Industrace backup and restore system to protect your data and ensure business continuity.

## Overview

The Industrace backup system creates complete snapshots of your system including:
- **Database**: Complete PostgreSQL dump with all data
- **Uploads**: All uploaded files (photos, documents, floorplans)
- **Configuration**: Environment files and docker-compose configurations
- **Logs**: Application logs (optional)
- **Metadata**: Backup information and file inventory

## Backup System

### Automatic Backup

The backup system can be configured to run automatically:

```bash
# Add to crontab for daily backups at 2 AM
0 2 * * * cd /path/to/industrace && python scripts/backup.py --backup-dir /backups/industrace

# Add to crontab for weekly backups with logs
0 2 * * 0 cd /path/to/industrace && python scripts/backup.py --backup-dir /backups/industrace --include-logs
```

### Manual Backup

#### Basic Backup
```bash
# Create a basic backup (database + uploads + config)
python scripts/backup.py
```

#### Backup with Logs
```bash
# Include application logs in backup
python scripts/backup.py --include-logs
```

#### Custom Backup Directory
```bash
# Specify custom backup directory
python scripts/backup.py --backup-dir /mnt/backups/industrace
```

#### List Existing Backups
```bash
# View all available backups
python scripts/backup.py --list
```

### Backup Contents

Each backup contains:

```
industrace_backup_YYYYMMDD_HHMMSS/
├── metadata.json          # Backup information and file inventory
├── database.sql           # Complete PostgreSQL dump
├── uploads/               # All uploaded files
│   ├── documents/         # Asset documents
│   ├── photos/           # Asset photos
│   ├── prints/           # Generated PDFs
│   └── tenants/          # Tenant-specific files
├── config/               # Configuration files
│   ├── .env              # Environment variables
│   ├── docker-compose.yml
│   └── production.env.example
└── logs/                 # Application logs (if --include-logs)
    ├── industrace.log
    ├── error.log
    └── security.log
```

### Backup Metadata

The `metadata.json` file contains:

```json
{
  "backup_name": "industrace_backup_20241201_143022",
  "timestamp": "20241201_143022",
  "created_at": "2024-12-01T14:30:22.123456",
  "version": "2.0.0",
  "includes_logs": false,
  "files": [
    {
      "path": "database.sql",
      "size": 1048576,
      "modified": "2024-12-01T14:30:22.123456"
    }
  ]
}
```

## Restore System

### Prerequisites

Before restoring, ensure:
- Industrace is stopped: `docker-compose down`
- Sufficient disk space for the backup
- Database is accessible
- Backup files are available

### Restore Process

#### Step 1: Stop Services
```bash
# Stop all services
docker-compose down
```

#### Step 2: Restore Database
```bash
# Restore database from backup
python scripts/restore.py --backup-dir /path/to/backup --restore-database
```

#### Step 3: Restore Files
```bash
# Restore uploaded files
python scripts/restore.py --backup-dir /path/to/backup --restore-files
```

#### Step 4: Restore Configuration
```bash
# Restore configuration files
python scripts/restore.py --backup-dir /path/to/backup --restore-config
```

#### Step 5: Complete Restore
```bash
# Restore everything from backup
python scripts/restore.py --backup-dir /path/to/backup --restore-all
```

#### Step 6: Start Services
```bash
# Start services with restored data
docker-compose up -d
```

### Restore Options

#### Selective Restore
```bash
# Restore only database
python scripts/restore.py --backup-dir /backup --restore-database

# Restore only files
python scripts/restore.py --backup-dir /backup --restore-files

# Restore only configuration
python scripts/restore.py --backup-dir /backup --restore-config
```

#### Dry Run
```bash
# Test restore without actually restoring
python scripts/restore.py --backup-dir /backup --dry-run
```

#### Force Restore
```bash
# Force restore even if services are running
python scripts/restore.py --backup-dir /backup --force
```

## Backup Strategy

### Recommended Schedule

#### Daily Backups
- **Time**: 2:00 AM
- **Retention**: 7 days
- **Type**: Database + files
- **Location**: Local storage

#### Weekly Backups
- **Time**: Sunday 2:00 AM
- **Retention**: 4 weeks
- **Type**: Complete backup with logs
- **Location**: Local + remote storage

#### Monthly Backups
- **Time**: First Sunday of month
- **Retention**: 12 months
- **Type**: Complete backup
- **Location**: Remote storage only

### Storage Locations

#### Local Storage
```bash
/backups/industrace/
├── daily/
├── weekly/
└── monthly/
```

#### Remote Storage
- **S3 Compatible**: AWS S3, MinIO, etc.
- **SFTP**: Remote server via SSH
- **NFS**: Network file system
- **Cloud Storage**: Google Cloud, Azure, etc.

### Backup Verification

#### Verify Backup Integrity
```bash
# Verify backup files
python scripts/backup.py --verify /path/to/backup
```

#### Test Restore
```bash
# Test restore in isolated environment
python scripts/restore.py --backup-dir /backup --test-restore
```

## Disaster Recovery

### Complete System Recovery

#### Scenario: Complete System Failure
1. **Prepare New System**
   ```bash
   # Install Docker and Docker Compose
   # Clone Industrace repository
   git clone <repository-url>
   cd industrace
   ```

2. **Restore from Backup**
   ```bash
   # Copy backup to new system
   scp -r backup/ user@new-server:/path/to/industrace/
   
   # Restore complete system
   python scripts/restore.py --backup-dir /path/to/backup --restore-all
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Verify Recovery**
   ```bash
   # Check system health
   curl http://localhost:8000/health
   
   # Verify data integrity
   curl http://localhost:8000/setup/status
   ```

### Partial Recovery

#### Database Only Recovery
```bash
# Stop services
docker-compose down

# Restore database only
python scripts/restore.py --backup-dir /backup --restore-database

# Start services
docker-compose up -d
```

#### Files Only Recovery
```bash
# Restore uploaded files
python scripts/restore.py --backup-dir /backup --restore-files

# Restart services
docker-compose restart
```

## Monitoring and Alerts

### Backup Monitoring

#### Check Backup Status
```bash
# List recent backups
python scripts/backup.py --list --recent 7

# Check backup sizes
python scripts/backup.py --list --show-sizes
```

#### Backup Health Check
```bash
# Verify latest backup
python scripts/backup.py --verify-latest

# Check backup age
python scripts/backup.py --check-age
```

### Alerting

#### Failed Backup Alert
```bash
# Check if backup failed
if ! python scripts/backup.py --verify-latest; then
    echo "Backup failed!" | mail -s "Industrace Backup Alert" admin@company.com
fi
```

#### Backup Age Alert
```bash
# Alert if backup is older than 24 hours
if python scripts/backup.py --check-age --max-age 24; then
    echo "Backup is too old!" | mail -s "Industrace Backup Alert" admin@company.com
fi
```

## Troubleshooting

### Common Issues

#### Backup Fails
```bash
# Check disk space
df -h

# Check permissions
ls -la /backups/

# Check logs
docker-compose logs backend
```

#### Restore Fails
```bash
# Check backup integrity
python scripts/backup.py --verify /path/to/backup

# Check database connection
docker-compose exec db psql -U postgres -d industrace -c "SELECT 1;"

# Check file permissions
ls -la /path/to/backup/
```

#### Database Connection Issues
```bash
# Check database container
docker-compose ps db

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Performance Optimization

#### Large Database Backups
```bash
# Use compression
python scripts/backup.py --compress

# Exclude logs for faster backup
python scripts/backup.py --exclude-logs

# Use parallel processing
python scripts/backup.py --parallel
```

#### Backup Storage Optimization
```bash
# Use deduplication
python scripts/backup.py --deduplicate

# Compress old backups
python scripts/backup.py --compress-old

# Clean up old backups
python scripts/backup.py --cleanup --keep-days 30
```

## Best Practices

### Backup Best Practices
1. **Regular Schedule**: Maintain consistent backup schedule
2. **Multiple Locations**: Store backups in multiple locations
3. **Test Restores**: Regularly test restore procedures
4. **Monitor Space**: Monitor backup storage space
5. **Verify Integrity**: Verify backup integrity after creation

### Restore Best Practices
1. **Stop Services**: Always stop services before restore
2. **Test Environment**: Test restores in isolated environment
3. **Document Process**: Document restore procedures
4. **Verify Data**: Verify data integrity after restore
5. **Monitor Logs**: Monitor logs during and after restore

### Security Best Practices
1. **Encrypt Backups**: Encrypt sensitive backup data
2. **Secure Storage**: Use secure storage locations
3. **Access Control**: Limit access to backup files
4. **Audit Logs**: Maintain audit logs of backup/restore operations
5. **Regular Testing**: Regularly test disaster recovery procedures 