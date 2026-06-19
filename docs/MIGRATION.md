# Migration and upgrades

This guide explains how Industrace versions relate to each other, how to move from **Industrace 1.x** to **2.x**, and how to upgrade within the **2.x** line.

---

## Version policy

### Industrace 1.x — frozen

- **Last release line**: `v1.0.0` (Git tag).
- **Status**: maintenance only; no new features.
- **Use case**: legacy deployments that cannot move to v2 yet.

Do not expect v1 to receive IEC 62443, Network Probes, SSO, Vulnerability Intelligence, or other v2 capabilities.

### Industrace 2.x — current product

- **Current line**: 2.0.0, 2.1.0, …
- **Scope**: multi-tenant CMDB with ISA/IEC 62443 (optional per tenant), vulnerabilities, notifications, SSO, Network Probes, extended RBAC, and more.

**Important:** Moving from v1 to v2 is **not** a typical in-place upgrade (`git pull` on the same stack). Treat it as a **new installation** of Industrace 2, then bring over only what you can export manually from v1.

---

## From Industrace 1 to 2 (recommended path)

### 1. Plan a parallel or greenfield install

1. **Back up v1** completely before any change (see [Backup and restore](#backup-and-restore) below).
2. Install **Industrace 2** on a **new** host or Docker stack (see [INSTALLATION.md](INSTALLATION.md) and [QUICK_START.md](QUICK_START.md)).
3. Run the setup wizard or initial tenant configuration on v2.
4. Keep v1 running in parallel until v2 is validated (optional but recommended).

### 2. What you can recover manually

| Data / area | Manual recovery | Notes |
|-------------|-----------------|-------|
| Sites, areas, locations | CSV export/import where available in v1 | Re-create hierarchy in v2 if needed |
| Manufacturers, suppliers, contacts | CSV or re-entry | Check v1 export features |
| Assets and interfaces | CSV export from v1 → import in v2 | Validate field mapping; IDs will change |
| Users | Re-create in v2 | Passwords are not portable; use SSO on v2 if possible |
| Roles / permissions | Reconfigure | v2 RBAC is different; run `make update-roles` on v2 |
| Network map / connections | Partial | May need re-discovery or probe on v2 |
| Documents / photos | Copy `uploads/` files if paths align | Prefer clean upload via v2 UI after asset import |
| Audit logs | Export from v1 for archive | Not automatically imported into v2 |

### 3. What does **not** migrate automatically

- ISA/IEC 62443 zones, conduits, SR assessments, evidence
- Vulnerability feeds and CVE matches
- Notification templates, queue, preferences
- SSO / Azure AD configuration and encrypted secrets
- Network Probes and discovered devices
- API keys and external integration settings
- Custom roles beyond what you recreate in v2

### 4. Cutover checklist

- [ ] v1 backup stored safely (`make backup` or `make backup-full`)
- [ ] v2 installed and reachable ([INSTALLATION.md](INSTALLATION.md))
- [ ] Critical data imported or re-entered in v2
- [ ] Users and roles configured ([ADMINISTRATION.md](ADMINISTRATION.md))
- [ ] Optional modules set in Setup (e.g. IEC 62443) — [CONFIGURATION.md](CONFIGURATION.md)
- [ ] Smoke test: login, assets, permissions, critical workflows
- [ ] DNS / URL / certificates switched to v2
- [ ] v1 decommissioned or kept read-only for reference

### Technical note (in-place v1 DB → v2)

Running Alembic migrations on a **live v1 database** to reach v2 schema is **unsupported** as the primary path: schema and product assumptions diverged too far. If you attempt it in a lab, use a **copy** of the database only; do not rely on it for production without full regression testing.

---

## Upgrading within Industrace 2.x (e.g. 2.0 → 2.1)

Minor and patch releases within 2.x use the standard Docker workflow.

### Automatic upgrade (recommended)

```bash
# 1. Backup
make backup

# 2. Stop
docker compose -f docker-compose.prod.yml --env-file .env.prod down

# 3. Update code
git pull origin main   # or checkout the release tag, e.g. v2.1.0

# 4. Rebuild images (required in production — code is not mounted as a volume)
docker compose -f docker-compose.prod.yml --env-file .env.prod build backend frontend
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 5. Migrations and roles (if not applied on startup)
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend alembic upgrade head
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python scripts/update_roles.py
```

Migrations usually run on backend startup; steps 5 confirm head revision and new permissions (e.g. `network_probes`, `external_log`).

### Check migration status

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend alembic current
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend alembic heads
```

### After upgrade

- Read [CHANGELOG.md](../CHANGELOG.md) and [release-notes.md](release-notes.md) for the target version.
- Compare `.env` with `.env.example` for new variables (`PROBE_*`, `ENCRYPTION_KEY`, etc.).
- Verify login, core data, and new features.
- See [troubleshooting.md](troubleshooting.md) if the backend fails to start.

### What is not automatic

- New **environment variables** — update `.env` / `.env.prod`
- **Custom** `nginx.conf` or compose overrides — merge manually
- **Frontend** — rebuild image in prod (see commands above)

---

## Upgrade safety

### Golden rules

1. **Backup before every upgrade** — no backup, no safe rollback.
2. **Test in staging** — restore a real backup to a test stack and upgrade there first.
3. **Read release notes** — breaking changes and new env vars are in CHANGELOG / release-notes.
4. **Know your rollback** — backup location, `make restore`, previous Git tag.
5. **Verify after upgrade** — logs, `alembic current`, login, critical workflows.

### Pre-upgrade checklist

- [ ] Backup completed (`make backup` or `make backup-full`)
- [ ] Release notes and CHANGELOG read for target version
- [ ] `.env` / `.env.prod` updated (compare with `.env.example`)
- [ ] (Recommended) Upgrade tested on staging with a real backup
- [ ] Users notified if production maintenance window
- [ ] Rollback plan documented

---

## Backup and restore

### Quick backup (Makefile)

```bash
make backup          # database + uploads + config
make backup-full     # includes logs
```

Backups are stored under `backups/` (e.g. `industrace_backup_YYYYMMDD_HHMMSS.tar.gz`).

### Restore

```bash
make restore BACKUP_FILE=backups/industrace_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Manual backup script

```bash
python scripts/backup.py
python scripts/backup.py --include-logs
python scripts/backup.py --list
```

### Restore options

```bash
# Stop stack first
docker compose -f docker-compose.prod.yml --env-file .env.prod down

# Full restore
python scripts/restore.py --backup-dir /path/to/backup --restore-all

# Selective
python scripts/restore.py --backup-dir /path/to/backup --restore-database
python scripts/restore.py --backup-dir /path/to/backup --restore-files
```

### Rollback after a failed 2.x upgrade

1. Stop services.
2. Restore backup: `make restore BACKUP_FILE=...`
3. Checkout previous tag: `git checkout v2.0.0` (or previous commit).
4. Rebuild and start: `docker compose ... build && up -d`

For a **single bad migration** (advanced): `alembic downgrade -1`, then align code to the matching revision.

---

## Troubleshooting upgrades

| Issue | What to do |
|-------|------------|
| Migration error | `make logs-backend`; fix migration in dev; restore backup if needed |
| Backend won't start | Check `DATABASE_URL`, `SECRET_KEY`, `ENCRYPTION_KEY` in `.env.prod` |
| DB password mismatch after `make clean` | Remove DB volume or align password in `.env.prod` with volume |
| Frontend shows old UI | Rebuild frontend image: `docker compose ... build frontend --no-cache` |
| Missing menu / permissions | `python scripts/update_roles.py` inside backend container |

More detail: [troubleshooting.md](troubleshooting.md).

---

## References

- [INSTALLATION.md](INSTALLATION.md) — deploy v2 from scratch
- [CONFIGURATION.md](CONFIGURATION.md) — environment and optional modules
- [ADMINISTRATION.md](ADMINISTRATION.md) — users, RBAC, SSO, password policy
- [CHANGELOG.md](../CHANGELOG.md) — per-version changes
- [release-notes.md](release-notes.md) — release summaries
