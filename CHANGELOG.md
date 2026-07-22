# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **MFA/TOTP**: two-factor authentication for local password users (RFC 6238), backup codes, tenant MFA policy (`optional` / `required_admins` / `required_all`), admin reset, Profile enrollment UI, and login verification step

### Security
- TOTP secrets encrypted at rest (Fernet); backup codes stored as bcrypt hashes; MFA lockout and rate limiting on `/login/mfa`

## [2.2.0] - 2026-07-15

### Added
- **CSV import/export**: bulk import for users, sites, and locations (UI dialogs + templates)
- **Deep health checks**: `/health` verifies database and Redis (SSO state); Docker healthchecks on backend and Postgres
- **CI coverage gate**: progressive backend coverage threshold via `.coveragerc` (critical modules)
- **Probe statistics API**: `GET /network-probes/{id}/statistics` with `time_range` (`24h`, `7d`, `30d`)
- **Device matches API**: `GET /discovered-devices/{id}/matches` for asset match candidates
- **Probe runbook**: [probe/RUNBOOK.md](probe/RUNBOOK.md) — daily checks, incident flow, pilot go-live checklist
- **Probe tests**: `test_probe_pilot_stable.py` for statistics and matching

### Changed
- **IEC 62443 zone compliance**: filter SR-relevant assets; show technical characteristics in compliance UI
- **Network Probes docs**: status upgraded to *pilot-stable* in [probe/NETWORK_PROBE.md](probe/NETWORK_PROBE.md)
- **Discovered device matching**: shared `DiscoveredDeviceService` (list + matches endpoint)

### Fixed
- **Asset detail**: real counts for relation badges and critical vulnerability indicators (no placeholder stubs)

## [2.1.1] - 2026-06-29

### Added
- Router-level RBAC enforcement on core API endpoints (`require_section_access`)
- Setup wizard protection via `SETUP_TOKEN` and `X-Setup-Token` header
- Backend API RBAC and setup protection tests with `pytest-cov` in CI
- [Pilot Deployment Checklist](docs/PILOT_DEPLOYMENT_CHECKLIST.md) for controlled production pilots
- [IEC 62443 scope and limits guide](docs/IEC62443.md) — module coverage, boundaries, and certification disclaimer

### Changed
- JWT authentication relies on HttpOnly cookies in the frontend (removed `localStorage` token storage)
- `EXTERNAL_API_DOCS_ENABLED` defaults to `false` in production
- Performance testing router disabled when `ENVIRONMENT=production`
- `EXTERNAL_API_ENABLED` now controls mounting of the external API router
- Updated `SECURITY.md`, `CONTRIBUTING.md`, and `CONFIGURATION.md` for v2.1.x

### Security
- Extended RBAC to assets, sites, users, suppliers, and other core routers
- Tenant endpoints now require authenticated admin-level access
- Production setup endpoints require `SETUP_TOKEN`

## [2.1.0] - 2026-06-17

### Added

#### Network Probes
- **Network probe system**: models, API, service, RBAC permission `network_probes`
- **Discovered devices**: listing with asset matching, onboard as asset, status management
- **Probe client** (`probe/network_probe_client.py`): Scapy sniffing, heartbeat, data transmission, remote config sync
- **Hardening**: API key via `X-API-Key` header, rate limiting, MAC dedup, stale probe detection, telemetry retention
- **UI**: NetworkProbes and DiscoveredDevices pages with i18n (en/it)
- **Background job**: hourly probe maintenance (stale status + retention purge)

#### Syslog external forwarding
- Tenant syslog configuration (`external_log` RBAC), audit log forwarding via BSD syslog

#### IEC 62443 enhancements
- Requirement Enhancement (RE 1–4) texts for all 52 SR; RE-level assessment and audit export CSV/JSON

