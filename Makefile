# Industrace Development Makefile
# ===============================

.PHONY: help clean clean-all demo prod prod-cloud logs logs-backend logs-frontend stop build rebuild rebuild-backend status shell migrate migration reset-db restart info config traefik create-tenant create-tenant-default custom-certs-setup custom-certs-start custom-certs-stop custom-certs-logs reset-admin-password list-tenants list-admins reset-security-requirements update-roles backup backup-full backup-list restore

# Default target
help:
	@echo "🏭 Industrace Development Commands"
	@echo "=================================="
	@echo ""
	@echo "📋 Available commands:"
	@echo "  make prod      - Start PRODUCTION environment (HTTPS + Nginx + self-signed + auto-init DB)"
	@echo "  make prod-cloud - Start CLOUD production environment (HTTPS + Traefik + Let's Encrypt)"
	@echo "  make demo      - Add demo data to existing system"
	@echo "  make clean     - Clean system completely"
	@echo "  make clean-all - Clean everything including images"
	@echo "  make logs      - Show logs"
	@echo "  make logs-backend - Show backend logs only"
	@echo "  make logs-frontend - Show frontend logs only"
	@echo "  make stop      - Stop all containers"
	@echo "  make build     - Build containers"
	@echo "  make rebuild   - Rebuild containers (no cache)"
	@echo "  make rebuild-backend - Rebuild backend only (faster)"
	@echo "  make status    - Show system status"
	@echo "  make shell     - Open backend shell"
	@echo "  make migrate   - Run database migrations"
	@echo "  make migration - Create new migration (requires message=)"
	@echo "  make reset-db  - Reset database (drop and recreate)"
	@echo "  make restart   - Quick restart"
	@echo "  make info      - Show system information"
	@echo "  make config    - Show configuration information"
	@echo "  make traefik   - Show Traefik dashboard information"
	@echo "  make create-tenant - Create new tenant (see usage below)"
	@echo "  make create-tenant-default - Create tenant with default values"
	@echo ""
	@echo "🔐 Custom Certificates:"
	@echo "  make custom-certs-setup - Setup custom certificates deployment"
	@echo "  make custom-certs-start - Start with custom certificates"
	@echo "  make custom-certs-stop  - Stop custom certificates deployment"
	@echo "  make custom-certs-logs  - Show custom certificates logs"
	@echo ""
	@echo "🏗️  Tenant Management:"
	@echo "  make create-tenant TENANT_NAME=\"My Company\" TENANT_SLUG=\"my-company\" ADMIN_EMAIL=\"admin@mycompany.com\" ADMIN_PASSWORD=\"pass\""
	@echo "  make reset-admin-password TENANT_SLUG=\"my-company\" ADMIN_EMAIL=\"admin@mycompany.com\""
	@echo "  make list-tenants - List all available tenants"
	@echo "  make list-admins TENANT_SLUG=\"my-company\" - List admin users in tenant"
	@echo ""
	@echo "🔒 Security & Compliance:"
	@echo "  make reset-security-requirements - Reset ISA/IEC 62443 Security Requirements"
	@echo "  make update-roles - Update roles with latest permissions"
	@echo ""
	@echo "💾 Backup & Restore:"
	@echo "  make backup - Create system backup (database + uploads + config)"
	@echo "  make backup-full - Create full backup (including logs)"
	@echo "  make backup-list - List available backups"
	@echo "  make restore BACKUP_FILE=backups/industrace_backup_YYYYMMDD_HHMMSS.tar.gz - Restore from backup"
	@echo ""


# Add demo data to existing system
demo:
	@echo "🌱 Adding demo data to existing system..."
	@if ! docker-compose -f docker-compose.prod.yml ps -q backend > /dev/null 2>&1; then \
		echo "❌ Backend container is not running. Please start with: make prod"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.prod.yml exec backend python -m app.init_demo_data
	@echo "✅ Demo data added successfully!"

# Clean system completely
clean:
	@echo "🧹 Cleaning Industrace system..."
	docker-compose -f docker-compose.prod.yml down -v
	docker-compose down -v
	@echo "🧹 Removing database volume (ensures fresh DB after make prod)..."
	-docker volume rm industrace_industrace_postgres_data 2>/dev/null || true
	docker system prune -f
	@echo "🧹 Cleaning temporary files..."
	@rm -f .env.prod .env.prod-cloud .env.custom
	@echo "✅ System cleaned successfully"

