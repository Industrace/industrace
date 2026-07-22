# Development Roadmap

## Overview

This roadmap outlines the development path for Industrace, the Configuration Management Database for Industrial Control Systems. The focus is on stability, documentation, and community growth.

**Current version:** v2.2.0 (July 2026) — **pilot recommended**; not validated for production OT environments without lab testing.

## Delivered in v2.0 (June 2026)

The following major features were delivered in version 2.0:

- **ISA/IEC 62443 Compliance**: Security zones, conduits, security requirements, capabilities, SR assessments, evidence
- **Vulnerability Intelligence**: CVE management, vulnerability feeds, automatic matching, risk integration
- **Asset Dependencies and Review**: Dependency graph, risk propagation, asset review and maintenance scheduling
- **Notification System**: Templates, queue, logs, user preferences, email integration
- **Single Sign-On (SSO)**: Azure AD / Microsoft Entra ID integration
- **Extended RBAC**: New permission sections for all new modules; see [ADMINISTRATION.md](ADMINISTRATION.md#role-based-access-control-rbac)
- **Password Policy**: Stricter requirements (12+ chars, complexity); see [ADMINISTRATION.md](ADMINISTRATION.md#password-policy)
- **Asset Detail Redesign**: New layout with tabs for Security, Dependencies, Vulnerabilities, IEC 62443, Review

See [Release Notes](release-notes.md) and [CHANGELOG](../CHANGELOG.md) for full details.

## Delivered in v2.1.x and v2.2.0

### v2.1.0 — Network Probes MVP and IEC 62443 RE

- **Network Probes (MVP)**: probe client, discovered devices, asset matching, UI pages, background maintenance
- **Syslog external forwarding**: tenant syslog configuration and audit log forwarding
- **IEC 62443 RE 1–4**: requirement enhancement texts, RE-level assessment, audit export CSV/JSON

### v2.1.1 — Security hardening and pilot readiness

- Router-level RBAC on core API endpoints; setup wizard protected via `SETUP_TOKEN`
- HttpOnly cookie authentication (no `localStorage` tokens)
- [Pilot Deployment Checklist](PILOT_DEPLOYMENT_CHECKLIST.md) and [IEC 62443 scope guide](IEC62443.md)

### v2.2.0 — Pilot stability

- **CSV bulk import**: users, sites, locations (UI + templates)
- **Deep health checks**: `/health` verifies database and Redis (SSO state); Docker healthchecks on backend and PostgreSQL
- **CI coverage gate** on critical backend modules
- **Network Probes — pilot-stable**: statistics and matches API, operational [runbook](../probe/RUNBOOK.md), hardening complete per [NETWORK_PROBE.md](../probe/NETWORK_PROBE.md)
- **Asset detail**: real relation and critical vulnerability badge counts
- **IEC 62443 zone compliance**: SR-relevant asset filtering and technical characteristics in UI

## Current Priorities

### Multi-Deployment Support ✅

- **Development**: Vite dev server with hot-reload
- **Production (local)**: Nginx + self-signed TLS (`make prod`)
- **Production (cloud)**: Traefik + Let's Encrypt (`make prod-cloud`, **BETA**)
- **Custom certificates**: Nginx + CA-signed certs (`make custom-certs-*`)
- **Automatic configuration**: CORS, cookies, and security settings

### Documentation and Support — partial (~70%)

**Done:**

- Installation, configuration, administration, API, migration, troubleshooting guides — see [docs/README.md](README.md)
- Probe documentation and operational runbook — [probe/README.md](../probe/README.md), [probe/RUNBOOK.md](../probe/RUNBOOK.md)
- Pilot deployment checklist

**Remaining:**

- Complete end-to-end user manual and FAQ
- Keep roadmap and pilot checklist aligned with each release

### Security Enhancements — delivered (MFA/TOTP)

- Multi-Factor Authentication (MFA) for local password users
- TOTP-based login step (`/login` → `/login/mfa`)
- Backup codes for account recovery
- Tenant MFA policy (`optional` / `required_admins` / `required_all`) with grace period
- Admin MFA reset + security/audit logging

**Design reference:** [MFA_TOTP_IMPLEMENTATION.md](MFA_TOTP_IMPLEMENTATION.md)

> **Pilot note:** Enable MFA (Industrace TOTP for local users and/or IdP MFA for SSO) when compliance requires it. See [PILOT_DEPLOYMENT_CHECKLIST.md](PILOT_DEPLOYMENT_CHECKLIST.md).

### Mobile Strategy — partial (~40%)

**Done:**

- Responsive web application design
- Touch-optimized user interface and mobile-first navigation

**Remaining (planned v2.3.x):**

- Progressive Web App (PWA): `manifest.json`, service worker
- Offline support and push notifications (future consideration)

### Stability and Performance — in progress (~60%)

**Done in v2.2.0:**

- Deep health checks and Docker healthchecks
- CI coverage gate on critical modules
- Probe and RBAC hardening

**Open:**

- Probe residual backlog (bulk ingest, frontend smoke tests) — see [NETWORK_PROBE.md](../probe/NETWORK_PROBE.md) §8
- Broader test coverage across all API paths
- Incremental performance and bug-fix work based on pilot feedback

## Future Considerations

### Potential Improvements

- Advanced reporting features
- External system integrations
- Customizable workflows
- Native mobile applications (if required; roadmap prefers PWA)

### Technology Evolution

- Architecture improvements
- Database optimizations (e.g. TimescaleDB for probe telemetry)
- API enhancements
- High availability (load balancer + DB replica)
- PWA capabilities (offline support, push notifications)

## Goals

### Technical

- Stability and reliability
- Optimal performance
- Robust security
- Easy maintenance
- Mobile accessibility

### Community

- Complete documentation
- Active support
- Organic growth
- Continuous feedback

## Conclusion

Industrace has delivered the core v2 feature set (CMDB ICS, IEC 62443, CVE intelligence, Network Probes) and entered a **pilot stability** phase with v2.2.0. The next wave targets **MFA/TOTP**, **PWA**, complete user documentation, and incremental hardening — driven by pilot feedback rather than large new feature blocks.

---

**Industrace** - Configuration Management Database for Industrial Control Systems  
**Author**: Maurizio Bertaboni  
**Website**: https://besafe.it/industrace  
**Contact**: industrace@besafe.it

*Last Updated: July 2026*
