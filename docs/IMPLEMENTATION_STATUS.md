# Stato Implementazione - Industrace

**Data Report**: 2025-12-23  
**Ultimo Aggiornamento**: 2025-12-23  
**Repository**: `industrace-dev` (sviluppo privato)

## 📊 Riepilogo Generale

| Categoria | ✅ Implementato | 🔄 Parziale | ❌ Non Implementato | Note |
|-----------|----------------|-------------|---------------------|------|
| **ISA/IEC 62443** | 95% | 3% | 2% | Sistema capability-based completo |
| **Asset Dependencies** | 90% | 5% | 5% | Confidence/source implementati |
| **Asset Review** | 95% | 5% | 0% | Notifiche automatiche mancanti |
| **Asset Ownership/Contacts** | 100% | 0% | 0% | Completo |
| **Notification System** | 98% | 2% | 0% | Completo, manca solo editor template avanzato |
| **Vulnerability Intelligence** | 80% | 15% | 5% | Sistema vulnerability-aware (auto-discovery), non vulnerability management |
| **Enterprise Auth (SSO)** | 85% | 10% | 5% | Azure AD completo, altri provider pronti ma non abilitati |
| **Asset Detail UI/UX** | 70% | 20% | 10% | Nuovo layout in test |
| **Syslog Server** | 0% | 0% | 100% | Design presente, non implementato |
| **BAS/CS** | 0% | 0% | 100% | Design presente, non implementato |

---

## 1. ISA/IEC 62443 Integration

**Design Document**: `docs/ISA62443_DESIGN.md`

### ✅ Implementato

#### Modelli Database
- ✅ `SecurityZone` - Zone di sicurezza con SL-T, SL-A, SL-C
- ✅ `Conduit` - Canali di comunicazione tra zone
- ✅ `SecurityRequirement` - Security Requirements ISA/IEC 62443
- ✅ `AssetZoneMembership` - Membership asset-zone con ruoli (Zone Participation Type)
- ✅ **Sistema Capability-based**:
  - ✅ `SecurityCapability` - 34 capability inizializzate
  - ✅ `SRCapability` - Mapping SR → Capability
  - ✅ `AssetCapability` - Evidenze esplicite
  - ✅ `SRAssessment` - Valutazione SR (sostituisce SecurityRequirementCompliance)
  - ✅ `SRAssessmentEvidence` - Evidenze per valutazione
  - ✅ `ConduitAsset` - Asset associati ai conduits

#### Servizi
- ✅ `ISA62443ComplianceEngine` - Calcolo SL-A, compliance status, gap analysis
- ✅ `ZoneRiskCalculator` - Calcolo rischio aggregato per zone
- ✅ Integrazione con `CompositeRiskScoringEngine` (penalità SL gap, non-compliance)

#### API Endpoints
- ✅ CRUD Security Zones (`/api/security-zones`)
- ✅ CRUD Conduits (`/api/conduits`)
- ✅ CRUD Zone Memberships (`/api/security-zones/{id}/memberships`)
- ✅ Compliance endpoints (`/api/compliance/zone/{zone_id}/...`)
- ✅ Capability-based assessment (`/api/compliance/zone/{zone_id}/sr/{sr_id}/assessment-assist`)

#### UI
- ✅ Pagine Security Zones Management (`SecurityZones.vue`, `SecurityZoneDetail.vue`)
- ✅ Pagine Conduits Management (`Conduits.vue`)
- ✅ Tab "IEC 62443" in Asset Detail (`AssetDetailIEC62443Tab.vue`)
- ✅ Tab "Compliance" in Security Zone Detail con 3-level review UX:
  - Level 1: Dashboard (SL-T, SL-A, GAP, SR summary)
  - Level 2: Foundation Requirements (FR) con percentuale compliance
  - Level 3: Security Requirements detail con processo capability-based guidato
- ✅ Compliance Dashboard base (`Compliance.vue`)

#### Database
- ✅ Migrazioni per tutti i modelli ISA 62443
- ✅ Migrazione capability-based
- ✅ Scripts di inizializzazione (34 Security Capabilities, SR-Capability mappings)

### 🔄 Parzialmente Implementato

- **UI per gestione AssetCapability**: Endpoint API mancante per creare/modificare evidenze esplicite
- **Inferenza capability da asset_type**: Implementata ma può essere migliorata
- **Visualizzazione evidenze in Asset Detail**: Non implementata
- **Reporting avanzato**: Gap analysis presente, export PDF/Excel mancante
- **Visualizzazione grafica Zone & Conduit**: Network map base presente, visualizzazione ISA 62443 specifica mancante

### ❌ Non Implementato

- Zone isolation violations detection automatica
- Advanced compliance reporting (PDF/Excel export)
- Security Requirements popolamento standard ISA/IEC 62443 completo
- UI per gestione manuale AssetCapability
- Visualizzazione capability in Asset Detail

---

## 2. Asset Dependencies e Risk Propagation

**Design Document**: `docs/ISA62443_DESIGN.md` (sezione Asset Dependencies)

### ✅ Implementato

#### Modello Database
- ✅ `AssetDependency` con campi:
  - `dependency_type` (operational, data, control, safety, network)
  - `criticality` (low, medium, high, critical)
  - `confidence` (low, medium, high) - **2025-01-15**
  - `source` (manual, detected, imported) - **2025-01-15**

