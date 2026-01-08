# Sistema RBAC Espanso - Industrace

## Panoramica

Il sistema RBAC (Role-Based Access Control) di Industrace è stato espanso per includere tutte le nuove funzionalità aggiunte al sistema. Questo documento descrive le sezioni di permessi disponibili e i livelli di accesso per ciascuna.

## Struttura dei Permessi

Il sistema RBAC utilizza un modello basato su **sezioni** e **livelli**:

- **Sezioni**: Aree funzionali del sistema (es: `assets`, `vulnerabilities`, `compliance`)
- **Livelli**: Livelli di accesso numerici (0-4):
  - **0**: Nessun accesso
  - **1**: Read (lettura)
  - **2**: Write (scrittura/modifica)
  - **3**: Delete (eliminazione/amministrazione)
  - **4**: Bulk/Advanced (operazioni massive e analisi avanzate)

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

### Admin
Accesso completo a tutte le sezioni (livello 3 o superiore per tutte).

### Editor
- Accesso read/write alle sezioni operative (assets, vulnerabilities, reviews, dependencies)
- Accesso read-only alle sezioni amministrative (compliance, security_zones, sso)
- Può gestire preferenze notifiche personali

### Viewer
- Accesso read-only a tutte le sezioni tranne:
  - `users`: nessun accesso
  - `sso`: nessun accesso
  - `api_keys`: nessun accesso
- Può visualizzare notifiche personali

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

## Migrazione

Per aggiornare i ruoli esistenti con le nuove sezioni di permessi, eseguire:

```bash
python -m app.expand_rbac_permissions
```

Questo script aggiorna automaticamente tutti i ruoli (admin, editor, viewer) per tutti i tenant nel sistema.

## Note

- I permessi sono ereditati se il ruolo ha un `parent_role` e `is_inheritable` è `True`
- I permessi del ruolo figlio hanno precedenza su quelli del ruolo padre
- I permessi sono memorizzati come JSON nel campo `permissions` del modello `Role`
- Il sistema supporta multi-tenancy: ogni tenant ha i propri ruoli e permessi
