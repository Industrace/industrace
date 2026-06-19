# Installation and deployment

Complete guide to installing Industrace 2.x. For a 5-minute path, see [QUICK_START.md](QUICK_START.md).

If you are on **Industrace 1.x**, read [MIGRATION.md](MIGRATION.md) first — v2 is a new installation, not an in-place upgrade.

---

## System requirements

| | Minimum | Recommended |
|---|---------|-------------|
| RAM | 4 GB | 8 GB+ |
| Storage | 20 GB | 50 GB SSD |
| CPU | 2 cores | 4+ cores |

**Software:** Docker Engine 20.10+, Docker Compose 2.0+, Git.

---

## Quick install (Docker + Make)

```bash
git clone https://github.com/industrace/industrace.git
cd industrace
```

### Production local (first-time, self-signed HTTPS)

```bash
make prod
```

- Application: https://localhost  
- API docs: https://localhost/api/docs  
- Uses `docker-compose.prod.yml` with Nginx

Use `--env-file .env.prod` if you have a custom env file:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

**Note:** Production images do not mount source code as volumes — after `git pull`, run `build backend frontend` before `up -d`.

### Production cloud (Traefik + Let's Encrypt)

```bash
make prod-cloud
```

- Application: https://industrace.local (configure DNS)  
- Traefik dashboard: http://localhost:8080

### Development

```bash
docker compose -f docker-compose.dev.yml up -d
```

- Backend: http://localhost:8000 (hot reload via volume mount)  
- Frontend: http://localhost:5173  
- Database: localhost:5432

### Useful Make targets

```bash
make stop      # stop services
make status    # service status
make logs      # follow logs
make migrate   # alembic upgrade head
make rebuild   # rebuild containers
make backup    # backup before upgrades
```

---

## Custom SSL certificates

For internal PKI, self-signed, or corporate CA certificates (no Let's Encrypt):

```bash
make custom-certs-setup
make custom-certs-start
```

1. Copy `custom-certs.env.example` → `custom-certs.env`
2. Set `DOMAIN`, `CERT_PATH`, `KEY_PATH`, `CA_PATH`
3. Run `./setup-custom-certs.sh` to validate certificates
4. Start with `docker-compose -f docker-compose.custom-certs.yml --env-file custom-certs.env up -d`

**Supported:** PEM/X.509, RSA 2048+ or ECDSA keys. Private key permissions: `600`.

**Troubleshooting certificates:**

```bash
openssl x509 -in certificate.crt -text -noout
openssl s_client -connect your-domain:443 -servername your-domain
```

See also [CONFIGURATION.md](CONFIGURATION.md) for environment variables.

---

## Initial setup

### Setup wizard

On first access, complete `/setup-wizard` if the system is not initialized.

### Default credentials (demo / auto-init)

- Email: `admin@example.com`  
- Password: `Admin@123456!`

You must change the password on first login (see [ADMINISTRATION.md](ADMINISTRATION.md#password-policy)).

### Demo data

`make prod` and `make prod-cloud` can seed sample sites, assets, and connections for evaluation.

---

## Manual Docker Compose

```bash
# Production
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Development
docker compose -f docker-compose.dev.yml up -d
```

---

## Native development (without Docker app containers)

**Backend:**

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg://user:pass@localhost/industrace"
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install && npm run dev
```

PostgreSQL 15+ required locally or via `docker compose -f docker-compose.dev.yml up -d db`.

---

## Production notes

- Set strong `SECRET_KEY`, `DB_PASSWORD`, and `ENCRYPTION_KEY` (required for SSO in production) — see [CONFIGURATION.md](CONFIGURATION.md)
- Rebuild images after code updates in prod
- Run `alembic upgrade head` and `python scripts/update_roles.py` after version upgrades — [MIGRATION.md](MIGRATION.md)
- Backup before upgrades: `make backup`

---

## Troubleshooting installation

| Issue | Action |
|-------|--------|
| Port 80/443 in use | `sudo lsof -i :80` — stop conflicting nginx/apache |
| DB auth failed | Align `DB_PASSWORD` in `.env.prod` with Postgres volume; see [troubleshooting.md](troubleshooting.md) |
| Blank UI after upgrade | Rebuild frontend image |
| `ENCRYPTION_KEY` error in prod | Set in `.env.prod` — generate with Fernet (see CONFIGURATION) |

Full guide: [troubleshooting.md](troubleshooting.md)

---

## Next steps

1. [CONFIGURATION.md](CONFIGURATION.md) — environment and optional modules  
2. [ADMINISTRATION.md](ADMINISTRATION.md) — users, RBAC, SSO  
3. [MIGRATION.md](MIGRATION.md) — upgrades and backup  
4. [Network Probe](../probe/README.md) — optional distributed discovery (separate docs)
