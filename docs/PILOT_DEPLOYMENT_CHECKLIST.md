# Pilot Deployment Checklist

Use this checklist before deploying Industrace v2.1.x in a **controlled pilot** or **pre-production** environment (internal network, limited users, non-critical ICS data).

For full installation steps see [INSTALLATION.md](INSTALLATION.md). For all environment variables see [CONFIGURATION.md](CONFIGURATION.md).

---

## 1. Infrastructure

- [ ] Docker and Docker Compose installed on the target host
- [ ] Minimum resources: 4 GB RAM, 20 GB disk (8 GB RAM recommended)
- [ ] Ports 80 and 443 available (or custom ports configured in Nginx)
- [ ] Host deployed on an **isolated or segmented network** (not directly exposed to the public internet unless strictly required)
- [ ] Firewall rules restrict access to authorized subnets only
- [ ] Persistent volumes configured for PostgreSQL data, `uploads/`, and `logs/`

## 2. Deploy with `make prod`

```bash
git clone https://github.com/industrace/industrace.git
cd industrace
make prod
```

`make prod` automatically:

- Generates `.env.prod` with `SECRET_KEY`, `ENCRYPTION_KEY`, `DB_PASSWORD`, `SETUP_TOKEN`
- Sets `EXTERNAL_API_DOCS_ENABLED=false`
- Runs `scripts/check-secrets.sh` before startup
- Starts Nginx with TLS (self-signed for local pilot; use custom certs for real domains)

After startup, note the generated secrets:

```bash
grep -E '^(SETUP_TOKEN|SECRET_KEY|DB_PASSWORD)=' .env.prod
```

Store `.env.prod` securely — **never commit it to version control**.

## 3. Security hardening (required)

- [ ] **`CORS_ORIGINS`** set to your real frontend URL(s) in `.env.prod`  
  Example: `CORS_ORIGINS=https://industrace.company.local`
- [ ] **`EXTERNAL_API_DOCS_ENABLED=false`** (default in `make prod`)
- [ ] **`SETUP_TOKEN`** set and kept secret (default in `make prod`)
- [ ] Complete initial setup **before** exposing the instance broadly
- [ ] If using the setup wizard, pass the token via `X-Setup-Token` header:
  ```bash
  curl -X POST https://your-host/api/setup/initialize \
    -H "Content-Type: application/json" \
    -H "X-Setup-Token: <value-from-.env.prod>" \
    -d '{ ... }'
  ```
- [ ] Change default admin password on first login (enforced by password policy)
- [ ] Limit initial users to **admin** role until RBAC is validated in your environment
- [ ] Review role assignments before granting **editor** or **viewer** access

## 4. TLS and certificates

- [ ] For local pilot: self-signed certs from `make prod` are acceptable
- [ ] For corporate pilot: use `make custom-certs-start` with your CA-signed certificates
- [ ] Avoid `make prod-cloud` (Traefik/Let's Encrypt) in production until out of BETA
- [ ] Verify HTTPS redirect: `curl -I http://your-host` → `301` to HTTPS

## 5. Backup and recovery

- [ ] Run initial backup after setup and demo data load:
  ```bash
  make backup
  ```
- [ ] Verify backup file exists in `backups/`
- [ ] Document restore procedure: `make restore BACKUP_FILE=backups/industrace_backup_*.tar.gz`
- [ ] Schedule recurring backups (cron or external tool)

## 6. Post-deploy validation

- [ ] Login works via HTTPS with cookie-based session
- [ ] Viewer user **cannot** create/edit assets via API (RBAC enforced)
- [ ] `/docs` and `/redoc` return 404 or are unreachable (docs disabled)
- [ ] `/performance/*` endpoints not available (`ENVIRONMENT=production`)
- [ ] `/setup/initialize` rejects requests without valid `X-Setup-Token`
- [ ] Audit log records login and critical operations
- [ ] `make test` passes in Docker before go-live

## 7. Operational monitoring

- [ ] Monitor `logs/industrace.log` and `logs/security.log`
- [ ] Configure tenant syslog forwarding if SIEM integration is required (optional)
- [ ] Plan image rebuild after `git pull` in production:
  ```bash
  docker compose -f docker-compose.prod.yml --env-file .env.prod build
  docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
  ```

## 8. Known limitations (pilot scope)

| Item | Status |
|------|--------|
| MFA / TOTP | Not yet implemented (roadmap) |
| High availability / Kubernetes | Not supported — Docker Compose only |
| `make prod-cloud` | BETA — not recommended for pilot |
| Network Probes | MVP in v2.1.0 — validate in lab before production OT networks |
| Redis in prod compose | Not included — rate limiting is per-process |

## 9. Go / No-Go criteria

**Go** for controlled pilot when all items in sections 1–6 are checked.

**No-Go** (wait for next release or restrict to admin-only lab) if:

- Instance must be exposed to the public internet without WAF/VPN
- Strict compliance requires MFA before any user access
- Multi-tenant RBAC must be audited by a third party (run `make test` and internal pen test first)

---

**Contact**: industrace@besafe.it  
**Last updated**: June 2026 — Industrace v2.1.x
