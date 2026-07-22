# Administration

Users, roles, SSO, and security policies for Industrace 2.x.

---

# Role-based access control (RBAC)


## Overview

Industrace's RBAC (Role-Based Access Control) system has been expanded to include all new features added to the system. This document describes the available permission sections and access levels for each.

## Permission Structure

The RBAC system uses a model based on **sections** and **levels**:

- **Sections**: Functional areas of the system (e.g., `assets`, `vulnerabilities`, `compliance`)
- **Levels**: Numeric access levels (0-4):
  - **0**: No access
  - **1**: Read
  - **2**: Write (modify)
  - **3**: Delete (administration)
  - **4**: Bulk/Advanced (bulk operations and advanced analytics)

## Permission Sections

### Existing Sections

These sections were already present in the original system:

- `assets` - Industrial asset management
- `sites` - Site management
- `areas` - Area management
- `locations` - Location management
- `suppliers` - Supplier management
- `contacts` - Contact management
- `manufacturers` - Manufacturer management
- `asset_types` - Asset type management
- `asset_statuses` - Asset status management
- `users` - User management
- `roles` - Role management
- `audit_logs` - Audit log viewing
- `utility` - Utility functions
- `asset_documents` - Asset document management
- `asset_photos` - Asset photo management
- `locations_floormap` - Floor plan management
- `reset_user_password` - User password reset

### New Sections

#### `vulnerabilities`
**Description**: Vulnerability and CVE management

- **Level 1 (Read)**: View vulnerabilities and asset vulnerabilities
- **Level 2 (Write)**: Create/update vulnerabilities, manage asset vulnerability status
- **Level 3 (Delete)**: Delete vulnerabilities, manage vulnerability feeds
- **Level 4 (Bulk)**: Bulk operations on vulnerabilities

**Protected endpoints**:
- GET `/vulnerabilities` - List vulnerabilities
- GET `/vulnerabilities/{id}` - Vulnerability detail
- POST `/vulnerabilities` - Create vulnerability
- GET `/vulnerabilities/assets/{asset_id}` - Asset vulnerabilities
- PUT `/vulnerabilities/assets/{asset_id}/vulnerabilities/{id}` - Update vulnerability status
- GET/POST `/vulnerabilities/feeds` - Vulnerability feed management

#### `asset_reviews`
**Description**: Asset review and maintenance management

- **Level 1 (Read)**: View review status and due/overdue assets
- **Level 2 (Write)**: Mark assets as reviewed, skip review
- **Level 3 (Delete)**: Recalculate all review dates, bulk operations
- **Level 4 (Bulk)**: Full review management

**Protected endpoints**:
- GET `/assets/{id}/review-status` - Asset review status
- POST `/assets/{id}/review` - Mark asset as reviewed
- POST `/assets/{id}/review/skip` - Skip review
- GET `/assets/review/due` - Due assets
- GET `/assets/review/overdue` - Overdue assets
- POST `/assets/review/bulk` - Bulk review
- POST `/assets/review/recalculate-all` - Recalculate all dates

#### `asset_dependencies`
**Description**: Asset dependency management

- **Level 1 (Read)**: View asset dependencies
- **Level 2 (Write)**: Create/update dependencies
- **Level 3 (Delete)**: Delete dependencies
- **Level 4 (Bulk)**: Run advanced analysis (risk propagation, impact analysis)

**Protected endpoints**:
- GET `/asset-dependencies` - List dependencies
- POST `/asset-dependencies` - Create dependency
- PUT/DELETE `/asset-dependencies/{id}` - Update/delete dependency
- GET `/asset-dependencies/assets/{id}/risk-propagation` - Risk propagation
- GET `/asset-dependencies/assets/{id}/impact-analysis` - Impact analysis

#### `compliance`
**Description**: ISA/IEC 62443 compliance management

- **Level 1 (Read)**: View compliance status, SR assessments
- **Level 2 (Write)**: Create/update SR assessments, manage evidence
- **Level 3 (Delete)**: Full compliance, zones, conduits, capabilities management
- **Level 4 (Bulk)**: Full compliance administration

