# Industrace Upgrade Guide: v1 to v2

This guide explains how to plan and run an upgrade from a **v1.x** installation (1.0 or 1.1) to **v2**, when many code changes have been made and you need a clear, safe path.

---

## Why This Guide

A **v1 → v2** upgrade is a **major upgrade** (Semantic Versioning): there may be breaking changes, new DB migrations, different environment variables, and configuration changes. This guide helps you to:

- **Prepare** the upgrade (what to document, what to test)
- **Run** the upgrade in a controlled way (backup, staging, production)
- **Recover** if something goes wrong (rollback)

---

## 1. Before Releasing v2: What to Document

Before considering v2 complete, have these items written and up to date.

### 1.1 Breaking Changes

A clear list of what is **no longer** compatible with v1:

- [ ] **API**: endpoints removed, renamed, or with different request/response payloads
- [ ] **Behaviour**: visible changes to features (e.g. permissions, validations)
- [ ] **Configuration**: environment variables renamed or made required
- [ ] **Database**: columns/tables removed or renamed (beyond Alembic migrations)

**Where to document**: in `CHANGELOG.md` under the `[2.0.0]` section as "Breaking changes", and/or in a `BREAKING_CHANGES_v2.md` file.

### 1.2 New Environment Variables

- [ ] Compare `.env.example` (and `custom-certs.env.example`) between v1 and v2
- [ ] List **new** required or recommended variables
- [ ] Note any **deprecated** variables and how to replace them

### 1.3 Database Migrations

- [ ] Ensure all Alembic migrations are in `backend/alembic/versions/`
- [ ] Test the migration chain **from a v1 DB** (1.0 or 1.1) up to `alembic upgrade head`
- [ ] Document migrations that require **downtime** or are slow (large tables)

See also: [docs/BACKEND_DATABASE_ANALYSIS.md - Migration strategy](BACKEND_DATABASE_ANALYSIS.md).

### 1.4 External Configuration Files

- [ ] `docker-compose.prod.yml` / nginx / other files: changes users must apply or merge
- [ ] If there are new templates, indicate where to copy them (e.g. `cp .env.example .env`)

---

## 2. Three-Phase Upgrade Strategy

### Phase A: Preparation (Before Upgrade Day)

1. **Full backup**
   ```bash
   make backup
   # or full backup including logs
   make backup-full
   ```
   Store the file safely (e.g. `backups/industrace_backup_YYYYMMDD_HHMMSS.tar.gz`).

2. **Documentation**
   - Read this guide and [UPGRADE.md](UPGRADE.md)
   - Read the CHANGELOG / BREAKING_CHANGES for v2
   - Check the list of new environment variables and prepare updates to `.env` / `.env.prod`

3. **Staging environment (recommended)**
   - Clone or restore a backup to a test environment
   - Run the upgrade on staging and verify login, data, and critical features
   - This reduces risk in production

### Phase B: Running the Upgrade (Upgrade Day)

1. **Notify** users of any maintenance window.

2. **Immediate backup before upgrade**
   ```bash
   make backup
   ```

3. **Stop services**
   ```bash
   make stop
   ```

4. **Update code**
   ```bash
   git fetch origin
   git checkout v2.0.0   # or the v2 branch/tag
   # If using main/develop:
   # git pull origin main
   ```

5. **Update configuration**
   - Update `.env` / `.env.prod` with new variables (see `.env.example` and v2 release notes)
   - If needed: manually merge your customisations in `docker-compose.prod.yml`, nginx, etc.

6. **Start the environment**
   ```bash
   make prod
   ```
   The backend applies missing Alembic migrations on startup.

7. **Check logs**
   ```bash
   make logs-backend
   ```
   Ensure there are no migration or DB connection errors.

### Phase C: After the Upgrade

1. **Functional checklist**
   - [ ] Login with existing users
   - [ ] Core data visible (assets, sites, areas, etc.)
   - [ ] Critical features (create/edit assets, permissions, etc.)
   - [ ] New v2 features (if documented)

2. **Migration status**
   ```bash
   docker-compose -f docker-compose.prod.yml exec backend alembic current
   ```
   Verify the revision matches what you expect for v2.

3. **Keep the backup** for at least a few days until you are confident a rollback is not needed.

---

## 3. Quick Procedure (Command Summary)

For those who have already read the guide and done backup and staging.

