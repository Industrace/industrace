# Industrace - Industrial Asset Management System

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.0-green.svg)](https://vuejs.org/)

**Industrace** is a comprehensive Industrial Asset Management System designed for managing and monitoring industrial equipment, networks, and infrastructure. Built with FastAPI backend and Vue.js frontend, it provides a modern, scalable solution for industrial environments.

It was born from a simple observation: most asset management tools are designed for IT, while the industrial world requires different logic — mapping systems against the Purdue model, assessing risk with ICS-specific parameters, and documenting operational infrastructure in a structured way.

👉 Industrace is meant to be a starting point: easy to deploy, preloaded with demo data, and most importantly open to contributions and real-world use cases.
We don’t claim to cover everything from day one, but we believe many organizations — large and small — face similar needs.

## 🤖 Built with Human Expertise + AI Support

Industrace was developed combining hands-on expertise in cybersecurity with the support of AI tools throughout the development process.

This means two things:

🛠️ The project was built faster and with broader perspectives, leveraging AI to explore solutions and speed up coding.

🌍 The code and documentation are designed to be clear, structured, and accessible — a direct result of the “AI-assisted” approach.

We like to think of Industrace as an experiment in human + AI co-creation, where the open source community can now take the lead to validate, extend, and adapt it to real-world industrial environments.

Last thing..
Born in Italy, Industrace combines European attention to industrial processes with a global open-source mindset.

[![Release](https://img.shields.io/badge/Release-v2.0.0-blue.svg)](https://github.com/industrace/industrace/releases/tag/v2.0.0)

## 🌟 Key Features

- **Asset Management**: Complete lifecycle management of industrial assets, dependencies, and reviews
- **ISA/IEC 62443**: Security zones, conduits, compliance engine, and evidence (v2)
- **Vulnerability Intelligence**: CVE management, feeds, and risk integration (v2)
- **Network Mapping**: Visual representation of asset connections and communications
- **Risk Assessment**: Built-in risk scoring, propagation, and vulnerability assessment
- **Multi-tenant Architecture**: Support for multiple organizations
- **Role-based Access Control**: Granular permissions (RBAC) with extended v2 permissions
- **Notifications**: Templates, queue, and user preferences (v2)
- **Single Sign-On**: Azure AD / Microsoft Entra ID (v2)
- **Change Management**: See what's changed with comparisons
- **Global Search**: Spotlight-style search (Command+K) across all entities with instant results
- **Asset Timeline**: Complete change history and audit trail for each asset
- **Document Management**: Asset documentation and photo management
- **Audit Trail**: Complete activity logging and change tracking
- **API-First Design**: RESTful API for integration with other systems
- **Modern UI**: Responsive Vue.js frontend with intuitive interface

## 📸 Screenshots & Demo

### 🏠 Dashboard Overview
![Dashboard](docs/images/readme/dashboard.png)
*Main dashboard showing asset overview, risk scores, and system status*

### 📊 Asset Management
![Asset Management](docs/images/readme/asset-management.png)
*Complete asset lifecycle management with detailed information and connections*

### 🌐 Network Topology
![Network Topology](docs/images/readme/network-topology.png)
*Interactive network visualization showing asset connections and communications*

### 🔍 Asset Details
![Asset Details](docs/images/readme/asset-details.png)
*Detailed asset view with interfaces, connections, and documentation*

### 👥 User Management
![User Management](docs/images/readme/user-management.png)
*Role-based access control with granular permissions management*

### 📋 Audit Trail
![Audit Trail](docs/images/readme/audit-trail.png)
*Complete activity logging and change tracking for compliance*

### 🗺️ Floor Plan Integration
![Floor Plan](docs/images/readme/floor-plan.png)
*Visual asset placement on floor plans with interactive mapping*

### 📱 Responsive Design
![Mobile View](docs/images/readme/mobile-view.png)
*Fully responsive interface that works on desktop, tablet, and mobile*

### 🔍 Global Search - Spotlight Feature
![Global Search](docs/images/globalsearch.gif)
*Powerful spotlight-style global search (Command+K / Ctrl+K) that searches across all entities - assets, locations, sites, contacts, suppliers, and more. Real-time results with instant navigation to any item in your system.*

### 📜 Asset Timeline
![Asset Timeline](docs/images/readme/asset-details.png)
*Complete change history and audit trail for each asset. Track every modification, view detailed change logs, and see who made what changes and when. Perfect for compliance, troubleshooting, and understanding asset evolution over time.*

## 🏗️ Architecture

- **Backend**: FastAPI with SQLAlchemy ORM
- **Database**: PostgreSQL 15+
- **Frontend**: Vue.js 3 with Vite
- **Authentication**: JWT-based with role-based access control
- **Containerization**: Docker and Docker Compose
- **API Documentation**: Auto-generated with OpenAPI/Swagger

## 🚀 Quick Start

**Quick Start?** Go to [Quick Start Guide](docs/QUICK_START.md) for a quick installation **in less than 5 minutes**.

### Prerequisites
- Docker and Docker Compose
- 4GB RAM minimum (8GB recommended)
- 20GB disk space minimum
- Port 80 and 443 available (for production)

### Installation

#### **Quick Start** (Recommended for first time)
```bash
# Clone the repository
git clone https://github.com/industrace/industrace.git
cd industrace

# Start production environment with demo data
make prod

# Access the application
open https://localhost
```

#### **Production Local** (HTTPS with Nginx + Self-signed certificates)
```bash
# Start production with Nginx + self-signed certificates
make prod

# Access the application
open https://localhost
# Note: You'll see a security warning due to self-signed certificates
# This is normal for local development. Click 'Advanced' and 'Proceed'
```

#### **Production Cloud** (BETA mode - HTTPS with Traefik + Let's Encrypt) 
```bash
# Start production with Traefik + Let's Encrypt
make prod-cloud

# Access the application
open https://industrace.local
```

#### **Custom Certificates** (BETA mode - HTTPS with Nginx)
```bash
# Setup custom certificates
make custom-certs-setup

# Start with custom certificates
make custom-certs-start

# Access the application
open https://yourdomain.com
```


### Development Environment (Advanced)
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Add demo data to existing system
make demo

# Clean system completely
make clean

# Show available commands
make help

# Show configuration options
make config
```

### Default Credentials
- **Production Local URL**: https://localhost
- **Production Cloud URL**: https://industrace.local
- **Email**: admin@example.com
- **Password**: Admin@123456!

**Note**: Demo data is automatically populated when using `make prod` or `make prod-cloud`. The system includes sample sites, areas, locations, manufacturers, suppliers, contacts, assets with interfaces, and network connections for testing purposes. On first login you will be required to change your password; see [Password Policy](docs/UPGRADE_PASSWORD_POLICY.md).

## 📊 Demo Data Included

The system comes pre-populated with comprehensive demo data:

- **3 Sites**: Main Production Plant, Research & Development Center, Distribution Warehouse
- **12 Areas**: Assembly Lines, Quality Control Lab, Control Room, Maintenance Bay, etc.
- **19 Locations**: Control Panels, Quality Stations, Maintenance Bays, etc.
- **8 Assets**: PLCs, HMIs, Robots, Switches, Sensors, Servers with realistic specifications
- **10 Interfaces**: Network interfaces with IP addresses, MAC addresses, and protocols
- **5 Connections**: Network topology showing asset communications
- **4 Manufacturers**: Siemens, Rockwell Automation, Schneider Electric, ABB
- **4 Suppliers** and **6 Contacts**: Complete supply chain information

## Documentation

Full index: **[docs/README.md](docs/README.md)**. Quick links:

**Getting started**
- [Quick Start Guide](docs/QUICK_START.md) - Get up and running in 5 minutes
- [Installation Guide](docs/installation.md) - Detailed installation instructions
- [Docker Deployment](docs/docker-deployment.md) - Production deployment
- [Configuration](docs/configuration.md) - System configuration
- [Custom Certificates](docs/custom-certificates.md) - HTTPS with your own certificates

**API & integration**
- [API Documentation](docs/api-documentation.md) - REST API reference
- [External API Guide](docs/external-api.md) - Integration APIs for third-party systems

**Upgrades & administration**
- [Upgrade Safety](docs/UPGRADE_SAFETY.md) - Reducing upgrade risk (backup, staging, rollback)
- [Upgrade Guide](docs/UPGRADE.md) - How to upgrade from previous versions
- [Upgrade v1 to v2](docs/UPGRADE_v1_TO_v2.md) - Major upgrade procedure (v1.x → v2)
- [Password Policy](docs/UPGRADE_PASSWORD_POLICY.md) - Password security requirements
- [RBAC Permissions](docs/RBAC_PERMISSIONS.md) - Roles and permissions (v2)
- [SSO with Azure AD](docs/SSO_AZURE_AD_SETUP.md) - Single Sign-On configuration
- [Backup and Restore](docs/backup-restore.md) - Data protection procedures
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

**Reference**
- [Release Notes](docs/release-notes.md) - Version history and changes
- [Roadmap](docs/roadmap.md) - Planned features and improvements

## 🔧 Development

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker and Docker Compose

### Setup Development Environment
```bash
# Clone and setup
git clone https://github.com/industrace/industrace.git
cd industrace

# Run tests
make test

# View logs
make logs
```

### Available Make Commands
```bash
make prod        # Start production (Nginx + self-signed certs + auto-init DB)
make prod-cloud   # Start production (Traefik + Let's Encrypt)
make demo        # Add demo data to existing system
make clean       # Clean system completely
make test        # Run tests
make logs        # View logs
make stop       # Stop all services
make build      # Build containers
make rebuild    # Rebuild containers
make status     # Show service status
make shell      # Open backend shell
make migrate    # Run database migrations
make reset-db   # Reset database
make backup     # Backup database, uploads, config
make backup-full # Full backup including logs
make restore    # Restore from backup (see docs/backup-restore.md)
make restart    # Restart services
make info       # Show system information
make config     # Show configuration options
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. This means you are free to use, modify, and distribute the software, but any modifications must also be released under the same license.

See the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/industrace/industrace/issues)

## 📋 Changelog

See **[CHANGELOG.md](CHANGELOG.md)** and **[Release Notes](docs/release-notes.md)** for full version history.

### [v2.0.0] - February 2026
- **ISA/IEC 62443**: Security zones, conduits, compliance engine, evidence
- **Vulnerability Intelligence**: CVE management, feeds, asset matching, risk integration
- **Asset Dependencies & Review**: Dependency graph, risk propagation, review scheduling
- **Notifications**: Templates, queue, logs, user preferences
- **Single Sign-On**: Azure AD / Microsoft Entra ID
- **Extended RBAC**: New permissions for zones, compliance, vulnerabilities, notifications, SSO
- **Password policy**: Stronger requirements; see [UPGRADE_PASSWORD_POLICY.md](docs/UPGRADE_PASSWORD_POLICY.md)
- **New Asset Detail layout**: Tabs for Overview, Relations, Security, IEC 62443, Review, etc.
- **Upgrade**: From v1.x see [UPGRADE_v1_TO_v2.md](docs/UPGRADE_v1_TO_v2.md) and [UPGRADE_SAFETY.md](docs/UPGRADE_SAFETY.md)

### [v1.1.0] - November 2025
- Trash management for Areas, multilingual printed kit, global search improvements, asset timeline filtering, performance indexes, translation restructuring. See [CHANGELOG.md](CHANGELOG.md).

### [v1.0.0] - August 2025
- Initial release: asset management, multi-tenant, RBAC, network topology, risk assessment, documents, audit trail, import/export, print, floor plans, i18n, REST API, Docker. See [CHANGELOG.md](CHANGELOG.md).

## 🗺️ Roadmap

See our [Roadmap](docs/roadmap.md) for planned features and improvements.

## Author and Support

- **Author**: Maurizio Bertaboni
- **Patronage**: The project is supported by BeSafe S.r.l., focusing on the Pro edition and enterprise services
- **Industrace Site**: https://besafe.it/industrace
- **Contact**: industrace@besafe.it