**Protected endpoints**:
- GET `/compliance/zone/{id}/foundation-requirements` - Foundation Requirements
- GET `/compliance/zone/{id}/security-requirements/{fr_id}` - Security Requirements
- GET `/compliance/zone/{id}/sr/{sr_id}/assessment-assist` - Assessment assist
- POST `/compliance/zone/{id}/sr/{sr_id}/assessment` - Create/update assessment
- GET `/compliance/gap-analysis` - Gap analysis

#### `security_zones`
**Description**: Security zone management

- **Level 1 (Read)**: View security zones and membership
- **Level 2 (Write)**: Create/update zones, manage asset membership
- **Level 3 (Delete)**: Delete zones, calculate security level
- **Level 4 (Bulk)**: Full zone management and risk analysis

**Protected endpoints**:
- GET `/security-zones` - List zones
- POST `/security-zones` - Create zone
- PUT/DELETE `/security-zones/{id}` - Update/delete zone
- GET `/security-zones/{id}/assets` - Assets in zone
- GET `/security-zones/{id}/compliance` - Zone compliance
- POST `/security-zones/{id}/calculate-sl` - Calculate Security Level
- POST `/security-zones/{id}/memberships` - Membership management

#### `notifications`
**Description**: Notification and preference management

- **Level 1 (Read)**: View personal notifications and logs
- **Level 2 (Write)**: Manage personal preferences, send test notifications
- **Level 3 (Delete)**: Manage notification templates, notification queue
- **Level 4 (Bulk)**: Full notification administration

**Protected endpoints**:
- GET `/notifications/preferences` - Personal preferences
- POST/PUT/DELETE `/notifications/preferences/{id}` - Preference management
- GET `/notifications/templates` - Notification templates
- PUT `/notifications/templates/{code}` - Update template (admin)
- GET `/notifications/queue` - Notification queue (admin)
- POST `/notifications/test` - Test notification

#### `sso`
**Description**: Single Sign-On management

- **Level 1 (Read)**: View SSO configuration (only if enabled)
- **Level 2 (Write)**: Configure SSO, test connection
- **Level 3 (Delete)**: Import users from SSO provider
- **Level 4 (Bulk)**: Full SSO administration

**Protected endpoints**:
- GET `/auth/sso/config` - SSO configuration
- POST/PUT/DELETE `/auth/sso/config` - Configuration management
- POST `/auth/sso/test` - Test connection
- GET `/auth/sso/azure-ad/users` - Azure AD user list
- POST `/auth/sso/azure-ad/import` - Import users

#### `api_keys`
**Description**: API key management for external integrations

- **Level 1 (Read)**: View own API keys
- **Level 2 (Write)**: Create/update own API keys
- **Level 3 (Delete)**: Delete own API keys, manage all API keys
- **Level 4 (Bulk)**: Full API key administration

#### `evidence`
**Description**: Compliance evidence management

- **Level 1 (Read)**: View evidence
- **Level 2 (Write)**: Create/update evidence
- **Level 3 (Delete)**: Delete evidence
- **Level 4 (Bulk)**: Full evidence management

## Predefined Roles

### Admin (Level 3 - Full Administration)

Full access to all sections:

| Section | Level | Description |
|---------|-------|-------------|
| All base modules | 3 | Full asset, site, area management, etc. |
| `vulnerabilities` | 3 | Full vulnerability and CVE management |
| `asset_reviews` | 3 | Full review and maintenance management |
| `asset_dependencies` | 3 | Full dependency and analysis management |
| `compliance` | 3 | Full ISA/IEC 62443 management |
| `security_zones` | 3 | Full security zone management |
| `evidence` | 3 | Full compliance evidence management |
| `notifications` | 3 | Full notification and template management |
| `sso` | 3 | Full Single Sign-On configuration |
| `api_keys` | 3 | Full API key management |
| `reset_user_password` | 1 | User password reset |

### Editor (Level 2 - Edit)

Read/write access to operational sections:

| Section | Level | Description |
|---------|-------|-------------|
| Base modules | 2 | Edit assets, sites, areas, etc. |
| `vulnerabilities` | 2 | Vulnerability and status management |
| `asset_reviews` | 2 | Review and maintenance management |
| `asset_dependencies` | 2 | Dependency management |
| `security_zones` | 2 | Zone and membership management |
| `evidence` | 2 | Evidence management |
| `notifications` | 2 | Personal preference management |
| `compliance` | 1 | Read-only ISA/IEC 62443 |
| `sso` | 1 | Read-only SSO configuration |
| `api_keys` | 1 | View own API keys |
| `users`, `roles` | 1 | Read-only users and roles |

