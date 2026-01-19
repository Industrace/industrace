# Installation Guide

This guide provides step-by-step instructions for installing Industrace on your system.

## System Requirements

### Minimum Requirements
- **RAM**: 4GB
- **Storage**: 20GB available space
- **CPU**: 2 cores
- **OS**: Linux, macOS, or Windows with Docker support

### Recommended Requirements
- **RAM**: 8GB or more
- **Storage**: 50GB SSD
- **CPU**: 4+ cores
- **Network**: Stable internet connection

### Software Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

## Installation Methods

### Method 1: Docker Compose with Make (Recommended)

#### Step 1: Clone the Repository
```bash
git clone https://github.com/industrace/industrace.git
cd industrace
```

#### Step 2: Choose Your Deployment Type

##### **Production Local** (Recommended for first time)
```bash
# Start production with Nginx + self-signed certificates + auto-init DB
make prod
```
- **Application**: https://localhost
- **Backend API**: https://localhost/api/docs
- **Features**: SSL certificates, optimized builds, automatic demo data

##### **Production Cloud** (HTTPS with Traefik)
```bash
# Start production with Traefik + Let's Encrypt
make prod-cloud
```
- **Application**: https://industrace.local
- **Traefik Dashboard**: http://localhost:8080
- **Features**: SSL certificates, optimized builds, production security

##### **Custom Certificates** (HTTPS with Nginx)
```bash
# Setup custom certificates
make custom-certs-setup

# Start with custom certificates
make custom-certs-start
```
- **Application**: https://yourdomain.com
- **Features**: Custom SSL certificates, production security

#### Step 4: Verify Installation
```bash
# Check system status
make status

# View logs if needed
make logs
```

#### Step 5: Access the Application

##### **Production Local**
- **Application**: https://localhost
- **Backend API**: https://localhost/api/docs

##### **Production Cloud**
- **Application**: https://industrace.local
- **Traefik Dashboard**: http://localhost:8080

##### **Custom Certificates**
- **Application**: https://yourdomain.com

### Method 2: Development Setup (Advanced)

#### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 15+

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure database
export DATABASE_URL="postgresql://user:password@localhost/industrace"

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Initial Configuration

### Default Credentials
After installation, you can log in with:
- **Email**: admin@example.com
- **Password**: Admin@123456!

**⚠️ Important Security Notice:**
- Default accounts (admin, editor, viewer) are created with weak passwords for initial setup
- **You will be required to change your password on first login**
- The new password must meet the following requirements:
  - Minimum 12 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
  - At least one special character (!@#$%^&*(),.?":{}|<>[]\/_+=-~`)

### Account Security Features
- **Account Lockout**: After 5 failed login attempts, your account will be temporarily locked for 30 minutes
- **Password Change Required**: Default accounts must change their password on first login
- **Rate Limiting**: Login attempts are rate-limited to prevent brute-force attacks

### Demo Data
The system automatically populates with comprehensive demo data when using `make prod` or `make prod-cloud`:
- 3 Sites (Production Plant, R&D Center, Distribution Warehouse)
- 12 Areas (Assembly Lines, Labs, Control Rooms, etc.)
- 19 Locations (Control Panels, Quality Stations, etc.)
- 8 Assets (PLCs, HMIs, Robots, Sensors, etc.)
- 10 Interfaces (Network interfaces with IP addresses)
- 5 Connections (Network topology)
- 4 Suppliers (Siemens, Rockwell, Schneider, ABB)
- 6 Contacts (Sales, Support, Management)

## Available Make Commands

### Basic Commands
```bash
make prod      # Start production environment (Nginx + self-signed certificates + auto-init DB)
make prod-cloud # Start production environment (Traefik + Let's Encrypt)
make stop      # Stop all services
make status    # Show service status
make logs      # View logs
```

### Development Commands
```bash
make demo      # Add demo data to existing system
make clean     # Clean system completely
make test      # Run tests
make shell     # Open backend shell
make migrate   # Run database migrations
make reset-db  # Reset database
```

### Build Commands
```bash
make build     # Build containers
make rebuild   # Rebuild containers
make restart   # Restart services
```

### Utility Commands
```bash
make help      # Show all available commands
make info      # Show system information
```

## Manual Docker Commands (Alternative)

If you prefer to use Docker commands directly:

### Development Environment (Advanced)
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Stop development environment
docker-compose -f docker-compose.dev.yml down

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Restart services
docker-compose -f docker-compose.dev.yml restart
```

### Production Local Environment
```bash
# Start production system (Nginx + self-signed certificates)
docker-compose -f docker-compose.prod.yml up -d

# Stop production system
docker-compose -f docker-compose.prod.yml down

# View production logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart production system
docker-compose -f docker-compose.prod.yml restart
```

### Production Cloud Environment
```bash
# Start production system (Traefik + Let's Encrypt)
docker-compose up -d

# Stop production system
docker-compose down

# View production logs
docker-compose logs -f

# Restart production system
docker-compose restart
```

## Troubleshooting

### Common Issues

#### System won't start
```bash
# Check logs
make logs

# Clean and restart
make clean
make prod
```

#### Demo data not loading
```bash
# Force demo data seeding
make demo

# Or clean and reinitialize
make clean
make prod
```

#### Port conflicts
```bash
# Check what's using the ports
sudo lsof -i :80
sudo lsof -i :443
sudo lsof -i :5432

# Stop conflicting services
sudo systemctl stop nginx  # if using port 80
```

#### Permission issues
```bash
# Set correct permissions
sudo chown -R $USER:$USER .

# Or run with sudo (not recommended for production)
sudo make init
```

### Database Issues

#### Reset database
```bash
# Complete reset
make clean
make init

# Or just reset database
make reset-db
```

#### Backup and restore
```bash
# Backup
make backup

# Restore
make restore
```

## Configuration Files

### Environment Variables
The main configuration file is `.env` (copied from `production.env.example`):

```bash
# Database Configuration
DB_PASSWORD=your_secure_password_here

# JWT Configuration
SECRET_KEY=your-super-secure-secret-key-change-this-in-production

# Domain Configuration
DOMAIN=yourdomain.com

# Admin Configuration
ADMIN_EMAIL=admin@yourdomain.com
```

### Docker Compose Files
- `docker-compose.dev.yml` - Development environment
- `docker-compose.prod.yml` - Production environment
- `docker-compose.yml` - Default environment

## Next Steps

After successful installation:

1. **Access the application**: http://localhost:5173
2. **Login with default credentials**: admin@example.com / Admin@123456!
3. **Change your password**: You will be required to change your password on first login. The new password must be at least 12 characters long and include uppercase, lowercase, numbers, and special characters.
4. **Explore demo data**: Navigate through sites, areas, assets, and connections
5. **Configure your environment**: Update settings in the admin panel
6. **Add your own data**: Start adding your industrial assets

## Support

- **Documentation**: [docs/](docs/)
- **Quick Start**: [QUICK_START.md](QUICK_START.md)
- **Troubleshooting**: [troubleshooting.md](troubleshooting.md)
- **Website**: https://besafe.it/industrace
- **Email**: industrace@besafe.it

---

**Author**: Maurizio Bertaboni