### Changed
- **IEC 62443 UI**: removed legacy `assessCompliance` API calls; zone assessments use `POST /compliance/zone/{id}/sr/{sr_id}/assessment`
- **Dashboard compliance summary**: aligned with `ISA62443ComplianceEngine` SL-A logic
- **SSO**: login success uses httponly cookie only (no JWT in query string); frontend bootstraps session via `/refresh`
- **`/refresh` endpoint**: returns `access_token` in JSON body for API interceptor bootstrap
- **Production config**: `ENCRYPTION_KEY` required when `ENVIRONMENT=production`

### Fixed
- Probe client stops after persistent 401 (de-authorize)
- Discovered device matching performance (hash map instead of nested loops)
- SQLite test compatibility for JSONB probe/discovered device columns

### Tests
- Re-enabled backend pytest in CI and `make test` (40 tests: IEC 62443, network probe, SSO encryption, log sanitizer)

## [2.0.0] - 2026-02-12

### Added

#### ISA/IEC 62443 and Security Zones
- **Security Zones**
  - Models: `SecurityZone`, `AssetZoneMembership`, `Conduit`, `ConduitAsset`
  - Full CRUD for zones, asset–zone membership, conduits between zones
  - Routers `security_zones.py`, `conduits.py`; pages SecurityZones, SecurityZoneDetail, Conduits
  - Zone risk calculation (`ZoneRiskCalculator`), risk propagation
- **ISA/IEC 62443 Compliance**
  - Models: `SecurityRequirement`, `SecurityCapability`, `SrAssessment`, `SrAssessmentEvidence`, `SecurityRequirementCompliance`, `SrCapability`
  - Compliance engine `ISA62443ComplianceEngine` (SL-A, SL-C, capabilities, requirements)
  - Router `compliance.py`; Asset Detail IEC 62443 tab, Compliance page
  - Init data: security requirements, capabilities, SR–capability mappings
- **Evidence System**
  - Model and CRUD for `Evidence` (compliance evidence)
  - Evidence API and router; docs `EVIDENCE_SYSTEM.md`, `TEST_EVIDENCE_API.md`

#### Vulnerability Intelligence
- **Vulnerability and CVE management**
  - `Vulnerability` model, tables and migrations for vulnerability intelligence
  - CRUD for vulnerabilities, feeds, automatic matching (`VulnerabilityMatcher`, `VulnerabilityAutoMatch`, `VulnerabilityFeed`, `VulnerabilityImpact`)
  - Router `vulnerabilities.py`; pages Vulnerabilities, VulnerabilityDetail, VulnerabilityFeeds
  - Asset Detail Vulnerabilities tab; integration with risk scoring
- Documentation: `VULNERABILITIES_DESIGN.md`, `VULNERABILITIES_STATUS.md`

#### Asset Dependencies and Review
- **Asset dependencies**
  - Model `AssetDependency`; CRUD and router `asset_dependencies.py`
  - Asset Detail Dependencies tab, risk propagation graph (`ConnectionDependencyAnalyzer`, `RiskPropagation`)
- **Asset Review (maintenance/review)**
  - Models and fields for review/next_review; router `asset_reviews.py`, service `AssetReviewService`
  - AssetReviews page, Asset Detail Review tab, `AssetReviewTable` component

#### Notifications
- **Notification system**
  - Models: `NotificationTemplate`, `NotificationQueue`, `NotificationLog`, `NotificationPreference`
  - Router `notifications.py`; services `NotificationService`, `EmailQueueProcessor`
  - Notifications page with tabs: Templates, Queue, Logs, Preferences, Test
  - Migrations and template init (`init_notification_templates`)

#### Single Sign-On (SSO) / Enterprise Auth
- **Azure AD SSO**
  - Model `TenantSsoConfig`; services `SSOAuth`, `AzureAdService`, `SSOEncryption`
  - Router `sso.py`; pages SSOConfig, SSOSuccess, SSOError; Login integration
  - Migration `add_enterprise_auth`; docs `SSO_AZURE_AD_SETUP.md`, `ENTERPRISE_AUTH_DESIGN.md`

#### Security and Permissions
- **Extended RBAC**
  - New permissions: vulnerabilities, asset_reviews, asset_dependencies, compliance, security_zones, evidence, notifications, sso, api_keys
  - Scripts `expand_rbac_permissions.py`, `update_roles_permissions.py`; doc `RBAC_PERMISSIONS.md`
