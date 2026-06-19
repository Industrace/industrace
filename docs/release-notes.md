# Release Notes

## License and Author (all versions)

- **License**: GNU Affero General Public License v3.0 (AGPL-3.0)
- **Author**: Maurizio Bertaboni
- **Website**: https://besafe.it/industrace
- **Contact**: industrace@besafe.it

---

## Version 2.1.0

**Release Date**: June 17, 2026

### Overview

Industrace v2.1.0 adds **Network Probes** (distributed network discovery), **external syslog forwarding**, **IEC 62443 RE-level assessments** with audit export, and **optional IEC 62443 per tenant** (Setup). It fixes IEC 62443 legacy API usage in the UI, aligns the compliance dashboard with the SL-A engine, and hardens SSO (no JWT in URL query string).

### Key Features

#### Network Probes
- Create and manage probes from the UI; API key shown once at creation
- Probe client (`probe/`) for passive sniffing, heartbeat, and device discovery — docs: [probe/NETWORK_PROBE.md](../probe/NETWORK_PROBE.md)
- Discovered devices page with asset matching and onboard
- RBAC permission `network_probes`; rate limiting and telemetry retention

#### Syslog
- Per-tenant syslog configuration in Setup (`external_log` permission)
- Automatic audit log forwarding (non-blocking)

#### IEC 62443
- RE 1–4 normative texts for all 52 SR
- Zone audit export (CSV/JSON)
- Optional module toggle per tenant (Setup → Optional modules)

### Upgrade notes (2.0 → 2.1)

1. Run migrations: `make migrate` or `docker compose exec backend alembic upgrade head`
2. Update roles: `make update-roles` (adds `network_probes`, `external_log`)
3. Optional env vars: `PROBE_HEARTBEAT_STALE_SECONDS`, `PROBE_RETENTION_DAYS` (see `.env.example`)
4. Production: ensure `ENCRYPTION_KEY` is set if using SSO

See [MIGRATION.md](MIGRATION.md) for backup and rollback within the 2.x line.

---

## Version policy (v1 vs v2)

| Line | Status | Guidance |
|------|--------|----------|
| **1.x** (`v1.0.0`) | Frozen | Legacy only; no new features |
| **2.x** | Current | **New installation** recommended when coming from v1 — not a simple in-place upgrade |

Full policy and manual data recovery: **[MIGRATION.md](MIGRATION.md)**.

---

## Version 2.0.0

**Release Date**: February 12, 2026

### Overview

Industrace v2.0.0 is a major release introducing ISA/IEC 62443 compliance, Security Zones, Vulnerability Intelligence, Asset Dependencies and Review, a full Notification system, Single Sign-On (Azure AD), and extended RBAC with a stronger password policy. The Asset Detail page has been redesigned with a new layout and additional tabs.

**From v1.x:** treat v2 as a **new installation** and recover exportable data manually — see [MIGRATION.md](MIGRATION.md), not in-place Alembic-only upgrade as the primary path.

### Key Features

#### ISA/IEC 62443 and Security Zones
- **Security Zones**: Full CRUD for zones, asset–zone membership, conduits between zones; zone risk calculation and risk propagation
- **Compliance engine**: SL-A, SL-C, security requirements and capabilities, SR assessments with evidence
- **Evidence system**: Compliance evidence model and API for conformity documentation
- **UI**: SecurityZones, SecurityZoneDetail, Conduits pages; Asset Detail IEC 62443 tab; Compliance page

#### Vulnerability Intelligence
- **Vulnerability and CVE management**: CRUD, feeds, automatic matching to assets
- **Integration**: Vulnerability impact on risk scoring; Asset Detail Vulnerabilities tab
- **Pages**: Vulnerabilities, VulnerabilityDetail, VulnerabilityFeeds

#### Asset Dependencies and Review
- **Asset dependencies**: Model and CRUD; dependency graph and risk propagation visualization
- **Asset Review**: Maintenance/review scheduling; AssetReviews page and Asset Detail Review tab

#### Notifications
- **Notification system**: Templates, queue, logs, user preferences
- **Email**: Notification service and email queue processor; SMTP configuration per tenant
- **UI**: Notifications page (Templates, Queue, Logs, Preferences, Test tabs)

