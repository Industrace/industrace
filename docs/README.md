# Industrace Documentation

Industrace is a comprehensive Configuration Management Database (CMDB) designed for Industrial Control Systems. This documentation provides comprehensive guides for installation, configuration, and usage.

## About Industrace

**Industrace** is an open-source Configuration Management Database (CMDB) specifically designed for Industrial Control Systems. It provides comprehensive asset management, network analysis, risk assessment, and reporting capabilities for industrial environments.

### License

Industrace is distributed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. This means you are free to use, modify, and distribute the software, but any modifications must also be released under the same license.

### Author and Support

- **Author**: Maurizio Bertaboni
- **Company**: BeSafe S.r.l.
- **Website**: https://besafe.it
- **Industrace Site**: https://besafe.it/industrace
- **Contact**: industrace@besafe.it

### Open Source

Industrace is fully open source and welcomes contributions from the community. The source code is available on GitHub and follows open-source best practices.

## Table of Contents

### Getting Started
- **[Quick Start Guide](QUICK_START.md)** - Get Industrace running in **5 minutes**
- [Installation Guide](installation.md) - Complete setup instructions
- [Docker Deployment](docker-deployment.md) - Production deployment with Docker
- [Configuration Guide](configuration.md) - System configuration options
- [Custom Certificates](custom-certificates.md) - HTTPS with your own certificates

### User and API
- [API Documentation](api-documentation.md) - REST API reference
- [External API Guide](external-api.md) - Integration APIs for third-party systems

### Administration and Security
- [Upgrade Safety](UPGRADE_SAFETY.md) - Reducing upgrade risk (backup, staging, rollback)
- [Upgrade Guide](UPGRADE.md) - How to upgrade from previous versions
- [Upgrade v1 to v2](UPGRADE_v1_TO_v2.md) - Major upgrade procedure (v1.x → v2)
- [Password Policy Upgrade](UPGRADE_PASSWORD_POLICY.md) - New password security requirements
- [RBAC Permissions](RBAC_PERMISSIONS.md) - Roles and permission sections (v2)
- [SSO with Azure AD](SSO_AZURE_AD_SETUP.md) - Single Sign-On configuration
- [Backup and Restore](backup-restore.md) - Data protection procedures
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

### Reference
- [Release Notes](release-notes.md) - Version history and changes
- [Development Roadmap](roadmap.md) - Future development plans and milestones

## Quick Start

### Prerequisites
- Docker and Docker Compose
- 4GB RAM minimum (8GB recommended)
- 20GB disk space minimum
- PostgreSQL 15+ (included in Docker setup)

### Installation
```bash
# Clone the repository
git clone https://github.com/industrace/industrace.git
cd industrace

# Start production (Nginx + self-signed SSL + auto-init DB)
make prod

# Access the application
open https://localhost
```

### Default Credentials
- **URL**: https://localhost (production local) or https://industrace.local (production cloud)
- **Email**: admin@example.com
- **Password**: Admin@123456!

See [QUICK_START.md](QUICK_START.md) for other deployment types and [UPGRADE_PASSWORD_POLICY.md](UPGRADE_PASSWORD_POLICY.md) for password requirements (v1.1+).

## System Overview

Industrace provides:

- **Multi-tenant Architecture**: Complete isolation between organizations
- **Asset Management**: Comprehensive industrial asset tracking, dependencies, and reviews
- **ISA/IEC 62443 Compliance**: Security zones, conduits, requirements, and evidence (v2)
- **Vulnerability Intelligence**: CVE management, feeds, and risk integration (v2)
- **Network Analysis**: Connection mapping and protocol analysis
- **Risk Assessment**: Automated risk scoring, propagation, and monitoring
- **Notifications**: Templates, queue, and user preferences (v2)
- **Single Sign-On**: Azure AD / Microsoft Entra ID (v2)
- **Document Management**: File uploads and document tracking
- **Reporting**: Customizable reports, dashboards, and print
- **API Integration**: REST APIs and API keys for external integrations
- **Security**: Role-based access control (RBAC), password policy, audit logging

## Support

For support and questions:
1. Check the troubleshooting guide
2. Review the API documentation
3. Check system logs: `docker-compose logs backend`
4. Verify system health: `curl https://localhost/api/health` (or your deployment URL + `/api/health`)
5. Contact: industrace@besafe.it

## Contributing

Industrace is open source and welcomes contributions! Please see our contributing guidelines for more information on how to get involved.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). See the [LICENSE](../LICENSE) file for details.

---

**Industrace** - Configuration Management Database for Industrial Control Systems  
**Author**: Maurizio Bertaboni (BeSafe S.r.l.)  
**Website**: https://besafe.it/industrace  
**Contact**: industrace@besafe.it 