#### Servizi
- ✅ `RiskPropagationService` - Calcolo rischio propagato (considera confidence)
- ✅ `ConnectionDependencyAnalyzer` - Analisi connessioni per suggerire dipendenze

#### API Endpoints
- ✅ CRUD Dependencies (`/api/assets/{id}/dependencies`)
- ✅ Risk Propagation (`/api/assets/{id}/risk-propagation`)
- ✅ Risk from Dependencies (`/api/assets/{id}/risk-from-dependencies`)

#### UI
- ✅ Tab "Dependencies" in Asset Detail
- ✅ Tab "Risk Propagation" in Asset Detail
- ✅ Tab "Risk" con breakdown completo (Base + Dependencies)
- ✅ Badge in Tab Connections per mostrare dipendenze esistenti
- ✅ Funzionalità "Create Dependency from Connection"

#### Integrazione Risk Scoring
- ✅ `CompositeRiskScoringEngine` aggiornato per includere:
  - Risk from dependencies (penalità per dipendenze ad alto rischio)
  - Risk propagation (come il rischio si propaga agli asset dipendenti)
- ✅ Total Risk Score = Base Risk + Risk from Dependencies (capped at 10.0)

### 🔄 Parzialmente Implementato

- **Network Map dual layer visualization**: In sviluppo
- **Ottimizzazioni performance**: Per grandi dataset

---

## 3. Asset Review e Maintenance Reminder System

**Design Document**: `docs/ISA62443_DESIGN.md` (sezione Asset Review)

### ✅ Implementato

#### Modello Database
- ✅ `AssetReview` con campi:
  - `review_type` (maintenance, security, compliance, safety)
  - `review_date`, `next_review_date`
  - `reviewer_id`, `status` (pending, completed, overdue)
  - `notes`, `findings`

#### API Endpoints
- ✅ CRUD Reviews (`/api/assets/{id}/reviews`)
- ✅ Review queries (`/api/reviews/upcoming`, `/api/reviews/overdue`)

#### UI
- ✅ Tab "Reviews" in Asset Detail
- ✅ Pagina "Asset Reviews" (`AssetReviews.vue`)
- ✅ Form per creare/modificare review

### 🔄 Parzialmente Implementato

- **Notifiche automatiche**: Modello presente, integrazione con Notification System mancante

---

## 4. Asset Ownership e Point-of-Contact

**Design Document**: `docs/ISA62443_DESIGN.md` (sezione Asset Ownership)

### ✅ Completo

- ✅ Modello `AssetContact` con campo `role` (owner, point_of_contact, other, technical, administrative)
- ✅ Relazioni many-to-many tra Asset e Contact
- ✅ API endpoints completi
- ✅ UI Tab "Contacts" in Asset Detail
- ✅ Visualizzazione owner e point-of-contact separati
- ✅ Form per aggiungere/rimuovere contatti con ruolo

---

## 5. Notification System

**Design Document**: `docs/ISA62443_DESIGN.md` (sezione Notification System)

### ✅ Implementato

#### Modelli Database
- ✅ `NotificationTemplate` - Template email con supporto override tenant-specific
- ✅ `NotificationPreference` - Preferenze utente per tipo di notifica
- ✅ `NotificationQueue` - Coda notifiche con retry logic
- ✅ `NotificationLog` - Log notifiche inviate/fallite
- ✅ `TenantSMTPConfig` - Configurazione SMTP per tenant
- ✅ **Campo `notifications_enabled` in User** - Preferenza globale per abilitare/disabilitare tutte le notifiche

#### Servizi
- ✅ `NotificationService` - Gestione notifiche e rendering template
  - ✅ Strategia multi-livello per destinatari (owner → preferenze → admin fallback)
  - ✅ Controllo preferenze globali (`notifications_enabled`)
  - ✅ Controllo preferenze specifiche con `severity_min` personalizzabile
  - ✅ Logging dettagliato per troubleshooting
- ✅ `EmailService` - Servizio email multi-provider (SMTP, SendGrid, Mailgun, AWS SES, Gmail OAuth2)
- ✅ `EmailQueueProcessor` - Processore coda email con retry automatico
- ✅ `BackgroundTaskManager` - Task automatici per processare coda e controllare review
- ✅ `AssetReviewService` - Servizio per controllare asset review e inviare notifiche

#### API Endpoints
- ✅ CRUD Notifications (`/api/notifications`)
- ✅ Notification Preferences (`/api/notifications/preferences`)
- ✅ Notification Queue (`/api/notifications/queue`)
- ✅ Notification Logs (`/api/notifications/logs`)
- ✅ Notification Templates (`/api/notifications/templates`)
- ✅ Template Override (`/api/notifications/templates/{code}/override`)
- ✅ SMTP Configuration (`/api/smtp-config`)
- ✅ SMTP Test (`/api/smtp-config/test`)
- ✅ Test Notification (`/api/notifications/test`)
- ✅ Manual Queue Processing (`/api/notifications/queue/process`)
- ✅ Manual Review Check (`/api/notifications/check-reviews`)
- ✅ **User Notification Preference** (`/api/users/me/notifications`) - Aggiorna preferenza globale

