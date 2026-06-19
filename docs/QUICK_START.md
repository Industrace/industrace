# Quick Start - Industrace

**Industrace** is an open-source industrial asset management system. This document will guide you through installation and initial setup in **less than 5 minutes**.

> **From Industrace 1.x?** v1 is frozen; install v2 as a new stack and migrate data manually — [MIGRATION.md](MIGRATION.md).  
> **Full install options** (cloud, dev, custom certs): [INSTALLATION.md](INSTALLATION.md).

## Prerequisites

- Docker and Docker Compose installed
- Git installed
- Port 80 and 443 available on your system (for production)

## Quick Installation

### 1. Clone the Repository

```bash
git clone https://github.com/industrace/industrace.git
cd industrace
```

### 2. Choose Your Deployment Type

Industrace supports two main deployment scenarios:

#### **Production Local** (Recommended for first time)
- **Frontend**: https://localhost (Nginx + self-signed certificates)
- **Backend**: https://localhost/api (Nginx proxy)
- **Features**: SSL certificates, optimized builds, automatic demo data
- **No configuration needed!**

#### **Production Cloud** (HTTPS with Traefik)
- **Frontend**: https://industrace.local (Traefik + Let's Encrypt)
- **Backend**: https://industrace.local/api (Traefik proxy)
- **Features**: SSL certificates, optimized builds, production security
- **Requires**: Domain configuration

#### **Custom Certificates** (HTTPS with Nginx)
- **Frontend**: https://yourdomain.com (Nginx + custom certificates)
- **Backend**: https://yourdomain.com/api (Nginx proxy)
- **Features**: Custom SSL certificates, production security
- **Requires**: Custom certificates and domain configuration

### 3. Start the System

#### **Production Local** (Recommended for first time)
```bash
# Start production with Nginx + self-signed certificates + auto-init DB
make prod
```

#### **Production Cloud** (HTTPS with Traefik)
```bash
# Start production with Traefik + Let's Encrypt
make prod-cloud
```

#### **Custom Certificates** (HTTPS with Nginx)
```bash
# Setup custom certificates
make custom-certs-setup

# Start with custom certificates
make custom-certs-start
```

### Configuration Differences

- **Production Local** (`make prod`): Nginx reverse proxy, self-signed SSL, optimized builds, automatic demo data
- **Production Cloud** (`make prod-cloud`): Traefik reverse proxy, Let's Encrypt SSL, optimized builds
- **Custom Certs** (`make custom-certs-start`): Nginx reverse proxy, custom SSL certificates

### 4. Verify Installation

Open your browser and go to:

#### **Production Local**
- **Application**: https://localhost
- **Backend API**: https://localhost/api/docs

#### **Production Cloud**
- **Application**: https://industrace.local
- **Traefik Dashboard**: http://localhost:8080

#### **Custom Certificates**
- **Application**: https://yourdomain.com

## First Access

1. **Login**: Use the default credentials:
   - Email: `admin@example.com`
   - Password: `Admin@123456!`

   **Alternative users:**
   - Editor: `editor@example.com` / `Editor@123456!`
   - Viewer: `viewer@example.com` / `Viewer@123456!`

2. **⚠️ Change Password (Required)**: 
   - On first login, you will be required to change your password
   - The new password must meet security requirements:
     - Minimum 12 characters
     - At least one uppercase letter (A-Z)
     - At least one lowercase letter (a-z)
     - At least one number (0-9)
     - At least one special character (!@#$%^&*(),.?":{}|<>[]\/_+=-~`)

3. **Account Security**:
   - After 5 failed login attempts, your account will be temporarily locked for 30 minutes
   - Login attempts are rate-limited to prevent brute-force attacks

4. **Demo Data**: The system automatically populates with realistic demo data when using `make prod` or `make prod-cloud` including:
   - 3 Sites (Production Plant, R&D Center, Distribution Warehouse)
   - 12 Areas (Assembly Lines, Labs, Control Rooms, etc.)
   - 19 Locations (Control Panels, Quality Stations, etc.)
   - 8 Assets (PLCs, HMIs, Robots, Sensors, etc.)
   - 10 Interfaces (Network interfaces with IP addresses)
   - 5 Connections (Network topology)
   - 4 Suppliers (Siemens, Rockwell, Schneider, ABB)
   - 6 Contacts (Sales, Support, Management)

5. **Initial Setup**: The system will automatically guide you through the first tenant configuration

## Main File Structure

```
industrace/
├── Makefile                    # ← NEW: Simplified commands
├── docker-compose.yml          # ← Production (Traefik)
├── docker-compose.dev.yml      # ← Development
├── docker-compose.custom-certs.yml # ← Custom certificates
├── custom-certs.env            # ← Custom certificates config
├── backend/                    # ← Backend application
└── frontend/                   # ← Frontend application
```

## Useful Commands

### Production Local Commands
```bash
# Start production system (Nginx + self-signed certificates + auto-init DB)
make prod

# Stop production system
make stop

# View production logs
make logs

# Restart production system
make restart

# Build containers
make build

# Rebuild containers
make rebuild
```

### Production Cloud Commands
```bash
# Start production system (Traefik + Let's Encrypt)
make prod-cloud

# Stop production system
make stop

# View production logs
make logs

# Restart production system
make restart

# Build containers
make build

# Rebuild containers
make rebuild
```

### Custom Certificates Commands
```bash
# Setup custom certificates
make custom-certs-setup

# Start with custom certificates
make custom-certs-start

# Stop custom certificates deployment
make custom-certs-stop

# View custom certificates logs
make custom-certs-logs
```

### Additional Commands
```bash
# Add demo data to existing system
make demo

# Run tests
make test

# Open backend shell
make shell

# Run database migrations
make migrate

# Reset database
make reset-db

# Show configuration information
make config

# Show Traefik dashboard information
make traefik

# Show all available commands
make help
```

## Troubleshooting

### "Port 80 already in use" Error
```bash
# Find what's using port 80
sudo lsof -i :80

# Stop the service (e.g., nginx)
sudo systemctl stop nginx
```

### "Permission denied" Error
```bash
# Set correct permissions
sudo chown -R $USER:$USER .
```

### System won't start
```bash
# Check logs
make logs

# Clean and restart
make clean
make prod
```

### Demo data not loading
```bash
# Force demo data seeding
make demo

# Or clean and reinitialize
make clean
make prod
```

## Advanced Configuration (Optional)

### Change Port
If port 80 is busy, modify `docker-compose.prod.yml`:

```yaml
ports:
  - "8080:80"  # Change 8080 to your preferred port
```

Then access via `http://localhost:8080`

### Database Backup
```bash
# Backup
make backup

# Restore
make restore
```

### Manual Database Operations
```bash
# Backup (manual)
docker-compose -f docker-compose.prod.yml exec db pg_dump -U industrace industrace > backup.sql

# Restore (manual)
docker-compose -f docker-compose.prod.yml exec -T db psql -U industrace industrace < backup.sql
```

## Support

- **Documentation**: [docs/](docs/)
- **Website**: https://besafe.it/industrace
- **Email**: industrace@besafe.it
- **GitHub**: https://github.com/industrace/industrace

## License

Industrace is distributed under AGPL v3.0 license - see [LICENSE](LICENSE) for details.

---

**Author**: Maurizio Bertaboni - BeSafe S.r.l. (https://besafe.it) 