- **Password policy**
  - Stronger requirements (12+ chars, upper, lower, digit, special character)
  - Doc `UPGRADE_PASSWORD_POLICY.md`; upgrade notes in `UPGRADE_NOTES_v1.1.0.md`
- **Security logging and hardening**
  - `SecurityLogging` service; account lockout and additional user fields (migrations)
  - SSO client secret encryption; encryption initialization fix

#### UI and Asset Detail
- **New Asset Detail layout**
  - Page `AssetDetailNew.vue`; Header, Sidebar, tabs: Management, Overview, Relations, Security, Risk, Connections, Dependencies, Vulnerabilities, IEC 62443, Review
  - Components: `AssetDetailSection`, `AssetDetailSidebar`, `AssetAlertBanner`, `RiskPropagationView`
- **Dashboard**
  - Components `DashboardCard`, `SectionHeader`, `RecentChangesList`; Dashboard page extensions
- **Print**
  - Improvements to `AssetCardPrint`, language parameter for printed kit

#### Backend and Infrastructure
- **API and services**
  - Routers: `asset_capabilities.py`, `asset_reviews.py`, `dashboards.py`, `evidence.py`; extended `smtp_config.py`
  - Services: `FileValidation`, extended `RateLimiter`, `RiskCache`, `BackgroundTasks`
- **Database**
  - Multiple Alembic migrations: capability, ISA62443, notifications, vulnerability, evidence, zone membership, conduit, review, lockout, manufacturer soft-delete, etc.
- **Configuration**
  - `custom-certs.env.example`, `docker-compose.custom-certs.yml`; updates to `.env.example`, `docker-compose.yml`, `docker-compose.prod.yml`
  - Makefile: review and improvements for build, backup, deploy, dev, test targets

#### Documentation
- `docs/ISA62443_DESIGN.md`, `docs/ISA_IEC_62443_IMPLEMENTATION_RECAP.md`
- Consolidated docs: `docs/MIGRATION.md`, `docs/ADMINISTRATION.md`, `docs/API.md`, `docs/IEC62443.md`
- `UPGRADE_NOTES_v1.1.0.md` (upgrade and password policy notes)
- `scripts/check-secrets.sh` for secret verification

### Changed
- **Assets**: Extended CRUD and router `assets.py` (filters, fields, zone/capability/dependency/vulnerability relations); form and tabs updated; Italian comments/strings translated to English where applicable
- **Roles and permissions**: `init_roles.py`, `RoleForm.vue`, `RoleDetails.vue`; permissions aligned to new modules
- **Email**: Improved email queue error handling; `EmailService` and SMTP config updates
- **Frontend**: `AssetsFilters.vue` (advanced filters); removal of `AssetsAdvancedFilters.vue`; unit tests `AssetsFilters.test.js`; IT/EN translations updated (assets, dashboard, menu, sso, roles, setup, vulnerabilities, assetDependencies, assetReviews, isa62443, notifications)
- **Configuration**: `config.py`, `main.py` (router mount, middleware, security); `requirements.txt`; `development.env.example`, `production.env.example`
- **Init and demo**: `init_demo_data.py` extended for zones, conduits, capabilities, vulnerabilities, notifications, SSO; `init_manufacturers.py`, `init_asset_statuses.py`, `init_asset_types.py`
- **Print**: `print.py` and `AssetCardPrint.vue` with multilingual support and layout improvements

### Fixed
- Vulnerability matching and PrimeIcons usage
- SSO: client secret management and encryption initialization
- Email queue error handling and role permissions update
- AssetsFilters tests: dropdown value change, filter props, PrimeVue plugin, dependencies
- Italian comments/strings translated to English in `assets.py`

### Removed
- `SECURITY_REVIEW.md`
- `frontend/ASSET_DETAIL_NEW_DESIGN.md`, `frontend/ASSET_DETAIL_NEW_LAYOUT.md`, `frontend/TEST_CHECKLIST_FILTRI.md`
- Backend tests: `test_performance.py`, `test_auth.py`, `test_comprehensive.py` (and partial test_users removal)
- `scripts/deploy.sh`
- `AssetsAdvancedFilters.vue` (logic merged into `AssetsFilters.vue`)