#### UI
- ✅ Pagina "Notifications" (`Notifications.vue`) con tab multipli:
  - ✅ Tab "Preferences" - Gestione preferenze per tipo di notifica
  - ✅ Tab "Queue" - Visualizzazione e gestione coda notifiche
  - ✅ Tab "Logs" - Log notifiche inviate/fallite
  - ✅ Tab "Test" - Invio email di test
  - ✅ Tab "Templates" (admin) - Editor template email
- ✅ Badge contatore notifiche non lette
- ✅ **Configurazione SMTP nella pagina Setup** (`Setup.vue`)
- ✅ Dialog configurazione SMTP con test connessione
- ✅ **Profilo Utente** - Impostazione globale `notifications_enabled` con tooltip informativo
- ✅ Editor template minimo con:
  - ✅ Supporto override tenant-specific
  - ✅ Visualizzazione template system-wide vs override
  - ✅ Editor HTML con QuillEditor
  - ✅ Gestione variabili template
  - ✅ Pulsante "Crea Override" per template system-wide
  - ✅ Pulsante "Elimina Override" per template tenant-specific

#### Background Tasks
- ✅ **Email Queue Processor**: Processa automaticamente la coda email ogni 60 secondi
- ✅ **Asset Review Checker**: Controlla asset review e invia notifiche ogni 24 ore
- ✅ Integrazione automatica con startup/shutdown dell'applicazione
- ✅ Gestione lifecycle thread con graceful shutdown

#### Funzionalità Avanzate
- ✅ **Sistema di priorità template**: Override tenant-specific > template system-wide
- ✅ **Preferenze con severity_min**: Utenti possono impostare soglia rischio personalizzata (0-10)
- ✅ **Tooltip e help text**: Guida utente per configurazione preferenze
- ✅ **Strategia destinatari intelligente**:
  1. Priorità 1: Owner asset (se hanno User associato)
  2. Priorità 2: Utenti con preferenze attive per tipo notifica
  3. Fallback: Admin tenant
- ✅ **Notifiche rischio asset**: Invio automatico quando rischio cambia significativamente
- ✅ **Logging completo**: Tracciamento dettagliato per debugging e audit

### 🔄 Parzialmente Implementato

- **Template email personalizzabili**: Editor minimo presente, editor avanzato con preview live mancante

### ❌ Non Implementato

- Notifiche push (browser notifications)
- Editor template avanzato con preview live e syntax highlighting

---

## 6. Vulnerability Intelligence

**Design Document**: `docs/VULNERABILITIES_DESIGN.md`

### 🎯 Principi Fondamentali

**Sistema "Vulnerability-Aware" (Non Vulnerability Management)**:
- Industrace è un sistema di **intelligence** che **suggerisce** vulnerabilità potenzialmente rilevanti basate sui metadati degli asset
- **NON** è un sistema di vulnerability management - non gestisce il ciclo di vita delle vulnerabilità
- **Auto-Discovery**: Il sistema suggerisce vulnerabilità candidate che devono essere verificate manualmente
- **Stato "Unreviewed" di Default**: Tutte le vulnerabilità suggerite hanno stato "unreviewed" finché non vengono esplicitamente:
  - **Acknowledged**: Confermata come applicabile
  - **Not Applicable**: Confermata come non applicabile
  - **Mitigated**: Mitigata/risolta
  - **False Positive**: Identificata come falso positivo
- **Focus**: Evidenzia vulnerabilità pubbliche potenzialmente rilevanti basate sui metadati degli asset (manufacturer, model, firmware)

### ✅ Implementato

#### Modelli Database
- ✅ `Vulnerability` - Database vulnerabilità system-wide (no tenant_id)
  - `cve_id`, `advisory_id`, `title`, `description`
  - `cvss_v3_score`, `cvss_v3_vector`, `cvss_v2_score`, `cvss_v2_vector`
  - `severity` (critical, high, medium, low)
  - `affected_manufacturers`, `affected_products`, `affected_versions` (JSONB)
  - `published_date`, `modified_date`
  - `references` (JSONB), `vendor_advisory_url`, `patch_url`
  - `source` (nvd, vendor, ics-cert, cisa), `source_url`
  - Index su `cve_id`, `severity`, `published_date`

- ✅ `AssetVulnerability` - Associazione asset-vulnerabilità (tenant-specific)
  - `asset_id`, `vulnerability_id`, `tenant_id`
  - `match_confidence` (0.0-1.0) - Confidence del matching automatico
  - `match_reason` - Ragione del match (manufacturer, model, firmware)
  - `status` (unreviewed, acknowledged, not_applicable, mitigated, false_positive)
  - `patched_date`, `patched_by`, `mitigation_notes`
  - `risk_impact` - Impatto sul risk score dell'asset
  - `detected_at`, `updated_at`
  - Index su `tenant_id`, `asset_id`, `vulnerability_id`, `status`, `detected_at`

- ✅ `VulnerabilityFeedSource` - Configurazione feed sources
  - `name`, `source_type` (nvd, vendor, ics-cert, cisa, custom)
  - `feed_url`, `feed_format` (json, xml, rss, csv), `api_key`
  - `sync_enabled`, `sync_interval_hours`
  - `last_sync_at`, `last_sync_status`, `last_sync_error`, `last_sync_count`
  - `filters` (JSONB) per manufacturer, product type, etc.
  - Supporto system-wide (`tenant_id=NULL`) e tenant-specific

