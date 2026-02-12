# Expanded RBAC System - Industrace

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