### Migration
- New tables: asset_dependencies, capability/SR/ISA62443-related, notification_*, vulnerability_*, evidence, security_zone, conduit, asset_zone_membership, tenant_sso_config, enterprise auth
- New/updated columns: manufacturer `deleted_at`, user (lockout, notifications), asset (review), conduit/governance, vulnerability status default, account lockout, role on asset_contacts, etc.
- Merge heads and constraint fixes (notification template, vulnerability status, conduit/review)

### Technical
- Backend: New routers and services for compliance, vulnerabilities, zones, conduits, notifications, SSO, evidence, dashboards, asset capabilities/reviews/dependencies
- Frontend: New pages and tabs for Security Zones, Conduits, Compliance, Vulnerabilities, Notifications, SSO; redesigned Asset Detail
- Database: Full set of Alembic migrations for 2.0; see `docs/MIGRATION.md` for moving from v1.x

## [1.1.0] - 2025-12-04

### Added
- **Trash Management for Areas**
  - Soft delete for areas with `deleted_at` column
  - Endpoint `/areas/trash` to view deleted areas
  - Endpoint `PATCH /areas/{id}/restore` to restore areas
  - Endpoint `DELETE /areas/{id}/hard` for permanent deletion
  - Endpoint `DELETE /areas/trash/empty` to empty trash
  - UI aligned with Sites and Locations for trash management

- **Multilingual Printed Kit**
  - PDF generation in Italian/English
  - Automatic support based on user interface language
  - `language` parameter in API request
  - Complete translations for all printed kit sections

- **Restructured Translation System**
  - Translation file consolidation (40 files deleted, 19 new)
  - Complete IT/EN translation alignment
  - New centralized loader (`loader-final.js`)
  - Translation automation scripts (`sync-translations.js`, `translate-keys.js`)
  - New translation files: `auditlog.json`, `globalsearch.json`, `pcap.json`, `areas.json`

- **Improved Global Search**
  - Fixed join with Area for Locations
  - Auto-search when query changes
  - Improved result descriptions with area name
  - Fixed search that wasn't finding results

- **Performance Optimizations**
  - New database indexes to improve query performance
  - Dashboard cache (`dashboard_cache.py`)
  - Performance test scripts

- **Documentation**
  - Complete upgrade guide (`docs/UPGRADE.md`)
  - Performance documentation

### Changed
- **Translation System**
  - Complete translation system restructuring
  - Consolidation of fragmented files into unified files
  - Deleted old files: `assetCommunications.json`, `assetConnections.json`, `assetCustomFields.json`, `assetDetail.json`, `assetForm.json`, `auditLogs.json`, `documents.json`, `errors.json`, `forms.json`, `interfaces.json`, `permissions.json`, `utility.json`
  - New more efficient centralized loader
  - Automatic IT/EN key alignment

- **Asset Timeline**
  - Now shows only changes related to the specific asset
  - `entity_id` filter in backend
  - Improved query performance

- **Global Search**
  - Correct join with Area for Locations
  - Improved result descriptions
  - Auto-search implemented

### Fixed
- Asset timeline showed all changes instead of only those of the specific asset
- Global search didn't find results for Locations (fixed Area join)
- IT/EN translation alignment (missing keys added)
- Fixed global search that wasn't working correctly

### Migration
- Added `deleted_at` column to `areas` table (migration `f5b3589a115e`)
- Added indexes to improve query performance (migration `add_performance_indexes`)

### Technical
- Backend: New endpoints for areas trash management
- Backend: `entity_id` filter for audit logs
- Backend: `language` parameter for printed kit
- Backend: Dashboard cache implemented
- Frontend: Translation system restructuring
- Frontend: Translation automation scripts
- Database: New Alembic migrations

## [1.0.0] - 2025 august

### 🎉 Initial Release