# Clean everything including images
clean-all:
	@echo "🧹 Cleaning everything..."
	docker-compose -f docker-compose.prod.yml down -v --rmi all
	docker-compose down -v --rmi all
	docker system prune -af
	@echo "✅ Everything cleaned successfully"


# Start production environment (Nginx + self-signed certificates)
prod:
	@echo "🔒 Running security checks..."
	@./scripts/check-secrets.sh || (echo ""; echo "❌ Security check failed. Please fix the issues above before starting production."; exit 1)
	@echo ""
	@echo "🚀 Starting production environment with Nginx..."
	@if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then \
		echo "🔐 SSL certificates not found. Generating self-signed certificates..."; \
		./scripts/generate-ssl-certs.sh; \
	fi
	@echo "📝 Setting up production environment..."
	@if [ -z "$$DB_PASSWORD" ]; then \
		echo "🔐 Generating secure database password..."; \
		DB_PASSWORD=$$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32); \
		echo "DB_PASSWORD=$$DB_PASSWORD" > .env.prod; \
	else \
		echo "DB_PASSWORD=$$DB_PASSWORD" > .env.prod; \
	fi
	@echo "CORS_ORIGINS=https://localhost,https://127.0.0.1,https://industrace.local" >> .env.prod
	@echo "SSO_REDIRECT_URI=https://localhost/auth/sso/callback" >> .env.prod
	@echo "SECURE_COOKIES=true" >> .env.prod
	@echo "SAME_SITE_COOKIES=strict" >> .env.prod
	@echo "SECRET_KEY=prod-$$(openssl rand -hex 32)" >> .env.prod
	@if [ -z "$$ENCRYPTION_KEY" ]; then \
		echo "🔐 Generating encryption key for SSO..."; \
		if ! python3 -c "from cryptography.fernet import Fernet" 2>/dev/null; then \
			echo "⚠️  Warning: cryptography module not found. Installing..."; \
			pip3 install cryptography > /dev/null 2>&1 || (echo "❌ Failed to install cryptography. Please install manually: pip3 install cryptography"; exit 1); \
		fi; \
		ENCRYPTION_KEY=$$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"); \
		echo "ENCRYPTION_KEY=$$ENCRYPTION_KEY" >> .env.prod; \
	else \
		echo "ENCRYPTION_KEY=$$ENCRYPTION_KEY" >> .env.prod; \
	fi
	docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
	@echo "⏳ Waiting for services to start..."
	@echo "   (Migrations and initialization are automatic on first startup)"
	sleep 20
	@echo "✅ Production environment started!"
	@echo "🌐 Access your application at: https://localhost or https://industrace.local"
	@echo "⚠️  Note: You'll see a security warning due to self-signed certificates"
	@echo "   This is normal for local development. Click 'Advanced' and 'Proceed'"
	@echo ""
	@echo "🔍 Checking for initialization credentials..."
	@sleep 5
	@BACKEND_LOGS=$$(docker-compose -f docker-compose.prod.yml logs --tail=200 backend 2>/dev/null); \
	if echo "$$BACKEND_LOGS" | grep -q "SYSTEM INITIALIZATION COMPLETED"; then \
		echo ""; \
		echo "🔐 Default Login Credentials:"; \
		echo "$$BACKEND_LOGS" | grep -A 10 "SYSTEM INITIALIZATION COMPLETED" | grep -E "(Admin|Editor|Viewer|IMPORTANT)" | sed 's/^[^:]*://' || true; \
		echo ""; \
	fi

