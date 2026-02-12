# Upgrade Safety: Reducing Risk When Many Things Change

Releases that introduce many changes (DB migrations, new environment variables, SSO, password policy, etc.) increase the risk of a failed upgrade. This guide summarises **how to reduce that risk** without changing the workflow you already use (backup, staging, rollback).

---

## Why Upgrades Can Go Wrong

- **Many migrations**: The Alembic chain must take the database from an old revision to the new one without errors; a single failed migration can block everything.
- **Configuration**: New required environment variables (e.g. `ENCRYPTION_KEY` for SSO, consistent `DB_PASSWORD`) not set → backend fails to start or errors at runtime.
- **New behaviour**: Password policy, RBAC permissions, and SSO flows require users and roles to be aligned with the new version.
- **Data**: Migrations that modify or move data may take time, hold locks, or fail on particular datasets.

By following the rules below and the existing upgrade guides, you can **greatly limit** the risk and have a clear plan if something goes wrong.

---

## Golden Rules for Safe Upgrades

### 1. Mandatory Backup Before Every Upgrade

Without a backup there is no reliable rollback.

```bash
make backup
# or full backup (DB + uploads + config + optional logs)
make backup-full
```

Store the file in a safe place (e.g. `backups/industrace_backup_YYYYMMDD_HHMMSS.tar.gz`) and **do not overwrite it** until you are sure the upgrade is stable. See [backup-restore.md](backup-restore.md).

### 2. Test the Upgrade in Staging (Strongly Recommended)

Before touching production:

1. Set up a staging environment (separate machine or another Docker stack).
2. Restore a **real** production backup there:
   ```bash
   make restore BACKUP_FILE=backups/industrace_backup_YYYYMMDD_HHMMSS.tar.gz
   ```
3. Update the code to the target version (e.g. tag `v2.0.0`) and config (`.env` / `.env.prod`).
4. Start the services (`make prod` or the compose file you use); migrations run on first backend startup.
5. Run a **functional checklist**: login, core data (assets, sites, zones), critical features (create/edit assets, permissions), and new features for the release (e.g. zones, compliance, notifications, SSO if enabled).

If something fails in staging, fix it (migrations, variables, documentation) **before** repeating the upgrade in production.

### 3. Read the Upgrade Notes for the Version

- **v1.x → v2**: Use the dedicated guide [UPGRADE_v1_TO_v2.md](UPGRADE_v1_TO_v2.md) and the notes in [release-notes.md](release-notes.md) (sections “Migration from v1.x” and “Breaking Changes”).
- For every version: check **CHANGELOG.md** and, if present, files like `UPGRADE_NOTES_*.md` or “Upgrade notes” sections in the release notes.
- Verify **new or changed environment variables** by comparing with `.env.example` (and `custom-certs.env.example` if you use custom certificates).

This avoids “that variable was missing” or “we didn’t know about the password change” issues.

### 4. Have a Clear Rollback Plan

Before starting the upgrade in production, know exactly:

- **Where** backups are stored and which file you would use for restore.
- **Restore command**: e.g. `make restore BACKUP_FILE=...` (see [backup-restore.md](backup-restore.md)).
- **Code version** to revert to if you roll back: e.g. `git checkout v1.1.0` or the previous tag/commit.
- **DB-only rollback** (if the issue is a single migration): `alembic downgrade <revision>` and then switch back to the previous version’s code (see [UPGRADE_v1_TO_v2.md](UPGRADE_v1_TO_v2.md#5-rollback-reverting-to-v1)).

If something goes wrong, you don’t waste time deciding what to do.

### 5. After the Upgrade: Quick Checks

- Check backend logs: `make logs-backend` (or `docker-compose logs backend`) for migration or DB connection errors.
- Verify Alembic revision:  
  `docker-compose -f docker-compose.prod.yml exec backend alembic current`  
  should match the head for the installed version.
- Login, core data, and one or two critical operations (e.g. edit asset, create zone) to confirm the application responds correctly.

Keep the backup for at least a few days until you are confident you won’t need a rollback.

---

## Procedure Summary

| What to do | Reference |
|------------|------------|
| Backup before upgrade | [backup-restore.md](backup-restore.md), `make backup` |
| General upgrade (automatic / manual) | [UPGRADE.md](UPGRADE.md) |
| Major upgrade v1 → v2 (three-phase plan) | [UPGRADE_v1_TO_v2.md](UPGRADE_v1_TO_v2.md) |
| Password policy and user password change | [UPGRADE_PASSWORD_POLICY.md](UPGRADE_PASSWORD_POLICY.md) |
| Issues after upgrade (DB, auth, frontend) | [troubleshooting.md](troubleshooting.md) |
| Restore from backup | [backup-restore.md](backup-restore.md), `make restore` |

---

## Quick Pre-Upgrade Checklist (Keep Handy)

- [ ] Backup completed and stored (`make backup` or `make backup-full`)
- [ ] Target version documentation read (CHANGELOG, upgrade notes, breaking changes)
- [ ] `.env` / `.env.prod` updated with required variables (compare with `.env.example`)
- [ ] (Recommended) Upgrade tested in staging with a real backup
- [ ] Maintenance window communicated to users (if in production)
- [ ] Rollback plan clear: where backups are, restore command, tag/commit to revert to

---

*This document complements [UPGRADE.md](UPGRADE.md) and [UPGRADE_v1_TO_v2.md](UPGRADE_v1_TO_v2.md) and does not replace them. For detailed operational steps, always refer to those guides.*