```bash
# 1. Backup
make backup

# 2. Stop
make stop

# 3. Code (example with tag v2.0.0)
git fetch origin && git checkout v2.0.0

# 4. Config: update .env.prod / .env with any new variables
# (see .env.example and v2 release notes)

# 5. Start (migrations run automatically on first backend startup)
make prod

# 6. Verify
make logs-backend
docker-compose -f docker-compose.prod.yml exec backend alembic current
```

---

## 4. Database Migrations (Detail)

- Migrations are managed by **Alembic** and applied **automatically** when the backend starts (standard Industrace behaviour).
- The revision chain in `backend/alembic/versions/` must allow upgrading from the current (v1) revision to the v2 "head" without missing steps.

**Useful commands**

```bash
# Current DB revision
docker-compose -f docker-compose.prod.yml exec backend alembic current

# History and heads
docker-compose -f docker-compose.prod.yml exec backend alembic history
docker-compose -f docker-compose.prod.yml exec backend alembic heads

# Manual apply (if you prefer not to rely only on startup)
make migrate
# or
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

If a migration fails, the backend logs will show the error; in that case, stop, restore the DB backup (or full backup with `make restore`), fix the migration in development, and re-test.

---

## 5. Rollback (Reverting to v1)

Use only if the upgrade fails and you need to go back to v1.

### 5.1 Restore from Backup (Recommended)

```bash
make stop
make restore BACKUP_FILE=backups/industrace_backup_YYYYMMDD_HHMMSS.tar.gz
git checkout v1.1.0   # or the latest v1 tag/branch
make prod
```

Then verify that everything works and data is consistent.

### 5.2 Migration Rollback Only (Without Restoring Backup)

Use only when the issue is a single migration and you have not made many data changes.

```bash
# Go back one revision
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade -1

# Or to a specific revision (v1 revision id)
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade <revision_id>
```

After downgrading, you should still switch back to v1 code and restart (`make stop`, checkout v1, `make prod`), otherwise v2 code may not match the reverted DB schema.

---

## 6. Troubleshooting

| Issue | What to do |
|-------|------------|
| Alembic migration error | Check `make logs-backend`. If the migration is wrong, restore backup, fix the migration in dev, re-test and re-run the upgrade. |
| Backend won't start / crashes right after upgrade | Check environment variables (`.env.prod`), especially `DATABASE_URL`, `SECRET_KEY`, `ENCRYPTION_KEY`. Ensure the DB is reachable (e.g. `db` container is up). |
| "Password authentication failed" for DB | See the guide on [make clean / make prod and DB password](UPGRADE.md). In short: after a clean, the DB volume must be removed; otherwise the DB password does not match `.env.prod`. |
| Missing or odd data after upgrade | Verify all migrations were applied (`alembic current` vs `alembic heads`). If needed, rollback and restore from backup, then analyse the migration that touches that data. |
| Frontend not updated | Rebuild images: `make rebuild` then `make prod`, or `docker-compose -f docker-compose.prod.yml build frontend --no-cache` and restart. |

---

## 7. Pre-Upgrade Checklist (Print or Keep Handy)

- [ ] Backup completed and stored (`make backup` or `make backup-full`)
- [ ] v2 documentation read (CHANGELOG, breaking changes, new env vars)
- [ ] `.env` / `.env.prod` updated with new variables (if required)
- [ ] (Recommended) Upgrade tested on staging with real backup
- [ ] Maintenance window communicated to users (if in production)
- [ ] Rollback plan clear (where backups are, `make restore` command)

---

## 8. References

- [UPGRADE_SAFETY.md](UPGRADE_SAFETY.md) – Reducing upgrade risk (backup, staging, rollback, checklist)
- [UPGRADE.md](UPGRADE.md) – General upgrade and automatic procedures
- [BACKEND_DATABASE_ANALYSIS.md](BACKEND_DATABASE_ANALYSIS.md) – Migration strategy and best practices
- [backup-restore.md](backup-restore.md) – Backup and restore
- [CHANGELOG.md](../CHANGELOG.md) – Changes per version
- [RELEASE_GUIDE.md](../RELEASE_GUIDE.md) – Release process (adaptable for v2)

---

*Last updated: January 2026. For v2.0.0 release, complement this guide with release-specific notes (BREAKING_CHANGES, new env vars, etc.).*