#### Added
- **Complete Asset Management System**
  - Full lifecycle management for industrial assets
  - Asset creation, editing, deletion, and restoration
  - Bulk operations (update, delete, restore)
  - Asset duplication functionality
  - Custom fields support for flexible asset properties
  - Asset search and filtering capabilities

- **Multi-tenant Architecture**
  - Support for multiple organizations
  - Complete data isolation between tenants
  - Tenant-specific configurations
  - Multi-tenant user management

- **Role-based Access Control (RBAC)**
  - Three predefined roles: Admin, Editor, Viewer
  - Granular permissions system
  - Permission-based UI rendering
  - Role assignment and management

- **Network Topology Visualization**
  - Interactive network mapping
  - Asset connection visualization
  - Communication flow analysis
  - Network graph with zoom and pan

- **Risk Assessment Engine**
  - Advanced risk scoring algorithm
  - Composite risk calculation (Vulnerability 35%, Impact 40%, Operational 25%)
  - Risk score breakdown and suggestions
  - Automated risk recalculation
  - Risk overview dashboard

- **Document Management**
  - Asset photo upload and management
  - Document upload and organization
  - File type validation
  - Image preview and thumbnails

- **Audit Trail System**
  - Complete activity logging
  - Change tracking for all entities
  - User action history
  - Exportable audit logs
  - IP address tracking

- **Import/Export System**
  - Excel/CSV import with preview
  - Data validation before import
  - Error reporting and correction
  - Template downloads
  - Bulk data operations

- **Print System**
  - PDF report generation
  - QR code generation for assets
  - Customizable print templates
  - Print history tracking
  - Asset card printing

- **PCAP Analysis**
  - Network traffic file upload
  - Protocol detection and analysis
  - Asset communication mapping
  - Network interface discovery

- **Floor Plan Integration**
  - Floor plan upload and management
  - Asset positioning on floor plans
  - Interactive floor plan navigation
  - Visual asset placement

- **Dashboard and Analytics**
  - Real-time dashboard with metrics
  - Asset statistics and charts
  - Risk overview visualization
  - Recent activity tracking
  - System health monitoring

- **User Interface**
  - Responsive design for all devices
  - Modern Vue.js 3 interface
  - PrimeVue component library
  - Dark/light theme support
  - Internationalization (Italian/English)

- **API and Integration**
  - Complete RESTful API
  - OpenAPI/Swagger documentation
  - JWT authentication
  - API key management
  - External API endpoints

#### Technical Features
- **Backend**: FastAPI with SQLAlchemy ORM
- **Database**: PostgreSQL with Alembic migrations
- **Frontend**: Vue.js 3 with Vite build system
- **Authentication**: JWT with secure cookies
- **Containerization**: Docker and Docker Compose
- **Testing**: Pytest framework with test coverage
- **Security**: Input validation, CORS, rate limiting
- **Performance**: Optimized queries, caching support

#### Security Features
- JWT-based authentication with refresh tokens
- Role-based access control
- Input validation and sanitization
- CORS protection
- Rate limiting
- Secure cookie configuration
- Audit logging for security events

#### Deployment Features
- Docker containerization
- Docker Compose for easy deployment
- Environment-based configuration
- Health check endpoints
- Production-ready configuration
- Backup and restore capabilities

### Fixed
- Asset name clickability in tables
- Dashboard risk threshold alignment
- Table column display issues
- Checkbox visual state updates
- Comprehensive error handling
- Null checks in data table functions

### Documentation
- Complete user manual
- API documentation
- Installation guides
- Development setup instructions
- Security best practices
- Troubleshooting guide

---

## Version History

- **v2.0.0** (February 2026): ISA/IEC 62443 compliance, Security Zones, Vulnerability Intelligence, Asset Dependencies & Review, Notifications, SSO (Azure AD), extended RBAC, password policy, new Asset Detail layout
- **v1.1.0** (December 2025): Areas trash, multilingual print kit, translation restructure, global search and performance improvements
- **v1.0.0** (August 2025): Initial release with complete asset management system