### Viewer (Level 1 - Read Only)

Read-only access to sections:

| Section | Level | Description |
|---------|-------|-------------|
| All base modules | 1 | Read-only assets, sites, areas, etc. |
| `vulnerabilities` | 1 | Read-only vulnerabilities |
| `asset_reviews` | 1 | Read-only review status |
| `asset_dependencies` | 1 | Read-only dependencies |
| `compliance` | 1 | Read-only ISA/IEC 62443 |
| `security_zones` | 1 | Read-only security zones |
| `evidence` | 1 | Read-only evidence |
| `notifications` | 1 | Read-only personal notifications |
| `users` | 0 | **No access** |
| `sso` | 0 | **No access** |
| `api_keys` | 0 | **No access** |

## Code Usage

### Backend (FastAPI)

```python
from app.services.rbac import require_permission

@router.get("/endpoint")
def my_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 1)),  # Read permission
):
    # Endpoint code
    pass
```

### Programmatic Check

```python
from app.services.rbac import check_permission, get_user_permission_level

# Check if the user has a permission
if check_permission(current_user, "vulnerabilities", 2):
    # User can modify vulnerabilities
    pass

# Get the permission level
level = get_user_permission_level(current_user, "vulnerabilities")
```

## Role Update

### Automatic Update (During Upgrade)

When you upgrade the system, the Alembic migration `update_roles_permissions` will automatically update all roles with the missing permissions.

### Manual Update

To manually update existing roles with the new permission sections, run:

```bash
# Via Makefile (recommended)
make update-roles

# Or directly
docker-compose -f docker-compose.prod.yml exec backend python scripts/update_roles.py
```

This script automatically updates all roles (admin, editor, viewer) for all tenants in the system, ensuring all permissions are present.

## Notes

- Permissions are inherited if the role has a `parent_role` and `is_inheritable` is `True`
- Child role permissions take precedence over parent role permissions
- Permissions are stored as JSON in the `permissions` field of the `Role` model
- The system supports multi-tenancy: each tenant has its own roles and permissions

---

# SSO with Azure AD


This guide will help you configure Single Sign-On (SSO) authentication between Industrace and Azure AD (Microsoft 365 / Entra ID).

## Prerequisites

- Administrator access to Microsoft Azure Portal
- Administrator access to Industrace
- Active Microsoft 365 / Azure AD tenant

## Step 1: Register the Application in Azure AD

### 1.1 Sign in to Azure Portal