# Start cloud production environment (Traefik + Let's Encrypt)
prod-cloud:
	@echo "🔒 Running security checks..."
	@./scripts/check-secrets.sh || (echo ""; echo "❌ Security check failed. Please fix the issues above before starting production."; exit 1)
	@echo ""
	@echo "☁️  Starting cloud production environment with Traefik..."
	@echo "📝 Setting up cloud production environment..."
	@if [ -z "$$DB_PASSWORD" ]; then \
		echo "🔐 Generating secure database password..."; \
		DB_PASSWORD=$$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32); \
		echo "DB_PASSWORD=$$DB_PASSWORD" > .env.prod-cloud; \
	else \
		echo "DB_PASSWORD=$$DB_PASSWORD" > .env.prod-cloud; \
	fi
	@echo "CORS_ORIGINS=https://industrace.local,https://www.industrace.local" >> .env.prod-cloud
	@echo "SSO_REDIRECT_URI=https://industrace.local/auth/sso/callback" >> .env.prod-cloud
	@echo "SECURE_COOKIES=true" >> .env.prod-cloud
	@echo "SAME_SITE_COOKIES=strict" >> .env.prod-cloud
	@echo "SECRET_KEY=prod-$$(openssl rand -hex 32)" >> .env.prod-cloud
	@if [ -z "$$ENCRYPTION_KEY" ]; then \
		echo "🔐 Generating encryption key for SSO..."; \
		if ! python3 -c "from cryptography.fernet import Fernet" 2>/dev/null; then \
			echo "⚠️  Warning: cryptography module not found. Installing..."; \
			pip3 install cryptography > /dev/null 2>&1 || (echo "❌ Failed to install cryptography. Please install manually: pip3 install cryptography"; exit 1); \
		fi; \
		ENCRYPTION_KEY=$$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"); \
		echo "ENCRYPTION_KEY=$$ENCRYPTION_KEY" >> .env.prod-cloud; \
	else \
		echo "ENCRYPTION_KEY=$$ENCRYPTION_KEY" >> .env.prod-cloud; \
	fi
	docker-compose -f docker-compose.yml --env-file .env.prod-cloud up -d
	@echo "✅ Cloud production environment started!"
	@echo "🌐 Access your application at: https://industrace.local"
	@echo "🦌 Traefik dashboard: http://localhost:8080"


# Run tests (disabled - tests removed)
# test:
# 	@echo "🧪 Running tests..."
# 	docker-compose -f docker-compose.prod.yml exec backend pytest

# Show logs
logs:
	@echo "📋 Showing logs..."
	docker-compose -f docker-compose.prod.yml logs -f

# Show backend logs only
logs-backend:
	@echo "📋 Showing backend logs..."
	docker-compose -f docker-compose.prod.yml logs -f backend

# Show frontend logs only
logs-frontend:
	@echo "📋 Showing frontend logs..."
	docker-compose -f docker-compose.prod.yml logs -f frontend

# Stop all containers
stop:
	@echo "🛑 Stopping all containers..."
	docker-compose -f docker-compose.prod.yml down
	docker-compose down

# Build images
build:
	@echo "🔨 Building images..."
	docker-compose -f docker-compose.prod.yml build

# Rebuild images (no cache)
rebuild:
	@echo "🔨 Rebuilding images (no cache)..."
	docker-compose -f docker-compose.prod.yml build --no-cache

# Rebuild backend only (faster)
rebuild-backend:
	@echo "🔨 Rebuilding backend..."
	docker-compose -f docker-compose.prod.yml build backend
	@echo "✅ Backend rebuilt. Restart with: make stop && make prod"

# Check system status
status:
	@echo "📊 System status:"
	docker-compose -f docker-compose.prod.yml ps

# Access backend shell
shell:
	@echo "🐚 Opening backend shell..."
	@if ! docker-compose -f docker-compose.prod.yml ps -q backend > /dev/null 2>&1; then \
		echo "❌ Backend container is not running. Please start with: make prod"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.prod.yml exec backend bash

# Run database migrations
migrate:
	@echo "📊 Running database migrations..."
	@if ! docker-compose -f docker-compose.prod.yml ps -q backend > /dev/null 2>&1; then \
		echo "❌ Backend container is not running. Please start with: make prod"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Create new migration
migration:
	@echo "📝 Creating new migration..."
	@if [ -z "$(message)" ]; then \
		echo "❌ Please provide message parameter"; \
		echo "Example: make migration message=\"Add new field to assets\""; \
		exit 1; \
	fi
	@if ! docker-compose -f docker-compose.prod.yml ps -q backend > /dev/null 2>&1; then \
		echo "❌ Backend container is not running. Please start with: make prod"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.prod.yml exec backend alembic revision --autogenerate -m "$(message)"

# Reset database (drop and recreate)
reset-db:
	@echo "🔄 Resetting database..."
	docker-compose -f docker-compose.prod.yml down
	docker volume rm industrace_industrace_postgres_data || true
	docker-compose -f docker-compose.prod.yml up -d db
	sleep 10
	docker-compose -f docker-compose.prod.yml up -d backend
	sleep 15
	make migrate
	make prod