#### Servizi
- ✅ `VulnerabilityMatcher` - Matching automatico vulnerabilità-asset
  - Fuzzy matching per manufacturer, model, product
  - Version matching per firmware (exact, pattern, range)
  - Calcolo `match_confidence` (manufacturer +0.4, model +0.4, firmware +0.2)
  - `match_vulnerability_to_assets()` - Match vulnerabilità → asset (tenant-wide)
  - `match_asset_to_vulnerabilities()` - Match asset → vulnerabilità
  - Threshold minimo configurabile (default: 0.6)

- ✅ `VulnerabilityFeedService` - Sync feed vulnerabilità
  - `fetch_nvd_feed()` - Fetch da NVD API v2.0 (recent, modified, all)
  - `parse_cve_json()` - Parse CVE JSON da NVD in `VulnerabilityCreate`
  - `sync_feed()` - Sincronizza feed (fetch, parse, store/update, auto-match opzionale)
  - Rate limiting per API esterne (NVD: 5 req/30s senza key, 50 req/30s con key)

- ✅ `VulnerabilityImpactCalculator` - Calcolo impatto su risk score
  - `calculate_risk_impact()` - Calcolo impatto (CVSS + criticality + exposure)
  - `update_asset_vulnerability_impact()` - Aggiorna impact per singola vulnerabilità
  - `update_all_asset_vulnerability_impacts()` - Aggiorna impact per tutte le vulnerabilità di un asset
  - Formula: `base_impact = (CVSS_score / 10.0) * 3.0` con multiplier per severity

- ✅ `VulnerabilityAutoMatch` - Auto-discovery vulnerabilità
  - Algoritmo di matching presente
  - Richiede trigger manuale (da automatizzare)

#### API Endpoints
- ✅ CRUD Vulnerabilities (`/api/vulnerabilities`)
  - `GET /api/vulnerabilities` - Lista vulnerabilità (con filtri: cve_id, severity, manufacturer)
  - `GET /api/vulnerabilities/{id}` - Dettaglio vulnerabilità
  - `POST /api/vulnerabilities` - Crea vulnerabilità (admin only)

- ✅ Asset Vulnerabilities (`/api/vulnerabilities/assets/{asset_id}`)
  - `GET /api/vulnerabilities/assets/{asset_id}` - Vulnerabilità per asset (con filtro status)
  - `POST /api/vulnerabilities/assets/{asset_id}` - Crea link asset-vulnerability
  - `PUT /api/vulnerabilities/assets/{asset_id}/vulnerabilities/{asset_vulnerability_id}` - Aggiorna status
  - `DELETE /api/vulnerabilities/assets/{asset_id}/vulnerabilities/{asset_vulnerability_id}` - Rimuovi link

- ✅ Matching (`/api/vulnerabilities/{vulnerability_id}/match-assets`)
  - `POST /api/vulnerabilities/{vulnerability_id}/match-assets` - Match vulnerabilità → asset
  - `POST /api/vulnerabilities/assets/{asset_id}/match-vulnerabilities` - Match asset → vulnerabilità (matching manuale per asset esistenti)
  - **Nota**: Matching automatico su creazione/aggiornamento asset, matching manuale disponibile per asset esistenti

- ✅ Feed Management (`/api/vulnerability-feeds`)
  - `GET /api/vulnerability-feeds` - Lista feed sources
  - `POST /api/vulnerability-feeds` - Crea feed source
  - `POST /api/vulnerability-feeds/{feed_source_id}/sync` - Sincronizza feed manualmente

- ✅ Statistics (`/api/vulnerabilities/stats`)
  - Statistiche vulnerabilità (total, by_severity, by_status, unpatched_critical/high, recent)

#### UI
- ✅ Tab "Vulnerabilities" in Asset Detail (`AssetDetailVulnerabilitiesTab.vue`)
  - ✅ Pulsante "Cerca Vulnerabilità" per matching manuale su asset esistenti
  - ✅ Indicatore progresso durante matching automatico
  - ✅ Visualizzazione confidence score e match reason
  - DataTable con vulnerabilità asset
  - Colonne: CVE ID (link NVD), Severity (Tag), CVSS Score, Status (Tag), Match Confidence
  - Pulsante "Cerca Vulnerabilità" per matching manuale (da rimuovere secondo design)
  - Paginazione (20 righe)
  - Loading states e error handling

- ✅ Pagina "Vulnerabilities" (`Vulnerabilities.vue`)
  - Lista globale vulnerabilità con filtri base

- ✅ Pagina "Vulnerability Detail" (`VulnerabilityDetail.vue`)
  - Dettaglio completo vulnerabilità

- ✅ Pagina "Vulnerability Feeds" (`VulnerabilityFeeds.vue`)
  - Gestione feed sources configurati

- ✅ Dialog Edit Vulnerability Status (`VulnerabilityEditDialog.vue`)
  - Dialog per modificare status vulnerabilità (parzialmente implementato)

#### Integrazione Risk Scoring
- ✅ Vulnerabilità considerate nel calcolo risk score (35% del peso totale)
- ✅ Breakdown vulnerabilità nel risk breakdown:
  - Critical vulnerabilities (+3)
  - High vulnerabilities (+2)
  - High CVSS score (+2)
  - Medium CVSS score (+1)
- ✅ Visualizzazione nel frontend (`RiskBreakdown.vue`)
- ✅ Impact calculation implementato e integrato

### 🔄 Parzialmente Implementato

