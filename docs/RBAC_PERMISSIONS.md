# Expanded RBAC System - Industrace

## Overview

Industrace's RBAC (Role-Based Access Control) system has been expanded to include all new features added to the system. This document describes the available permission sections and access levels for each.

## Permission Structure

The RBAC system uses a model based on **sections** and **levels**:

- **Sections**: Functional areas of the system (e.g., `assets`, `vulnerabilities`, `compliance`)
- **Levels**: Numeric access levels (0-4):
  - **0**: No access
  - **1**: Read
  - **2**: Write (modify)
  - **3**: Delete (administration)
  - **4**: Bulk/Advanced (bulk operations and advanced analytics)

## Sezioni di Permessi

### Sezioni Esistenti

Queste sezioni erano già presenti nel sistema originale:

- `assets` - Gestione asset industriali
- `sites` - Gestione siti
- `areas` - Gestione aree
- `locations` - Gestione ubicazioni
- `suppliers` - Gestione fornitori
- `contacts` - Gestione contatti
- `manufacturers` - Gestione produttori
- `asset_types` - Gestione tipi di asset
- `asset_statuses` - Gestione stati asset
- `users` - Gestione utenti
- `roles` - Gestione ruoli
- `audit_logs` - Visualizzazione log di audit
- `utility` - Funzioni di utilità
- `asset_documents` - Gestione documenti asset
- `asset_photos` - Gestione foto asset
- `locations_floormap` - Gestione mappe dei piani
- `reset_user_password` - Reset password utenti

### Nuove Sezioni

#### `vulnerabilities`
**Descrizione**: Gestione vulnerabilità e CVE

- **Livello 1 (Read)**: Visualizzare vulnerabilità e vulnerabilità asset
- **Livello 2 (Write)**: Creare/modificare vulnerabilità, gestire status vulnerabilità asset
- **Livello 3 (Delete)**: Eliminare vulnerabilità, gestire feed di vulnerabilità
- **Livello 4 (Bulk)**: Operazioni bulk su vulnerabilità

**Endpoint protetti**:
- GET `/vulnerabilities` - Lista vulnerabilità
- GET `/vulnerabilities/{id}` - Dettaglio vulnerabilità
- POST `/vulnerabilities` - Crea vulnerabilità
- GET `/vulnerabilities/assets/{asset_id}` - Vulnerabilità di un asset
- PUT `/vulnerabilities/assets/{asset_id}/vulnerabilities/{id}` - Aggiorna status vulnerabilità
- GET/POST `/vulnerabilities/feeds` - Gestione feed vulnerabilità

#### `asset_reviews`
**Descrizione**: Gestione review e manutenzione asset

- **Livello 1 (Read)**: Visualizzare review status e asset in scadenza
- **Livello 2 (Write)**: Marcare asset come reviewati, saltare review
- **Livello 3 (Delete)**: Ricalcolare tutte le date review, operazioni bulk
- **Livello 4 (Bulk)**: Gestione completa review

**Endpoint protetti**:
- GET `/assets/{id}/review-status` - Status review asset
- POST `/assets/{id}/review` - Marca asset come reviewato
- POST `/assets/{id}/review/skip` - Salta review
- GET `/assets/review/due` - Asset in scadenza
- GET `/assets/review/overdue` - Asset scaduti
- POST `/assets/review/bulk` - Review bulk
- POST `/assets/review/recalculate-all` - Ricalcola tutte le date

#### `asset_dependencies`
**Descrizione**: Gestione dipendenze tra asset

- **Livello 1 (Read)**: Visualizzare dipendenze tra asset
- **Livello 2 (Write)**: Creare/modificare dipendenze
- **Livello 3 (Delete)**: Eliminare dipendenze
- **Livello 4 (Bulk)**: Eseguire analisi avanzate (propagazione rischio, impact analysis)

**Endpoint protetti**:
- GET `/asset-dependencies` - Lista dipendenze
- POST `/asset-dependencies` - Crea dipendenza
- PUT/DELETE `/asset-dependencies/{id}` - Modifica/elimina dipendenza
- GET `/asset-dependencies/assets/{id}/risk-propagation` - Propagazione rischio
- GET `/asset-dependencies/assets/{id}/impact-analysis` - Analisi impatto

