# Upgrade Notes - Industrace v1.1.0

**Date:** 2026-01-19  
**Version:** v1.1.0

## 🎯 Overview

This version introduces important improvements to security and permissions management:

1. **New password security policy**
2. **Role permissions update**

---

## 🔐 1. New Password Security Policy

### What's Changed

Default passwords have been updated to meet new security requirements compliant with ISA/IEC 62443 standards.

### Password Requirements

All **new passwords** must have:

- ✅ **Minimum 12 characters**
- ✅ **At least one uppercase letter** (A-Z)
- ✅ **At least one lowercase letter** (a-z)
- ✅ **At least one number** (0-9)
- ✅ **At least one special character** (!@#$%^&*(),.?":{}|<>[]\\/_+=\-~`)

### New Default Passwords

```
Admin:   admin@example.com / Admin@123456!
Editor:  editor@example.com / Editor@123456!
Viewer:  viewer@example.com / Viewer@123456!
```

**⚠️ IMPORTANT:** Change these passwords immediately after installation!

### Upgrade Impact

- ✅ **Existing users can still log in** with their current passwords
- 📝 **On first login after upgrade**, all users will be required to change their password
- 🔒 **New passwords must meet security requirements**

### Documentation

For complete details, see: [docs/UPGRADE_PASSWORD_POLICY.md](docs/UPGRADE_PASSWORD_POLICY.md)

---

## 👥 2. Role Permissions Update

### Problem Solved

Existing roles (admin, editor, viewer) did not have permissions for new modules added in previous versions.

### Permissions Added

All roles have been updated with permissions for:

- ✅ `vulnerabilities` - Vulnerability and CVE management
- ✅ `asset_reviews` - Asset review and maintenance
- ✅ `asset_dependencies` - Asset dependencies
- ✅ `compliance` - ISA/IEC 62443 Compliance
- ✅ `security_zones` - Security zones
- ✅ `evidence` - Evidence for compliance (NEW)
- ✅ `notifications` - Notification system
- ✅ `sso` - Single Sign-On
- ✅ `api_keys` - API Keys for integrations (NEW)

### Permission Levels by Role

#### Admin (Level 3 - Full Access)
All modules with level 3 (complete management)

#### Editor (Level 2 - Edit)
- Level 2 on operational modules (vulnerabilities, asset_reviews, dependencies, zones, evidence)
- Level 1 on administrative modules (compliance, sso, api_keys)

#### Viewer (Level 1 - Read-only)
- Level 1 on all modules except:
  - users: 0 (no access)
  - sso: 0 (no access)
  - api_keys: 0 (no access)

### Automatic Update

The Alembic migration `update_roles_permissions` will automatically update all roles during upgrade.

### Manual Update

If needed, you can manually update roles:

```bash
make update-roles
```

### Documentation

For complete details on permissions, see: [docs/RBAC_PERMISSIONS.md](docs/RBAC_PERMISSIONS.md)

---

## 📋 Upgrade Procedure

### Pre-Upgrade

1. **Database backup**:
   ```bash
   make backup
   ```

2. **Check current version**:
   ```bash
   docker-compose -f docker-compose.prod.yml exec backend alembic current
   ```

### Upgrade

1. **Stop the system**:
   ```bash
   make stop
   ```

2. **Update code**:
   ```bash
   git pull origin main
   ```

3. **Restart the system**:
   ```bash
   make prod
   ```

Migrations will be applied automatically on startup.

### Post-Upgrade

1. **Check logs**:
   ```bash
   make logs-backend | grep "migration\|password\|role"
   ```

2. **Verify roles** (optional):
   ```bash
   make update-roles
   ```

3. **Communicate to users** about mandatory password change

---

## 🔄 Rollback (Emergency Only)

If necessary, you can rollback migrations:

```bash
# Rollback password migration
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade -1

# Rollback roles migration
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade -1
```

⚠️ **WARNING:** Rollback is not recommended for security reasons.

---

## 📝 Post-Upgrade Checklist

After upgrade, verify that:

- [ ] System starts correctly
- [ ] Migrations were applied (check logs)
- [ ] Users can log in with current passwords
- [ ] Password change prompt is shown on login
- [ ] Roles have all necessary permissions
- [ ] New features are accessible (evidence, api_keys)

---

## 📞 Support

In case of issues:

1. Check logs: `make logs-backend`
2. Verify migrations: `docker-compose -f docker-compose.prod.yml exec backend alembic current`
3. Consult documentation: `docs/UPGRADE.md`
4. Contact support with error details

---

## 🔗 Related Documentation

- [UPGRADE.md](docs/UPGRADE.md) - General upgrade guide
- [UPGRADE_PASSWORD_POLICY.md](docs/UPGRADE_PASSWORD_POLICY.md) - Password policy details
- [RBAC_PERMISSIONS.md](docs/RBAC_PERMISSIONS.md) - RBAC permissions details
- [SECURITY.md](SECURITY.md) - Security guidelines

---

**Happy upgrading! 🚀**