1. Go to [https://portal.azure.com](https://portal.azure.com)
2. Sign in with a tenant administrator account
3. Navigate to **Azure Active Directory** (or **Microsoft Entra ID**)

### 1.2 Register a New Application

1. In the left menu, select **App registrations**
2. Click **+ New registration**
3. Fill in the form:
   - **Name**: `Industrace SSO` (or a name of your choice)
   - **Supported account types**:
     - Select **Accounts in this organizational directory only** for maximum security
     - Or **Accounts in any organizational directory** if you need to support multiple tenants
   - **Redirect URI**:
     - Platform: **Web**
     - URI: `https://yourdomain.com/api/auth/sso/azure_ad/callback`
     - ⚠️ **IMPORTANT**: Replace `yourdomain.com` with your actual domain
     - Example: `https://industrace.local/api/auth/sso/azure_ad/callback` (for local development)
     - Example: `https://app.industrace.com/api/auth/sso/azure_ad/callback` (for production)
4. Click **Register**

### 1.3 Note the Application Information

After registration, note the following:

- **Application (client) ID**: This is your `Client ID`
- **Directory (tenant) ID**: This is your `Tenant Domain` (you can also use the tenant name, e.g. `contoso.onmicrosoft.com`)

## Step 2: Configure Authentication

### 2.1 Configure Redirect URIs

1. On the application page, go to **Authentication**
2. Under **Redirect URIs**, add:
   - `https://yourdomain.com/api/auth/sso/azure_ad/callback`
   - `https://yourdomain.com/api/auth/sso/azure_ad/authorize` (optional, for direct redirect)
3. Under **Implicit grant and hybrid flows**, ensure:
   - ✅ **ID tokens** is selected (required for OIDC)
   - ❌ **Access tokens** can be unchecked (not required for the base flow)
4. Click **Save**

### 2.2 Configure API Permissions

1. Go to **API permissions**
2. Verify the following are present:
   - **Microsoft Graph** > **openid** (Delegated) - ✅ Already present
   - **Microsoft Graph** > **profile** (Delegated) - ✅ Already present
   - **Microsoft Graph** > **email** (Delegated) - ✅ Already present
   - **Microsoft Graph** > **User.Read** (Delegated) - Add if not present
3. **IMPORTANT**: If you need to import users, also add:
   - **Microsoft Graph** > **User.Read.All** (Application) - ⚠️ **REQUIRED** to import users
   - This permission must be of type **Application** (not Delegated) to work with the client credentials flow
   - ⚠️ **Requires admin consent**
4. Click **Grant admin consent** - **REQUIRED** for Application permissions
5. ⚠️ **Note**: Without **User.Read.All (Application)** permission and admin consent, user import will not work

## Step 3: Create a Client Secret

### 3.1 Generate the Secret

1. Go to **Certificates & secrets**
2. Under **Client secrets**, click **+ New client secret**
3. Fill in:
   - **Description**: `Industrace SSO Secret` (or a descriptive name)
   - **Expires**: Choose an expiry (recommended: 24 months for production)
4. Click **Add**
5. ⚠️ **IMPORTANT**: Copy the **Value** of the secret immediately (you will only see it once!)
   - This is your `Client Secret`

## Step 4: Configure Industrace

### 4.1 Access SSO Configuration

1. Log in to Industrace as an administrator
2. Go to **SSO Config**
3. If no configuration exists yet, click **Start Setup**

### 4.2 Fill in the Configuration Form

Fill in the following fields:

- **Provider Type**: Select `Azure AD (EntraID)`
- **Enabled**: Enable when you are ready to test
- **Client ID**: Paste the **Application (client) ID** from Step 1.3
- **Client Secret**: Paste the **Value** of the secret from Step 3.1
- **Tenant Domain**:
  - You can use the **Directory (tenant) ID** (UUID)
  - Or the tenant name (e.g. `contoso.onmicrosoft.com`)
  - Or `common` to support personal Microsoft accounts (not recommended for enterprise)
- **Redirect URI**:
  - Must match exactly what is configured in Azure AD
  - Example: `https://yourdomain.com/api/auth/sso/azure_ad/callback`
- **Auto-Provisioning**:
  - ⚠️ **Recommended: DISABLED** for maximum security
  - If disabled, only users who already exist in Industrace can sign in
  - Existing users are linked automatically if the email matches
- **Domain Restriction** (optional):
  - Example: `contoso.com` to allow only users from this domain

### 4.3 Test the Connection

1. Click **Test Connection**
2. If the test succeeds, proceed to the next step
3. If it fails, verify:
   - Client ID and Client Secret are correct
   - Redirect URI matches exactly
   - API permissions are configured correctly

### 4.4 Save the Configuration

1. Click **Save**
2. Enable **Enabled** if you have not already
3. The configuration is now active!

## Step 5: Import Users (Optional)

### 5.1 Import Users from Azure AD

1. On the SSO Config page, go to the **Import Users** tab
2. Search for users you want to import (you can filter by name or email)
3. Select the users to import
4. Choose the **Role** to assign to the imported users
5. Click **Import Selected**

### 5.2 Verify Imported Users

1. Go to **Users** in Industrace
2. Verify that the users were created correctly
3. Imported users will have:
   - Email matching the one in Azure AD
   - Role assigned during import
   - `auth_provider` set to `azure_ad`

## Step 6: Test SSO Login

### 6.1 Test Login

1. Log out of Industrace
2. Go to the login page
3. You should see a **"Sign in with Microsoft"** button (or similar)
4. Click the button
5. You will be redirected to Microsoft for authentication
6. After authentication, you will be redirected back to Industrace automatically

### 6.2 Verify User Linking

1. After SSO login, go to **Profile**
2. Verify that the user was linked correctly:
   - The user should have `auth_provider` = `azure_ad`
   - The user should have `external_id` populated

## Troubleshooting

### Issue: "Invalid redirect URI"

**Cause**: The Redirect URI in Industrace does not match the one configured in Azure AD.

**Solution**:
- Verify that the Redirect URI in Industrace matches exactly the one in Azure AD
- Check for extra spaces or special characters
- Ensure the protocol is correct (http vs https)

### Issue: "Invalid client secret"

**Cause**: The Client Secret has expired or is incorrect.

**Solution**:
- Generate a new Client Secret in Azure AD
- Update the configuration in Industrace with the new secret

### Issue: "User not found" during login

**Cause**: The user does not exist in Industrace and auto-provisioning is disabled.

**Solution**:
- Import the user manually via the "Import Users" feature
- Or enable auto-provisioning (not recommended for security)

### Issue: "Domain restriction violation"

**Cause**: The user's email does not match the domain configured in Domain Restriction.

**Solution**:
- Verify the user's domain in Azure AD
- Update Domain Restriction to include the correct domain
- Or remove Domain Restriction if not needed

### Issue: SSO button does not appear on the login page

**Cause**: SSO configuration is not enabled or is not configured correctly.

**Solution**:
- Verify that **Enabled** is turned on in the SSO configuration
- Verify that the configuration was saved correctly
- Check backend logs for any errors

### Issue: Error 500 when listing/importing Azure AD users

**Cause**: The Azure AD application does not have the correct permissions or admin consent has not been granted.

**Solution**:
1. Verify that **User.Read.All (Application)** permission has been added (not Delegated!)
2. Verify that **admin consent** has been granted (Grant admin consent)
3. Check backend logs for the specific error:
   - If you see "Failed to authenticate" → issue with Client ID/Secret or tenant
   - If you see "Insufficient privileges" → User.Read.All (Application) permission is missing
   - If you see "consent required" → admin consent is missing
4. After adding permissions, wait a few minutes before retrying (Azure AD may take time to propagate permissions)

## Important Notes

### Security

- ⚠️ **Never share the Client Secret**: It is a sensitive credential
- ⚠️ **Use HTTPS in production**: The Redirect URI must use HTTPS
- ⚠️ **Auto-provisioning disabled**: Recommended for maximum security
- ⚠️ **Domain Restriction**: Use to limit access to specific domains

### Best Practices

1. **Test in a development environment before production**
2. **Use long-expiry secrets** (24 months) to avoid disruption
3. **Document the configuration** for your team
4. **Monitor logs** for any issues
5. **Rotate secrets** before they expire

## Support

For issues or questions:
- See Azure AD documentation: [https://docs.microsoft.com/azure/active-directory/](https://docs.microsoft.com/azure/active-directory/)
- Contact Industrace support

---

# Password policy


## Version: v1.1.0+

### ⚠️ Important: Password Security Changes

Starting from this version, Industrace implements stricter security requirements for user passwords, in line with industrial security best practices and ISA/IEC 62443 standards.

---

## Multi-factor authentication (MFA / TOTP)

**Available from the MFA feature set (v2.3.x).** Local password users can enable TOTP (Google Authenticator, Authy, 1Password, etc.) from **Profile**.

### User enrollment

1. Sign in with email/password
2. Open **Profile** → **Two-factor authentication** → **Enable MFA**
3. Scan the QR code (or enter the secret manually)
4. Confirm with a 6-digit code
5. Save the **recovery codes** shown once

At the next login, after the password step, Industrace asks for the authenticator code (or a recovery code).

### Tenant policy (SSO Config page)

| Policy | Behaviour |
|--------|-----------|
| `optional` (default) | Users opt in; self-service disable allowed |
| `required_admins` | Local admin users must enroll within the grace period |
| `required_all` | All local password users must enroll within the grace period |

Grace period defaults to **7 days** (`mfa_enrollment_deadline_days`). After the deadline, login returns `MFA_SETUP_REQUIRED` until enrollment completes.

**SSO-only users** are not forced through Industrace TOTP — use IdP MFA (e.g. Azure AD Conditional Access). That satisfies pilot MFA requirements when configured.

### Admin reset

On **Users → user detail**, admins with `users` write permission can **Reset MFA**. If SMTP is configured for the tenant, the user receives a notification email.

### Recovery

- Use a one-time recovery code on the MFA verify screen
- Or ask an admin to reset MFA, then re-enroll

See also [MFA_TOTP_IMPLEMENTATION.md](MFA_TOTP_IMPLEMENTATION.md).

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