- **Feed Integration**:
  - ✅ NVD feed completamente implementato (JSON parsing)
  - 🔄 Altri feed (ICS-CERT, CISA, vendor) non ancora implementati
  - 🔄 Auto-sync schedulato non implementato (solo sync manuale)
  - 🔄 Feed locali (upload file JSON/XML/CSV) non implementati

- **Matching Automatico**:
  - ✅ Algoritmo di matching presente e funzionante
  - ✅ Fuzzy matching base implementato (manufacturer, model, firmware)
  - 🔄 Richiede trigger manuale (da automatizzare con hook su Asset/Vulnerability create/update)
  - 🔄 Background job periodico per re-match asset esistenti mancante
  - 🔄 Potrebbe essere migliorato con librerie dedicate (rapidfuzz, fuzzywuzzy)
  - 🔄 Version matching supporta pattern base, ma non range complessi (>=x.y.z,<x.y.z)

- **Dialog Edit Vulnerability**:
  - ✅ Pulsante edit presente
  - 🔄 Dialog non completamente implementato (campi mitigation_notes, patched_date, patched_by)

- **Notifiche Intelligenti**:
  - 🔄 Notifiche per nuove vulnerabilità critiche parziali
  - 🔄 Notifiche solo per match critici non completamente implementate

### ❌ Non Implementato

- **Matching Automatico Trasparente**:
  - Hook su `Asset` create/update per trigger matching automatico in background
  - Hook su `Vulnerability` create per trigger matching automatico a tutti gli asset
  - Background job periodico per re-match asset esistenti (configurabile)
  - Configurazione matching (min_confidence, auto-match on sync) in database

- **Feed Management in Setup**:
  - Tile "Vulnerability Feeds" in `Setup.vue`
  - Pagina `VulnerabilityFeeds.vue` completa con:
    - Lista feed sources con status (enabled/disabled)
    - Form per aggiungere feed remoti (NVD, ICS-CERT, CISA, vendor) e locali
    - Sync manuale con visualizzazione progress
    - Stato sync (last sync, status, errori, count)
  - Supporto feed locali (upload file JSON/XML/CSV con parser configurabili)

- **Scheduled Sync**:
  - Background jobs per sync automatico feed (Celery/APScheduler)
  - Configurazione sync interval per feed source
  - Notifiche su sync failures
  - Retry logic per sync falliti

- **Notifiche Intelligenti Complete**:
  - Notifiche automatiche solo per match critici
  - Notifiche per vulnerabilità critiche matchate durante sync feed
  - Configurazione notifiche (notify_on_critical_match, notify_on_high_match)

- **Bulk Operations**:
  - Selezione multipla vulnerabilità
  - Bulk update status
  - Bulk matching (override automatico)

- **Export**:
  - Export vulnerabilità in CSV/JSON
  - Export report vulnerabilità per asset

### 📝 Note Design

**Differenza "Vulnerability-Aware" vs "Vulnerability Management"**:
- **Vulnerability-Aware**: Sistema di intelligence che suggerisce vulnerabilità potenzialmente rilevanti basate sui metadati degli asset. Non gestisce il ciclo di vita delle vulnerabilità, ma evidenzia solo che esistono vulnerabilità pubbliche potenzialmente rilevanti.
- **Vulnerability Management**: Sistema completo per gestire il ciclo di vita delle vulnerabilità (discovery, assessment, remediation, tracking). Industrace NON è un sistema di vulnerability management.

**Auto-Discovery vs Matching Manuale**:
- **Auto-Discovery**: Il sistema suggerisce automaticamente vulnerabilità candidate basate su matching fuzzy di manufacturer, model e firmware. Tutte le vulnerabilità suggerite hanno stato "unreviewed" di default e devono essere verificate manualmente.
- **Matching Manuale**: Attualmente presente ma da rimuovere in futuro. Il design prevede matching automatico trasparente in background quando si crea/aggiorna un asset o si sincronizza un feed.

**Stato "Unreviewed" di Default**:
- Tutte le vulnerabilità suggerite dal sistema hanno stato "unreviewed" finché non vengono esplicitamente verificate dall'utente.
- L'utente può cambiare lo stato a: acknowledged, not_applicable, mitigated, false_positive.
- Questo approccio conservativo evita falsi positivi e richiede verifica manuale.

**Focus su Suggerimenti Basati su Metadati**:
- Il sistema NON afferma che un asset ha certe vulnerabilità - suggerisce solo vulnerabilità potenzialmente rilevanti.
- Il matching è basato su metadati asset (manufacturer, model, firmware) confrontati con `affected_manufacturers`, `affected_products`, `affected_versions` delle vulnerabilità.
- La `match_confidence` indica quanto forte è il match, ma non garantisce che la vulnerabilità sia effettivamente applicabile.

---

## 7. Enterprise Authentication (SSO)

**Design Document**: `docs/ENTERPRISE_AUTH_DESIGN.md`

### ✅ Implementato

#### Modelli Database
- ✅ `TenantSSOConfig` - Configurazione SSO per tenant con supporto multi-provider
  - Campi per Azure AD, Google Workspace, Okta, Generic OIDC
  - Supporto per `authority_url`, `authorization_endpoint`, `token_endpoint`, `userinfo_endpoint`
  - `auto_provision_enabled` (default: False - Scenario 3)
  - `domain_restriction` per limitare accesso per dominio email
