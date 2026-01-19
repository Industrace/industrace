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

### User Guides
- [User Manual](user-manual.md) - Complete user guide
- [API Documentation](api-documentation.md) - REST API reference
- [External API Guide](external-api.md) - Integration APIs for third-party systems

### Administration
- [Administration Guide](administration.md) - System administration tasks
- [Upgrade Guide](UPGRADE.md) - How to upgrade from previous versions
- [Backup and Restore](backup-restore.md) - Data protection procedures
- [Security Guide](security.md) - Security best practices
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

### Development
- [Development Guide](development.md) - Development setup and guidelines
- [API Testing](api-testing.md) - Testing procedures for APIs
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
git clone <repository-url>
cd industrace

# Start the application
docker-compose up -d

# Access the application
open http://localhost:5173
```

### Default Credentials
- **URL**: http://localhost:5173
- **Email**: admin@example.com
- **Password**: Admin@123456!

## System Overview

Industrace provides:

- **Multi-tenant Architecture**: Complete isolation between organizations
- **Asset Management**: Comprehensive industrial asset tracking
- **Network Analysis**: Connection mapping and protocol analysis
- **Risk Assessment**: Automated risk scoring and monitoring
- **Document Management**: File uploads and document tracking
- **Reporting**: Customizable reports and dashboards
- **API Integration**: REST APIs for external integrations
- **Security**: Role-based access control and audit logging

## Support

For support and questions:
1. Check the troubleshooting guide
2. Review the API documentation
3. Check system logs: `docker-compose logs backend`
4. Verify system health: `curl http://localhost:8000/health`
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