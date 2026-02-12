# Upgrade: New Password Security Policy

## Version: v1.1.0+

### ⚠️ Important: Password Security Changes

Starting from this version, Industrace implements stricter security requirements for user passwords, in line with industrial security best practices and ISA/IEC 62443 standards.

---

## 📋 New Password Requirements

All **new passwords** must meet the following requirements:

- ✅ **Minimum 12 characters**
- ✅ **At least one uppercase letter** (A-Z)
- ✅ **At least one lowercase letter** (a-z)
- ✅ **At least one number** (0-9)
- ✅ **At least one special character** (!@#$%^&*(),.?":{}|<>[]\\/_+=\-~`)

**Examples of valid passwords:**
- `MySecure@Pass2024!`
- `Industrace#2024Secure`
- `Admin@123456!`

---

## 🔄 Upgrade Impact

### For Existing Users

**✅ GOOD NEWS:** Existing users can continue to log in with their current passwords, even if they don't meet the new requirements.

**📝 MANDATORY CHANGE:** On first login after the upgrade, all users (except demo accounts @example.com) will be required to change their password. The new password **MUST** meet the security requirements.

### For New Users

All new users created after the upgrade must have passwords that meet the security requirements, unless the `password_change_required=true` flag is set, which will force a password change on first login.

---

## 🛠️ Upgrade Procedure

### 1. Database Backup

```bash
# Always perform a backup before upgrading
make backup
```

### 2. Update the System

```bash
# Stop services
make stop

# Download new version
git pull origin main

# Rebuild images
make rebuild

# Start services
make prod
```

### 3. Automatic Migration

The Alembic migration `force_password_change_sec` will run automatically and:

- ✅ Set `password_change_required=true` for all existing users (except @example.com)
- ✅ Users will still be able to log in with their current password
- ✅ On first login, they will be required to change their password

---

## 👥 User Communication

### Suggested Email Template

```
Subject: Important Update - New Password Security Policy

Dear User,

The Industrace system has been updated with enhanced security measures.

On your next login, you will be required to change your password to meet the new security requirements:

- Minimum 12 characters
- At least one uppercase and one lowercase letter
- At least one number
- At least one special character (!@#$%^&*)

This change is necessary to ensure compliance with ISA/IEC 62443 security standards.

Your current password will continue to work until the password change.

Thank you for your cooperation.

The Industrace Team
```

---

## 🔧 Configuration Options

### Creating Users with Temporary Password

If you need to create users with passwords that don't meet the requirements (e.g., for bulk imports), you can use the `password_change_required` flag:

```python
# Example API call
POST /api/users
{
  "name": "New User",
  "email": "newuser@company.com",
  "password": "temp123",
  "role_id": "...",
  "password_change_required": true  # Allows weak password, forces change on login
}
```

### Manual Password Reset

If a user has issues, you can manually reset the password:

```bash
make reset-admin-password TENANT_SLUG="default-tenant" ADMIN_EMAIL="user@company.com"
```

This will generate a secure temporary password.

---

## 🔍 Post-Upgrade Verification

After the upgrade, verify that:

1. ✅ Users can log in with their current passwords
2. ✅ The password change prompt is displayed
3. ✅ New passwords are validated correctly
4. ✅ New users can only be created with secure passwords

```bash
# Check logs to verify migration
make logs-backend | grep "password_change"
```

---

## 📞 Support

If you encounter issues during the upgrade:

1. Check logs: `make logs-backend`
2. Verify migration: `docker-compose -f docker-compose.prod.yml exec backend alembic current`
3. Consult documentation: `docs/UPGRADE.md`

---

## 🔙 Rollback (Emergency Only)

If necessary, you can rollback the migration:

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade -1
```

⚠️ **WARNING:** Rollback will remove the password change requirement, but is not recommended for security reasons.

---

## 📚 References

- [ISA/IEC 62443-3-3](https://www.isa.org/standards-and-publications/isa-standards/isa-iec-62443-series-of-standards) - Security Requirements
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [Industrace Security Documentation](../SECURITY.md)