- ✅ Estensioni `User` per SSO:
  - `auth_provider` - Provider SSO utilizzato
  - `external_id` - ID utente nel provider esterno
  - `sso_email` - Email dal provider SSO
  - `sso_metadata` - Metadata JSON dal provider

#### Servizi
- ✅ `SSOAuthService` - OAuth2/OIDC flow completo con supporto multi-provider
  - ✅ PKCE (Proof Key for Code Exchange) per sicurezza
  - ✅ Supporto Azure AD, Google Workspace, Okta, Generic OIDC
  - ✅ Token exchange e user info retrieval
  - ✅ User provisioning e linking automatico per email match
- ✅ `SSOEncryption` - Encryption/decryption client secrets
- ✅ `AzureADService` - Integrazione Azure AD specifica
  - ✅ Client credentials flow per importazione utenti
  - ✅ Microsoft Graph API integration
  - ✅ Lista e importazione utenti Azure AD

#### API Endpoints
- ✅ SSO Configuration CRUD (`/api/auth/sso/config`)
- ✅ SSO Login Flow:
  - ✅ `GET /api/auth/sso/enabled` - Check SSO status (public endpoint)
  - ✅ `GET /api/auth/sso/{provider}/authorize` - Authorization redirect
  - ✅ `GET /api/auth/sso/callback` - OAuth callback handler
- ✅ SSO Test Connection (`/api/auth/sso/test`)
- ✅ Azure AD User Management:
  - ✅ `GET /api/auth/sso/azure-ad/users` - Lista utenti Azure AD
  - ✅ `POST /api/auth/sso/azure-ad/import` - Importazione utenti selezionati

#### UI
- ✅ Pagina "SSO Configuration" (`SSOConfig.vue`)
  - ✅ Form configurazione multi-provider (Azure AD abilitato, altri pronti)
  - ✅ Test connection con feedback dettagliato
  - ✅ Guida setup Azure AD integrata (`SSO_AZURE_AD_SETUP.md`)
  - ✅ Importazione utenti Azure AD con:
    - ✅ Tabella utenti con filtri e ricerca
    - ✅ Selezione multipla utenti
    - ✅ Selezione ruolo per utenti importati
    - ✅ Gestione errori e feedback dettagliato
- ✅ Pagina Login (`Login.vue`):
  - ✅ Rilevamento automatico SSO abilitato
  - ✅ Pulsante SSO dinamico basato su provider configurato
  - ✅ Redirect automatico al provider SSO
- ✅ Pagine Callback SSO:
  - ✅ `SSOSuccess.vue` - Gestione callback successo
  - ✅ `SSOError.vue` - Gestione errori SSO

#### Funzionalità Avanzate
- ✅ **Auto-provisioning configurabile**: Scenario 3 (disabilitato di default) - solo utenti esistenti possono accedere
- ✅ **Domain restriction**: Limitazione accesso per dominio email
- ✅ **User linking automatico**: Collegamento automatico utenti esistenti se email corrisponde
- ✅ **Client secret encryption**: Secrets criptati nel database
- ✅ **Client secret preservation**: Il secret viene preservato durante aggiornamenti se non viene fornito un nuovo valore
- ✅ **Logging dettagliato**: Tracciamento completo per troubleshooting
- ✅ **Error handling robusto**: Gestione errori con messaggi specifici

### 🔄 Parzialmente Implementato

- **Altri provider SSO**: Backend supporta già Google Workspace, Okta e Generic OIDC, ma non ancora abilitati nel frontend (design pronto per abilitazione futura)
- **Role mapping da SSO claims**: Base presente, mapping automatico da claims mancante

### ❌ Non Implementato

- "Connect" workflow semplificato per setup guidato
- JIT user provisioning completo (auto-provisioning disabilitato per design)

---

## 8. Asset Detail Page - Nuovo Layout

**Design Document**: `frontend/ASSET_DETAIL_NEW_DESIGN.md`

### ✅ Implementato

- ✅ Design document creato
- ✅ Prototipo `AssetDetailNew.vue` con layout a 4 macro-sezioni:
  - Panoramica (`AssetDetailOverviewTab.vue`)
  - Relazioni (`AssetDetailRelationsTab.vue`)
  - Sicurezza e Rischi (`AssetDetailSecurityTab.vue`)
  - Gestione (`AssetDetailManagementTab.vue`)
- ✅ Componenti base (`AssetDetailSidebar.vue`, `AssetDetailSection.vue`)
- ✅ Accessibilità (skip links, ARIA labels, keyboard navigation)
- ✅ Route alternativa `/assets-new/:id` per test

### 🔄 In Sviluppo

- Testing completo del nuovo layout
- Migrazione da layout originale a nuovo layout
- Aggiornamento link interni

---

## 9. Syslog Server e SIEM Forwarding

**Design Document**: `docs/ISA62443_DESIGN.md` (sezione Syslog Server)

### ❌ Non Implementato

- Modello database per syslog messages
- API endpoints per ricevere syslog
- Parsing e analisi syslog messages
- Forwarding a SIEM esterni
- Dashboard syslog events

**Nota**: Design completo presente, implementazione non iniziata.

---

## 10. BAS/CS™ Integration

**Design Document**: `docs/ISA62443_DESIGN.md` (sezione BAS/CS)

### ❌ Non Implementato