#### Single Sign-On (SSO) / Enterprise Auth
- **Azure AD SSO**: Tenant SSO configuration, encrypted client secrets, Login integration
- **Pages**: SSOConfig, SSOSuccess, SSOError
- **Documentation**: [ADMINISTRATION.md](ADMINISTRATION.md#sso-with-azure-ad)

#### Security and Permissions
- **Extended RBAC**: New permissions for vulnerabilities, asset_reviews, asset_dependencies, compliance, security_zones, evidence, notifications, sso, api_keys
- **Password policy**: Stronger requirements (12+ characters, upper, lower, digit, special character); see [ADMINISTRATION.md](ADMINISTRATION.md#password-policy)
- **Hardening**: Security logging, account lockout, SSO secret encryption

#### UI and Asset Detail
- **New Asset Detail layout**: Header, Sidebar, tabs for Management, Overview, Relations, Security, Risk, Connections, Dependencies, Vulnerabilities, IEC 62443, Review
- **Dashboard**: New card and section components; recent changes list
- **Print**: Improved asset card print and multilingual printed kit

### Migration from v1.x

- **Recommended**: Fresh v2 install + manual import of exportable v1 data — [MIGRATION.md](MIGRATION.md)
- **Password policy**: Existing users keep current password until next change; new passwords must meet the new policy
- **Roles**: Run `make update-roles` on v2; verify role assignments

Technical in-place v1→v2 migration (high risk) is documented only as a legacy note inside [MIGRATION.md](MIGRATION.md); prefer parallel/greenfield install.

### Breaking Changes and Removed Items

- Default passwords and password rules have changed; see [ADMINISTRATION.md](ADMINISTRATION.md#password-policy)
- Removed: `SECURITY_REVIEW.md`, some frontend design docs, legacy backend tests, `scripts/deploy.sh`, `AssetsAdvancedFilters.vue` (merged into `AssetsFilters.vue`)

### Documentation (2.0.0)

Consolidated user guides (2026): [README.md](README.md) — [INSTALLATION.md](INSTALLATION.md), [MIGRATION.md](MIGRATION.md), [ADMINISTRATION.md](ADMINISTRATION.md), [API.md](API.md), [IEC62443.md](IEC62443.md).

### Support and Documentation

- **Email**: industrace@besafe.it
- **Website**: https://besafe.it/industrace
- GitHub issues for bug reports
- See `docs/README.md` for documentation index

---

## Version 1.0.0 - Initial Release

**Release Date**: August 20, 2025

### Overview

Industrace v1.0.0 represents the first stable release of the Configuration Management Database for Industrial Control Systems. This release provides a comprehensive solution for managing industrial assets, network analysis, and risk assessment.

### Key Features

#### Multi-Deployment Support
- **Development**: Vite dev server with hot-reload
- **Production**: Traefik + Let's Encrypt for automatic SSL
- **Custom Certificates**: Nginx + custom SSL certificates
- **Automatic Configuration**: CORS, cookies, and security settings

#### Multi-Tenant Architecture
- Complete tenant isolation with secure data separation
- Tenant-specific user and role management
- Customizable SMTP configurations per tenant
- Multi-organization support

#### Asset Management
- Comprehensive industrial asset catalog
- Asset classification by type, status, and criticality
- Location management with floor plan support
- Photo and document attachments
- Customizable asset fields

#### Network Analysis
- Asset connection mapping and visualization
- Network communication analysis (PCAP support)
- Automatic protocol identification
- Network topology visualization
- Communication graph generation

#### Risk Assessment
- Automated risk scoring algorithms
- Risk level classification (Low, Medium, High, Critical)
- Risk factor analysis and reporting
- Risk trend monitoring
- Asset criticality assessment

#### Dashboard and Reporting
- Operational dashboard with key metrics
- Customizable print templates
- QR code generation for assets
- Data export in multiple formats
- Real-time statistics

#### User Management and Security
- Role-Based Access Control (RBAC)
- Granular permissions for different sections
- Comprehensive audit logging
- Contact and supplier management
- Secure authentication with JWT

#### Search and Filtering
- Global search across all assets
- Advanced filtering by criticality, risk, and site
- Bulk import/export operations
- Soft delete with trash management

### Security Features

#### Authentication and Authorization
- JWT with standard claims (issuer, audience, type)
- Bcrypt password hashing
- Configurable rate limiting
- Automatic production configuration validation

#### Multi-Tenant Security
- Complete data isolation between tenants
- Automatic tenant_id control
- API Keys for external integrations
- Comprehensive audit logging for all operations

#### Data Protection
- Input validation with Pydantic
- File upload sanitization
- Proper CORS configuration
- Secure cookie handling in production

### Technical Architecture

#### Backend (FastAPI + PostgreSQL)
- Complete RESTful API
- Database migrations with Alembic
- Standardized error handling
- Centralized logging
- Optional Redis caching

#### Frontend (Vue 3 + PrimeVue)
- Modern SPA with Vue 3 Composition API
- Consistent UI/UX with PrimeVue
- Complete internationalization (IT/EN)
- State management with Pinia
- Centralized error handling

#### DevOps
- Complete containerization with Docker
- Automated deployment scripts
- Health checks for monitoring
- Automatic database backup

### System Requirements

#### Minimum Requirements
- Docker & Docker Compose
- 4GB RAM
- 20GB disk space
- PostgreSQL 15+

#### Recommended Requirements
- 8GB RAM
- 50GB SSD storage
- Multi-core CPU
- Stable network connection

### Installation

#### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd industrace

# Start application
make prod

# Access application
open https://localhost
```

#### Default Credentials
- **URL**: https://localhost
- **Email**: admin@example.com
- **Password**: Admin@123456!

### API Features

#### REST API
- 137+ endpoints covering all functionality
- OpenAPI 3.0 specification
- Interactive documentation (Swagger UI)
- Comprehensive error handling
- Rate limiting and security

#### External API
- Secure API Key authentication
- Multi-tenant data isolation
- Configurable rate limiting
- Audit logging for all requests
- Statistics and risk assessment endpoints

### Database Schema

#### Core Tables
- **assets**: Main asset information
- **users**: User management
- **tenants**: Multi-tenant support
- **roles**: Role-based access control
- **audit_logs**: Comprehensive audit trail

#### Asset-Related Tables
- **asset_types**: Asset classification
- **asset_statuses**: Asset states
- **asset_connections**: Network connections
- **asset_communications**: Network traffic
- **asset_documents**: File attachments
- **asset_photos**: Image attachments

#### Supporting Tables
- **locations**: Physical locations
- **sites**: Site management
- **areas**: Area classification
- **suppliers**: Supplier information
- **manufacturers**: Manufacturer data
- **contacts**: Contact management

### Migration from Previous Versions

This is the initial release, so no migration is required.

### Known Issues

- None reported in this release

### Breaking Changes

- None in this initial release

### Deprecations

- None in this initial release

### Performance

#### Benchmarks
- **Asset List**: 1000+ assets loaded in <2 seconds
- **Search**: Global search across 10,000+ records in <1 second
- **API Response**: Average response time <200ms
- **Database**: Optimized queries with proper indexing

#### Scalability
- Horizontal scaling support
- Database connection pooling
- Efficient pagination
- Optimized file handling

### Security Considerations

#### Production Deployment
- Change default credentials immediately
- Configure proper SSL/TLS certificates
- Set up firewall rules
- Enable secure cookie settings
- Configure proper backup procedures

#### API Security
- Use API Keys for external integrations
- Implement proper rate limiting
- Monitor API usage
- Regular security audits

### Support and Documentation

#### Documentation
- Complete installation guide
- API documentation with examples
- User manual
- Administration guide
- Troubleshooting guide

#### Support
- **Email**: industrace@besafe.it
- **Website**: https://besafe.it/industrace
- GitHub issues for bug reports
- Documentation for common questions
- Community support channels

### Future Roadmap

#### Planned Features
- Advanced reporting and analytics
- Mobile application
- Integration with monitoring systems
- Advanced network analysis
- Machine learning for risk assessment

#### Technical Improvements
- Performance optimizations
- Additional database support
- Enhanced API features
- Improved user interface
- Extended customization options

### Contributing

We welcome contributions from the community. Please see the contributing guidelines for more information.

### License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). This means you are free to use, modify, and distribute the software, but any modifications must also be released under the same license.

### Acknowledgments

Thanks to all contributors and the open-source community for making this release possible.

---

**Industrace** - Configuration Management Database for Industrial Control Systems  
**Author**: Maurizio Bertaboni
**Website**: https://besafe.it/industrace  
**Contact**: industrace@besafe.it 