# Industrace Upgrade Guide

This guide explains how to upgrade Industrace from a previous version to the latest version.

**When many changes exist between versions, upgrade risk increases.** To reduce it (backup, staging, rollback, checklist), see **[UPGRADE_SAFETY.md](UPGRADE_SAFETY.md)**.

## 🚀 Major Upgrade (v1 → v2)

If you are upgrading from **v1.x to v2**, many things may have changed (breaking changes, new env vars, new migrations). Use the dedicated guide:

- **[UPGRADE_v1_TO_v2.md](UPGRADE_v1_TO_v2.md)** – Planning, procedure, backup, staging, rollback, and checklist for the v1→v2 upgrade.

For minor/patch upgrades (e.g. 1.0 → 1.1), the procedure below is usually sufficient.

---

## ⚡ Automatic Upgrade

**Good news**: Industrace automatically handles database updates thanks to **Alembic** and the automatic startup system.

### What is handled automatically:

✅ **Database Migrations**: Applied automatically on backend startup  
✅ **Database Schema**: Updated automatically via Alembic  
✅ **New Columns/Tables**: Added automatically  
✅ **Structural Changes**: Handled via migration scripts  

## 📋 Upgrade Procedure

### Method 1: Automatic Upgrade (Recommended)

The system automatically applies migrations on startup:

```bash
# 1. Stop the system
make stop
# or
docker-compose -f docker-compose.prod.yml down

# 2. Update the code
git pull origin main  # or the branch you're using

# 3. Restart the system
make prod
# or
docker-compose -f docker-compose.prod.yml up -d
```

**What happens automatically:**
- Backend checks migration status on startup
- Automatically applies all missing migrations
- Updates database schema if needed
- System continues to work normally

### Method 2: Manual Upgrade (Optional)

If you prefer to manually control migrations:

```bash
# 1. Stop the system
make stop

# 2. Update the code
git pull origin main

# 3. Manually apply migrations
make migrate
# or
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 4. Restart the system
make prod
```

## 🔍 Checking Migration Status

You can check migration status at any time:

```bash
# Check current revision
docker-compose -f docker-compose.prod.yml exec backend alembic current

# Check available revisions
docker-compose -f docker-compose.prod.yml exec backend alembic history

# Check if there are pending migrations
docker-compose -f docker-compose.prod.yml exec backend alembic heads
```

## 📦 What is NOT handled automatically

Some changes require manual intervention:

### 1. **Environment Variables**
If new environment variables have been added, you need to update the `.env` file:

```bash
# Check example files
cat backend/production.env.example
cat backend/development.env.example

# Update your .env with new variables
```

### 2. **Python/Node Dependencies**
Dependencies are automatically updated when you rebuild containers:

```bash
# Rebuild containers to update dependencies
make rebuild
# or
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### 3. **Configuration Files**
If configuration files have been modified (e.g., `nginx.conf`, `docker-compose.yml`), you need to update them manually or merge with your customizations.

### 4. **Static/Frontend Files**
The frontend is automatically rebuilt when you rebuild containers. If you use custom builds, you might need to rebuild:

```bash
# Rebuild only frontend
docker-compose -f docker-compose.prod.yml build frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

## 🛡️ Backup Before Upgrade

**IMPORTANT**: Always backup the database before upgrading:

```bash
# Automatic backup
make backup

# Or manual backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U industrace_user industrace > backup_$(date +%Y%m%d_%H%M%S).sql
```

## 🔄 Rollback (Going Back)

If something goes wrong, you can rollback:

### Database Rollback

```bash
# 1. Restore backup
make restore
# or
docker-compose -f docker-compose.prod.yml exec -T db psql -U industrace_user industrace < backup.sql

# 2. Go back to previous code version
git checkout <previous-version-tag>
# or
git reset --hard <commit-hash>

# 3. Restart the system
make prod
```

### Migration Rollback

```bash
# Go back to a specific revision
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade <revision-id>

# Go back one revision
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade -1
```

## 📝 Pre-Upgrade Checklist

Before upgrading, verify:

- [ ] Database backup completed
- [ ] Backup of custom configuration files
- [ ] Verified no uncommitted local changes
- [ ] Read CHANGELOG.md to see changes
- [ ] Verified new environment variables are configured (if needed)

## 📝 Post-Upgrade Checklist

After upgrading, verify:

- [ ] System starts correctly
- [ ] Migrations were applied (check logs)
- [ ] Application works correctly
- [ ] Existing data is still present
- [ ] New features are available

## 🐛 Troubleshooting

### Migrations not applying

```bash
# Force migration application
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head --sql

# Check status
docker-compose -f docker-compose.prod.yml exec backend alembic current
```

### Errors during upgrade

1. **Check logs**:
   ```bash
   make logs
   # or
   docker-compose -f docker-compose.prod.yml logs backend
   ```

2. **Verify database status**:
   ```bash
   docker-compose -f docker-compose.prod.yml exec db psql -U industrace_user -d industrace -c "\dt"
   ```

3. **Restore from backup** if necessary (see Rollback section)

### System won't start after upgrade

1. Verify all migrations were applied
2. Check logs for specific errors
3. Verify environment variables are correct
4. If necessary, restore from backup

To see all available migrations:
```bash
docker-compose -f docker-compose.prod.yml exec backend alembic history
```

## 🔗 Additional Resources

- [Upgrade v1 to v2](UPGRADE_v1_TO_v2.md) – Major upgrade guide (v1.x → v2)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Installation Guide](installation.md)
- [Troubleshooting Guide](troubleshooting.md)
- [CHANGELOG](../CHANGELOG.md)

---

**Note**: If you have significant customizations or database modifications, contact support before upgrading to ensure your changes are compatible.