# Quick restart
restart:
	@echo "🔄 Quick restart..."
	docker-compose -f docker-compose.prod.yml restart

# Show system info
info:
	@echo "ℹ️  System Information:"
	@echo "======================"
	@echo "Frontend: https://localhost"
	@echo "Backend:  https://localhost/api"
	@echo "API Docs: https://localhost/api/docs"
	@echo ""
	@echo "Default credentials (if system is initialized):"
	@echo "Admin:   admin@example.com / Admin@123456!"
	@echo "Editor:  editor@example.com / Editor@123456!"
	@echo "Viewer:  viewer@example.com / Viewer@123456!"
	@echo ""
	@echo "💡 Run 'make prod' to start the system and see actual credentials"

# Show configuration info
config:
	@echo "⚙️  Configuration Information:"
	@echo "============================="
	@echo ""
	@echo "🚀 Production Local (make prod):"
	@echo "  - CORS: https://localhost, https://127.0.0.1, https://industrace.local"
	@echo "  - API URL: https://localhost/api (via Nginx)"
	@echo "  - Cookies: Secure, SameSite=strict"
	@echo "  - Proxy: Nginx + Self-signed certificates"
	@echo "  - Access: https://localhost or https://industrace.local"
	@echo ""
	@echo "☁️  Production Cloud (make prod-cloud):"
	@echo "  - CORS: https://industrace.local, https://www.industrace.local"
	@echo "  - API URL: https://industrace.local/api (via Traefik)"
	@echo "  - Cookies: Secure, SameSite=strict"
	@echo "  - Proxy: Traefik + Let's Encrypt"
	@echo "  - Dashboard: http://localhost:8080"
	@echo ""
	@echo "🔐 Custom Certs (make custom-certs-start):"
	@echo "  - CORS: https://[DOMAIN], https://www.[DOMAIN]"
	@echo "  - API URL: https://[DOMAIN] (via nginx)"
	@echo "  - Cookies: Secure, SameSite=strict"
	@echo "  - Proxy: Nginx + Custom certificates"
	@echo ""
	@if [ -f "custom-certs.env" ]; then \
		DOMAIN=$$(grep DOMAIN custom-certs.env | cut -d= -f2); \
		echo "📋 Current custom domain: $$DOMAIN"; \
	fi

# Show Traefik dashboard info
traefik:
	@echo "🦌 Traefik Information:"
	@echo "======================"
	@echo "Dashboard: http://localhost:8080"
	@echo "Services: http://localhost:8080/api/http/services"
	@echo "Routers: http://localhost:8080/api/http/routers"
	@echo ""
	@echo "🔍 Checking Traefik status..."
	@if docker ps | grep -q traefik; then \
		echo "✅ Traefik is running"; \
		echo "🌐 Access dashboard at: http://localhost:8080"; \
	else \
		echo "❌ Traefik is not running"; \
		echo "💡 Start with: make prod"; \
	fi

# Create new tenant
create-tenant:
	@echo "🏗️  Creating new tenant..."
	@echo "Usage: make create-tenant TENANT_NAME=\"My Company\" TENANT_SLUG=\"my-company\" ADMIN_EMAIL=\"admin@mycompany.com\""
	@if ! docker-compose -f docker-compose.prod.yml ps -q backend > /dev/null 2>&1; then \
		echo "❌ Backend container is not running. Please start with: make prod"; \
		exit 1; \
	fi
	@if [ -z "$(TENANT_NAME)" ] || [ -z "$(TENANT_SLUG)" ] || [ -z "$(ADMIN_EMAIL)" ]; then \
		echo "❌ Please provide TENANT_NAME, TENANT_SLUG, and ADMIN_EMAIL parameters"; \
		echo "Example: make create-tenant TENANT_NAME=\"My Company\" TENANT_SLUG=\"my-company\" ADMIN_EMAIL=\"admin@mycompany.com\""; \
		exit 1; \
	fi
	@if [ -z "$(ADMIN_PASSWORD)" ]; then \
		echo "🔐 No password provided, generating secure password..."; \
		PASSWORD=$$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-12); \
		echo "Generated password: $$PASSWORD"; \
		docker-compose -f docker-compose.prod.yml exec backend python -m app.init_tenant "$(TENANT_NAME)" "$(TENANT_SLUG)" "$(ADMIN_EMAIL)" "$$PASSWORD" "$(ADMIN_NAME)"; \
	else \
		echo "🔐 Using provided password..."; \
		docker-compose -f docker-compose.prod.yml exec backend python -m app.init_tenant "$(TENANT_NAME)" "$(TENANT_SLUG)" "$(ADMIN_EMAIL)" "$(ADMIN_PASSWORD)" "$(ADMIN_NAME)"; \
	fi