- Modello database per BAS/CS data
- API endpoints per integrazione BAS/CS
- Parsing BAS/CS reports
- Visualizzazione BAS/CS findings
- Integrazione con risk scoring

**Nota**: Design presente, status ON HOLD / FUTURE. Richiede syslog server completo.

---

## 📋 Priorità Implementazione

### 🔴 Alta Priorità (Gap Critici)

1. **Notification System**:
   - ✅ Configurazione SMTP (completato)
   - ✅ Preferenze globali e specifiche (completato)
   - ✅ Template editor minimo (completato)
   - ✅ Strategia invio multi-livello (completato)
   - Editor template avanzato con preview live

2. **Vulnerability Intelligence**:
   - Matching automatico trasparente (hook su Asset/Vulnerability create/update)
   - Feed management in Setup (tile in Setup.vue, pagina completa VulnerabilityFeeds.vue)
   - Supporto feed locali (upload file JSON/XML/CSV con parser configurabili)
   - Scheduled sync automatico (background jobs per sync feed)
   - Notifiche intelligenti (solo per match critici)

3. **Enterprise Auth**:
   - Integrazione completa frontend SSO login flow
   - JIT user provisioning completo

### 🟡 Media Priorità (Miglioramenti)

1. **ISA/IEC 62443**:
   - UI per gestione manuale AssetCapability
   - Visualizzazione evidenze in Asset Detail
   - Reporting avanzato (PDF/Excel export)

2. **Asset Dependencies**:
   - Network Map dual layer visualization
   - Ottimizzazioni performance

3. **Asset Detail**:
   - Migrazione completa al nuovo layout
   - Rimozione layout originale

### 🟢 Bassa Priorità (Futuro)

1. Syslog Server e SIEM Forwarding
2. BAS/CS™ Integration
3. Change Management Review completo
4. Security Requirements popolamento standard ISA/IEC 62443 completo

---

## 📝 Note Implementative

### Differenze Design vs Implementazione

1. **Security Zone - Asset Relationship**:
   - **Design originale**: Campo `security_zone_id` diretto in Asset
   - **Implementazione**: Modello `AssetZoneMembership` per supportare multiple memberships con ruoli
   - **Motivo**: Conformità IEC 62443, supporto per asset in multiple zone con ruoli diversi

2. **Risk Scoring**:
   - **Design originale**: Solo base risk score
   - **Implementazione**: Total Risk Score = Base Risk + Risk from Dependencies
   - **Motivo**: Migliore rappresentazione del rischio reale considerando dipendenze

3. **Vulnerability Matching**:
   - **Design originale**: Matching automatico completo
   - **Implementazione**: Auto-discovery con stato "unreviewed" di default
   - **Motivo**: Approccio più conservativo, richiede verifica manuale

---

## 📁 File Implementati - Riepilogo

### Backend - Modelli
- ✅ `backend/app/models/security_zone.py`
- ✅ `backend/app/models/conduit.py`
- ✅ `backend/app/models/security_requirement.py`
- ✅ `backend/app/models/asset_zone_membership.py`
- ✅ `backend/app/models/asset_dependency.py`
- ✅ `backend/app/models/asset_review.py`
- ✅ `backend/app/models/asset_contact.py`
- ✅ `backend/app/models/vulnerability.py`
- ✅ `backend/app/models/tenant_sso_config.py`
- ✅ `backend/app/models/security_capability.py`
- ✅ `backend/app/models/sr_assessment.py`
- ✅ `backend/app/models/asset_capability.py`
- ✅ `backend/app/models/notification_template.py`
- ✅ `backend/app/models/notification_preference.py`
- ✅ `backend/app/models/notification_queue.py`
- ✅ `backend/app/models/notification_log.py`
- ✅ `backend/app/models/tenant_smtp_config.py`
- ✅ `backend/app/models/user.py` (campi `notifications_enabled`, `auth_provider`, `external_id`, `sso_email`, `sso_metadata`)

### Backend - Servizi
- ✅ `backend/app/services/isa62443_compliance_engine.py`
- ✅ `backend/app/services/zone_risk_calculator.py`
- ✅ `backend/app/services/risk_propagation.py`
- ✅ `backend/app/services/connection_dependency_analyzer.py`
- ✅ `backend/app/services/vulnerability_feed.py`
- ✅ `backend/app/services/vulnerability_matcher.py`
- ✅ `backend/app/services/vulnerability_impact.py`
- ✅ `backend/app/services/vulnerability_auto_match.py`
- ✅ `backend/app/services/sso_auth.py`
- ✅ `backend/app/services/azure_ad_service.py`
- ✅ `backend/app/services/sso_encryption.py`
- ✅ `backend/app/services/notification_service.py`
- ✅ `backend/app/services/email_service.py`
- ✅ `backend/app/services/email_queue_processor.py`
- ✅ `backend/app/services/background_tasks.py`
- ✅ `backend/app/services/asset_review_service.py`

### Backend - Router/API
- ✅ `backend/app/routers/security_zones.py`
- ✅ `backend/app/routers/conduits.py`
- ✅ `backend/app/routers/compliance.py`
- ✅ `backend/app/routers/asset_dependencies.py`
- ✅ `backend/app/routers/asset_reviews.py`
- ✅ `backend/app/routers/notifications.py`
- ✅ `backend/app/routers/vulnerabilities.py`
- ✅ `backend/app/routers/sso.py`