#### `compliance`
**Descrizione**: Gestione compliance ISA/IEC 62443

- **Livello 1 (Read)**: Visualizzare stato compliance, assessment SR
- **Livello 2 (Write)**: Creare/modificare assessment SR, gestire evidence
- **Livello 3 (Delete)**: Gestire completamente compliance, zone, conduits, capabilities
- **Livello 4 (Bulk)**: Amministrazione completa compliance

**Endpoint protetti**:
- GET `/compliance/zone/{id}/foundation-requirements` - Foundation Requirements
- GET `/compliance/zone/{id}/security-requirements/{fr_id}` - Security Requirements
- GET `/compliance/zone/{id}/sr/{sr_id}/assessment-assist` - Assist assessment
- POST `/compliance/zone/{id}/sr/{sr_id}/assessment` - Crea/aggiorna assessment
- GET `/compliance/gap-analysis` - Gap analysis

#### `security_zones`
**Descrizione**: Gestione security zones

- **Livello 1 (Read)**: Visualizzare security zones e membership
- **Livello 2 (Write)**: Creare/modificare zone, gestire membership asset
- **Livello 3 (Delete)**: Eliminare zone, calcolare security level
- **Livello 4 (Bulk)**: Gestione completa zone e analisi rischio

**Endpoint protetti**:
- GET `/security-zones` - Lista zone
- POST `/security-zones` - Crea zone
- PUT/DELETE `/security-zones/{id}` - Modifica/elimina zone
- GET `/security-zones/{id}/assets` - Asset in zona
- GET `/security-zones/{id}/compliance` - Compliance zona
- POST `/security-zones/{id}/calculate-sl` - Calcola Security Level
- POST `/security-zones/{id}/memberships` - Gestione membership

#### `notifications`
**Descrizione**: Gestione notifiche e preferenze

- **Livello 1 (Read)**: Visualizzare notifiche personali e log
- **Livello 2 (Write)**: Gestire preferenze personali, inviare notifiche di test
- **Livello 3 (Delete)**: Gestire template notifiche, coda notifiche
- **Livello 4 (Bulk)**: Amministrazione completa notifiche

**Endpoint protetti**:
- GET `/notifications/preferences` - Preferenze personali
- POST/PUT/DELETE `/notifications/preferences/{id}` - Gestione preferenze
- GET `/notifications/templates` - Template notifiche
- PUT `/notifications/templates/{code}` - Modifica template (admin)
- GET `/notifications/queue` - Coda notifiche (admin)
- POST `/notifications/test` - Test notifica

#### `sso`
**Descrizione**: Gestione Single Sign-On

- **Livello 1 (Read)**: Visualizzare configurazione SSO (solo se abilitato)
- **Livello 2 (Write)**: Configurare SSO, testare connessione
- **Livello 3 (Delete)**: Importare utenti da provider SSO
- **Livello 4 (Bulk)**: Amministrazione completa SSO

**Endpoint protetti**:
- GET `/auth/sso/config` - Configurazione SSO
- POST/PUT/DELETE `/auth/sso/config` - Gestione configurazione
- POST `/auth/sso/test` - Test connessione
- GET `/auth/sso/azure-ad/users` - Lista utenti Azure AD
- POST `/auth/sso/azure-ad/import` - Importa utenti

#### `api_keys`
**Descrizione**: Gestione API keys per integrazioni esterne

- **Livello 1 (Read)**: Visualizzare API keys proprie
- **Livello 2 (Write)**: Creare/modificare API keys proprie
- **Livello 3 (Delete)**: Eliminare API keys proprie, gestire tutte le API keys
- **Livello 4 (Bulk)**: Amministrazione completa API keys

#### `evidence`
**Descrizione**: Gestione evidence per compliance

- **Livello 1 (Read)**: Visualizzare evidence
- **Livello 2 (Write)**: Creare/modificare evidence
- **Livello 3 (Delete)**: Eliminare evidence
- **Livello 4 (Bulk)**: Gestione completa evidence

## Ruoli Predefiniti

### Admin (Livello 3 - Amministrazione Completa)

Accesso completo a tutte le sezioni:

| Sezione | Livello | Descrizione |
|---------|---------|-------------|
| Tutti i moduli base | 3 | Gestione completa asset, siti, aree, etc. |
| `vulnerabilities` | 3 | Gestione completa vulnerabilità e CVE |
| `asset_reviews` | 3 | Gestione completa review e manutenzione |
| `asset_dependencies` | 3 | Gestione completa dipendenze e analisi |
| `compliance` | 3 | Gestione completa ISA/IEC 62443 |
| `security_zones` | 3 | Gestione completa zone di sicurezza |
| `evidence` | 3 | Gestione completa evidence compliance |
| `notifications` | 3 | Gestione completa notifiche e template |
| `sso` | 3 | Configurazione completa Single Sign-On |
| `api_keys` | 3 | Gestione completa API keys |
| `reset_user_password` | 1 | Reset password utenti |

### Editor (Livello 2 - Modifica)

Accesso read/write alle sezioni operative:

| Sezione | Livello | Descrizione |
|---------|---------|-------------|
| Moduli base | 2 | Modifica asset, siti, aree, etc. |
| `vulnerabilities` | 2 | Gestione vulnerabilità e status |
| `asset_reviews` | 2 | Gestione review e manutenzione |
| `asset_dependencies` | 2 | Gestione dipendenze |
| `security_zones` | 2 | Gestione zone e membership |
| `evidence` | 2 | Gestione evidence |
| `notifications` | 2 | Gestione preferenze personali |
| `compliance` | 1 | Solo lettura ISA/IEC 62443 |
| `sso` | 1 | Solo lettura configurazione SSO |
| `api_keys` | 1 | Visualizzazione API keys proprie |
| `users`, `roles` | 1 | Solo lettura utenti e ruoli |

### Viewer (Livello 1 - Solo Lettura)

Accesso read-only alle sezioni:

| Sezione | Livello | Descrizione |
|---------|---------|-------------|
| Tutti i moduli base | 1 | Solo lettura asset, siti, aree, etc. |
| `vulnerabilities` | 1 | Solo lettura vulnerabilità |
| `asset_reviews` | 1 | Solo lettura status review |
| `asset_dependencies` | 1 | Solo lettura dipendenze |
| `compliance` | 1 | Solo lettura ISA/IEC 62443 |
| `security_zones` | 1 | Solo lettura zone di sicurezza |
| `evidence` | 1 | Solo lettura evidence |
| `notifications` | 1 | Solo lettura notifiche personali |
| `users` | 0 | **Nessun accesso** |
| `sso` | 0 | **Nessun accesso** |
| `api_keys` | 0 | **Nessun accesso** |

## Utilizzo nel Codice

### Backend (FastAPI)

```python
from app.services.rbac import require_permission

@router.get("/endpoint")
def my_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    perm=Depends(require_permission("vulnerabilities", 1)),  # Read permission
):
    # Endpoint code
    pass
```

### Verifica Programmatica

```python
from app.services.rbac import check_permission, get_user_permission_level

# Verifica se l'utente ha un permesso
if check_permission(current_user, "vulnerabilities", 2):
    # L'utente può modificare vulnerabilità
    pass

# Ottieni il livello di permesso
level = get_user_permission_level(current_user, "vulnerabilities")
```

## Aggiornamento Ruoli

### Aggiornamento Automatico (Durante Upgrade)

Quando si aggiorna il sistema, la migrazione Alembic `update_roles_permissions` aggiornerà automaticamente tutti i ruoli con i permessi mancanti.

### Aggiornamento Manuale

Per aggiornare manualmente i ruoli esistenti con le nuove sezioni di permessi, eseguire:

```bash
# Via Makefile (consigliato)
make update-roles

# Oppure direttamente
docker-compose -f docker-compose.prod.yml exec backend python scripts/update_roles.py
```

Questo script aggiorna automaticamente tutti i ruoli (admin, editor, viewer) per tutti i tenant nel sistema, assicurando che tutti i permessi siano presenti.

## Note

- I permessi sono ereditati se il ruolo ha un `parent_role` e `is_inheritable` è `True`
- I permessi del ruolo figlio hanno precedenza su quelli del ruolo padre
- I permessi sono memorizzati come JSON nel campo `permissions` del modello `Role`
- Il sistema supporta multi-tenancy: ogni tenant ha i propri ruoli e permessi