# Create tenant with default values
create-tenant-default:
	@echo "🏗️  Creating tenant with default values..."
	@if ! docker-compose -f docker-compose.prod.yml ps -q backend > /dev/null 2>&1; then \
		echo "❌ Backend container is not running. Please start with: make prod"; \
		exit 1; \
	fi
	@echo "🔐 Generating secure password..."
	@PASSWORD=$$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-12); \
	echo "Generated password: $$PASSWORD"; \
	docker-compose -f docker-compose.prod.yml exec backend python -m app.init_tenant "New Tenant" "new-tenant" "admin@example.com" "$$PASSWORD"

# Custom Certificates Commands
# ============================

# Setup custom certificates deployment
custom-certs-setup:
	@echo "🔐 Setting up custom certificates deployment..."
	@if [ ! -f "custom-certs.env" ]; then \
		echo "❌ custom-certs.env not found!"; \
		echo "📋 Please copy custom-certs.env.example to custom-certs.env and configure it:"; \
		echo "   cp custom-certs.env.example custom-certs.env"; \
		echo "   nano custom-certs.env"; \
		exit 1; \
	fi
	@echo "✅ Running setup validation..."
	./setup-custom-certs.sh

# Start with custom certificates
custom-certs-start:
	@echo "🔒 Running security checks..."
	@./scripts/check-secrets.sh || (echo ""; echo "❌ Security check failed. Please fix the issues above before starting production."; exit 1)
	@echo ""
	@echo "🚀 Starting Industrace with custom certificates..."
	@if [ ! -f "custom-certs.env" ]; then \
		echo "❌ custom-certs.env not found!"; \
		echo "📋 Please run 'make custom-certs-setup' first"; \
		exit 1; \
	fi
	@echo "📝 Setting up security variables..."
	@if ! grep -q "^DB_PASSWORD=" custom-certs.env 2>/dev/null; then \
		echo "🔐 Generating secure database password..."; \
		DB_PASSWORD=$$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32); \
		echo "DB_PASSWORD=$$DB_PASSWORD" >> custom-certs.env; \
	fi
	@if ! grep -q "^SECRET_KEY=" custom-certs.env 2>/dev/null; then \
		echo "🔐 Generating secure JWT secret key..."; \
		echo "SECRET_KEY=prod-$$(openssl rand -hex 32)" >> custom-certs.env; \
	fi
	@if ! grep -q "^ENCRYPTION_KEY=" custom-certs.env 2>/dev/null; then \
		echo "🔐 Generating encryption key for SSO..."; \
		if ! python3 -c "from cryptography.fernet import Fernet" 2>/dev/null; then \
			echo "⚠️  Warning: cryptography module not found. Installing..."; \
			pip3 install cryptography > /dev/null 2>&1 || (echo "❌ Failed to install cryptography. Please install manually: pip3 install cryptography"; exit 1); \
		fi; \
		ENCRYPTION_KEY=$$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"); \
		echo "ENCRYPTION_KEY=$$ENCRYPTION_KEY" >> custom-certs.env; \
	fi
	docker-compose -f docker-compose.custom-certs.yml --env-file custom-certs.env up -d
	@echo "✅ Services started with custom certificates!"
	@echo "🌐 Access your application at: https://$(grep DOMAIN custom-certs.env | cut -d= -f2)"

# Stop custom certificates deployment
custom-certs-stop:
	@echo "🛑 Stopping custom certificates deployment..."
	docker-compose -f docker-compose.custom-certs.yml --env-file custom-certs.env down

# Show custom certificates logs
custom-certs-logs:
	@echo "📋 Showing custom certificates logs..."
	docker-compose -f docker-compose.custom-certs.yml --env-file custom-certs.env logs -f