### Frontend - Pagine
- ✅ `frontend/src/pages/SecurityZones.vue`
- ✅ `frontend/src/pages/SecurityZoneDetail.vue`
- ✅ `frontend/src/pages/Conduits.vue`
- ✅ `frontend/src/pages/Compliance.vue`
- ✅ `frontend/src/pages/AssetReviews.vue`
- ✅ `frontend/src/pages/Notifications.vue`
- ✅ `frontend/src/pages/Vulnerabilities.vue`
- ✅ `frontend/src/pages/VulnerabilityDetail.vue`
- ✅ `frontend/src/pages/VulnerabilityFeeds.vue`
- ✅ `frontend/src/pages/SSOConfig.vue`
- ✅ `frontend/src/pages/SSOSuccess.vue`
- ✅ `frontend/src/pages/SSOError.vue`
- ✅ `frontend/src/pages/AssetDetailNew.vue` (prototipo)

### Frontend - Componenti
- ✅ `frontend/src/components/features/isa62443/ZoneComplianceTab.vue`
- ✅ `frontend/src/components/features/assets/tabs/AssetDetailIEC62443Tab.vue`
- ✅ `frontend/src/components/features/assets/tabs/AssetDetailDependenciesTab.vue`
- ✅ `frontend/src/components/features/assets/tabs/AssetDetailVulnerabilitiesTab.vue`
- ✅ `frontend/src/components/features/vulnerabilities/VulnerabilityEditDialog.vue`
- ✅ `frontend/src/components/features/vulnerabilities/VulnerabilityFeedDialog.vue`
- ✅ `frontend/src/components/features/notifications/NotificationPreferencesTab.vue`
- ✅ `frontend/src/components/features/notifications/NotificationQueueTab.vue`
- ✅ `frontend/src/components/features/notifications/NotificationLogsTab.vue`
- ✅ `frontend/src/components/features/notifications/NotificationTestTab.vue`
- ✅ `frontend/src/components/features/notifications/NotificationTemplatesTab.vue`

---

## 📝 Changelog Implementazione

### 2025-12-17 - SecurityZoneDetail Ristrutturazione
- ✅ Rimosso tab "Zone Memberships" separato
- ✅ Integrata gestione memberships nel tab "Assets"
- ✅ Zone Participation Type implementato con valori predefiniti
- ✅ Dialog "Add Asset" con gestione individuale per ogni asset

### 2025-01-XX - Sistema Capability-based
- ✅ Modelli SecurityCapability, SRCapability, AssetCapability, SRAssessment implementati
- ✅ UX capability-based per valutazione SR
- ✅ Sistema evidenze (esplicite e inferite)

### 2025-01-15 - Asset Dependencies Enhancement
- ✅ Campi `confidence` e `source` aggiunti a AssetDependency
- ✅ ConnectionDependencyAnalyzer implementato
- ✅ UI visibilità incrociata Connessioni-Dipendenze

### 2025-12-22 - Notification System Completion
- ✅ Campo `notifications_enabled` aggiunto a User per preferenza globale
- ✅ Editor template minimo implementato con supporto override tenant-specific
- ✅ Strategia multi-livello per destinatari notifiche (owner → preferenze → admin)
- ✅ Preferenze con `severity_min` personalizzabile (0-10) con tooltip informativi
- ✅ Background tasks per processamento automatico coda email e controllo review
- ✅ Integrazione notifiche rischio asset con ricalcolo automatico
- ✅ Logging dettagliato per troubleshooting e audit
- ✅ UI profilo utente per gestione preferenza globale notifiche
- ✅ Migrazione database per campo `notifications_enabled`

### 2025-12-23 - Enterprise SSO (Azure AD) Completion
- ✅ Integrazione completa Azure AD SSO con OAuth2/OIDC flow
- ✅ Supporto PKCE per sicurezza avanzata
- ✅ Login SSO integrato nel frontend con rilevamento automatico provider
- ✅ Importazione utenti da Azure AD con selezione multipla e gestione ruoli
- ✅ Pagine callback SSO (success/error) con gestione token JWT
- ✅ Guida setup Azure AD completa (`SSO_AZURE_AD_SETUP.md`)
- ✅ Auto-provisioning configurabile (Scenario 3 - disabilitato di default)
- ✅ Domain restriction per limitare accesso per dominio email
- ✅ User linking automatico per email match
- ✅ Client secret encryption per sicurezza
- ✅ **Client secret preservation**: Fix per preservare secret esistente durante aggiornamenti (non si svuota più)
- ✅ Logging dettagliato e error handling robusto
- ✅ Design multi-provider: backend supporta già Google Workspace, Okta, Generic OIDC (pronti per abilitazione futura)
- ✅ Migrazione database per estensioni User SSO

### 2025-12-23 - Vulnerability Intelligence Enhancement
- ✅ Pulsante "Cerca Vulnerabilità" aggiunto in Asset Detail per matching manuale su asset esistenti
- ✅ Matching automatico funzionante su creazione/aggiornamento asset
- ✅ Matching manuale disponibile per asset esistenti creati prima dell'implementazione o senza vulnerabilità nel database
- ✅ Threshold intelligente: 0.6 default, 0.3 se solo manufacturer disponibile (no model/firmware)

---

**Documento aggiornato**: 2025-12-23  
**Prossimo aggiornamento**: Dopo completamento feature in sviluppo