# Reset admin password
reset-admin-password:
	@echo "🔐 Resetting admin password..."
	@if ! docker-compose -f docker-compose.prod.yml ps -q backend > /dev/null 2>&1; then \
		echo "❌ Backend container is not running. Please start with: make prod"; \
		exit 1; \
	fi
	@if [ -z "$(TENANT_SLUG)" ] || [ -z "$(ADMIN_EMAIL)" ]; then \
		echo "❌ Please provide TENANT_SLUG and ADMIN_EMAIL parameters"; \
		echo "Example: make reset-admin-password TENANT_SLUG=\"my-company\" ADMIN_EMAIL=\"admin@mycompany.com\""; \
		exit 1; \
	fi
	@if [ -z "$(NEW_PASSWORD)" ]; then \
		echo "🔐 No new password provided, generating secure password..."; \
		docker-compose -f docker-compose.prod.yml exec backend python app/reset_password.py reset "$(TENANT_SLUG)" "$(ADMIN_EMAIL)"; \
	else \
		echo "🔐 Using provided password..."; \
		docker-compose -f docker-compose.prod.yml exec backend python app/reset_password.py reset "$(TENANT_SLUG)" "$(ADMIN_EMAIL)" "$(NEW_PASSWORD)"; \
	fi

# List all tenants
list-tenants:
	@echo "🏢 Listing all tenants..."
	@if ! docker-compose -f docker-compose.prod.yml ps -q backend > /dev/null 2>&1; then \
		echo "❌ Backend container is not running. Please start with: make prod"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.prod.yml exec backend python app/reset_password.py list-tenants

# List admin users in a tenant
list-admins:
	@echo "👤 Listing admin users in tenant..."
	@if ! docker-compose -f docker-compose.prod.yml ps -q backend > /dev/null 2>&1; then \
		echo "❌ Backend container is not running. Please start with: make prod"; \
		exit 1; \
	fi
	@if [ -z "$(TENANT_SLUG)" ]; then \
		echo "❌ Please provide TENANT_SLUG parameter"; \
		echo "Example: make list-admins TENANT_SLUG=\"my-company\""; \
		exit 1; \
	fi
	docker-compose -f docker-compose.prod.yml exec backend python app/reset_password.py list-admins "$(TENANT_SLUG)"

# Reset Security Requirements
reset-security-requirements:
	@echo "🔄 Resetting ISA/IEC 62443 Security Requirements..."
	@if ! docker-compose -f docker-compose.prod.yml ps -q backend > /dev/null 2>&1; then \
		echo "❌ Backend container is not running. Please start with: make prod"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.prod.yml exec backend python app/reset_security_requirements.py

# Update Roles Permissions
update-roles:
	@echo "🔄 Updating roles with latest permissions..."
	@if ! docker-compose -f docker-compose.prod.yml ps -q backend > /dev/null 2>&1; then \
		echo "❌ Backend container is not running. Please start with: make prod"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.prod.yml exec backend python scripts/update_roles.py
	@echo "✅ Roles updated successfully!"

# Backup system
backup:
	@echo "💾 Creating Industrace backup..."
	@python3 scripts/backup.py --backup-dir backups
	@echo "✅ Backup completed!"

# Backup with logs
backup-full:
	@echo "💾 Creating full Industrace backup (including logs)..."
	@python3 scripts/backup.py --backup-dir backups --include-logs
	@echo "✅ Full backup completed!"

# List backups
backup-list:
	@echo "📋 Listing available backups..."
	@python3 scripts/backup.py --list

# Restore from backup
restore:
	@echo "⚠️  Restore will stop services and restore from backup"
	@echo "Usage: make restore BACKUP_FILE=backups/industrace_backup_YYYYMMDD_HHMMSS.tar.gz"
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "❌ Please specify BACKUP_FILE"; \
		echo "Example: make restore BACKUP_FILE=backups/industrace_backup_20240101_120000.tar.gz"; \
		echo ""; \
		echo "Available backups:"; \
		python3 scripts/backup.py --list; \
		exit 1; \
	fi
	@echo "🔄 Restoring from $(BACKUP_FILE)..."
	@python3 scripts/restore.py "$(BACKUP_FILE)"
	@echo "✅ Restore completed!"
	@echo "🚀 You can now start Industrace with: make prod"
