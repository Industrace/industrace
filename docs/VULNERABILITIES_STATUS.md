# Stato Implementazione - Feature Vulnerabilità

**Data Report**: 2025-01-XX  
**Ultimo Aggiornamento**: 2025-01-XX

## 📊 Riepilogo Generale

| Componente | ✅ Implementato | 🔄 Parziale | ❌ Non Implementato |
|------------|----------------|-------------|---------------------|
| **Backend - Modelli** | 100% | 0% | 0% |
| **Backend - API** | 90% | 10% | 0% |
| **Backend - Servizi** | 80% | 15% | 5% |
| **Frontend - UI** | 30% | 20% | 50% |
| **Integrazione Feed** | 60% | 30% | 10% |
| **Matching Automatico** | 70% | 20% | 10% |

**Stato Complessivo**: 🔄 **75% Implementato** (15% parziale, 10% non implementato)

---

## 1. Backend - Modelli Database

### ✅ Completamente Implementato

- **`Vulnerability`** (System-wide, no tenant_id)
  - ✅ `cve_id`, `advisory_id`, `title`, `description`
  - ✅ `cvss_v3_score`, `cvss_v3_vector`, `cvss_v2_score`, `cvss_v2_vector`
  - ✅ `severity` (critical, high, medium, low)
  - ✅ `affected_manufacturers`, `affected_products`, `affected_versions` (JSONB)
  - ✅ `published_date`, `modified_date`
  - ✅ `references` (JSONB), `vendor_advisory_url`, `patch_url`
  - ✅ `source` (nvd, vendor, ics-cert, cisa), `source_url`
  - ✅ Index su `cve_id`, `severity`, `published_date`

- **`AssetVulnerability`** (Tenant-specific)
  - ✅ `asset_id`, `vulnerability_id`, `tenant_id`
  - ✅ `match_confidence` (0.0-1.0), `match_reason`
  - ✅ `status` (unpatched, patched, mitigated, false_positive, not_applicable)
  - ✅ `patched_date`, `patched_by`, `mitigation_notes`
  - ✅ `risk_impact` (impatto sul risk score)
  - ✅ `detected_at`, `updated_at`
  - ✅ Index su `tenant_id`, `asset_id`, `vulnerability_id`, `status`, `detected_at`

- **`VulnerabilityFeedSource`** (Feed configuration)
  - ✅ `name`, `source_type` (nvd, vendor, ics-cert, cisa, custom)
  - ✅ `feed_url`, `feed_format` (json, xml, rss, csv), `api_key`
  - ✅ `sync_enabled`, `sync_interval_hours`
  - ✅ `last_sync_at`, `last_sync_status`, `last_sync_error`, `last_sync_count`
  - ✅ `filters` (JSONB) per manufacturer, product type, etc.
  - ✅ Supporto system-wide (`tenant_id=NULL`) e tenant-specific

---

## 2. Backend - API Endpoints

### ✅ Implementato

- **Vulnerabilities CRUD**:
  - ✅ `GET /api/vulnerabilities` - Lista vulnerabilità (con filtri: cve_id, severity, manufacturer)
  - ✅ `GET /api/vulnerabilities/{id}` - Dettaglio vulnerabilità
  - ✅ `POST /api/vulnerabilities` - Crea vulnerabilità (admin only)

- **Asset Vulnerabilities**:
  - ✅ `GET /api/vulnerabilities/assets/{asset_id}` - Vulnerabilità per asset (con filtro status)
  - ✅ `POST /api/vulnerabilities/assets/{asset_id}` - Crea link asset-vulnerability
  - ✅ `PUT /api/vulnerabilities/assets/{asset_id}/vulnerabilities/{asset_vulnerability_id}` - Aggiorna status
  - ✅ `DELETE /api/vulnerabilities/assets/{asset_id}/vulnerabilities/{asset_vulnerability_id}` - Rimuovi link

- **Matching**:
  - ✅ `POST /api/vulnerabilities/{vulnerability_id}/match-assets` - Match vulnerabilità → asset
  - ✅ `POST /api/vulnerabilities/assets/{asset_id}/match-vulnerabilities` - Match asset → vulnerabilità

- **Feed Sources**:
  - ✅ `GET /api/vulnerabilities/feeds` - Lista feed sources
  - ✅ `POST /api/vulnerabilities/feeds` - Crea feed source
  - ✅ `POST /api/vulnerabilities/feeds/{feed_source_id}/sync` - Sincronizza feed manualmente

- **Statistics**:
  - ✅ `GET /api/vulnerabilities/stats` - Statistiche vulnerabilità (total, by_severity, by_status, unpatched_critical/high, recent)

### 🔄 Parzialmente Implementato

- **Paginazione**: ✅ Presente ma potrebbe essere migliorata (skip/limit)
- **Filtri Avanzati**: ✅ Base implementata, mancano filtri complessi (date range, CVSS range, etc.)

### ❌ Non Implementato

- **Bulk Operations**: Aggiornamento status multipli, bulk matching
- **Export**: Export vulnerabilità in CSV/JSON
- **Notifications**: Endpoint per notifiche vulnerabilità critiche

---

## 3. Backend - Servizi

### ✅ Implementato

- **`VulnerabilityMatcher`** (`backend/app/services/vulnerability_matcher.py`)
  - ✅ `_fuzzy_match_string()` - Fuzzy matching per stringhe
  - ✅ `_fuzzy_match_list()` - Match in liste
  - ✅ `_check_version_match()` - Version matching (exact, pattern, range)
  - ✅ `calculate_match_confidence()` - Calcolo confidence (manufacturer +0.4, model +0.4, firmware +0.2)
  - ✅ `match_vulnerability_to_assets()` - Match vulnerabilità → asset (tenant-wide)
  - ✅ `match_asset_to_vulnerabilities()` - Match asset → vulnerabilità

- **`VulnerabilityFeedService`** (`backend/app/services/vulnerability_feed.py`)
  - ✅ `fetch_nvd_feed()` - Fetch da NVD API v2.0 (recent, modified, all)
  - ✅ `parse_cve_json()` - Parse CVE JSON da NVD in `VulnerabilityCreate`
  - ✅ `sync_feed()` - Sincronizza feed (fetch, parse, store/update, auto-match opzionale)

- **`VulnerabilityImpactCalculator`** (`backend/app/services/vulnerability_impact.py`)
  - ✅ `calculate_risk_impact()` - Calcolo impatto su risk score (CVSS + criticality + exposure)
  - ✅ `update_asset_vulnerability_impact()` - Aggiorna impact per singola vulnerabilità
  - ✅ `update_all_asset_vulnerability_impacts()` - Aggiorna impact per tutte le vulnerabilità di un asset

### 🔄 Parzialmente Implementato

- **Matching Algorithm**:
  - ✅ Fuzzy matching base implementato
  - 🔄 Potrebbe essere migliorato con librerie dedicate (rapidfuzz, fuzzywuzzy)
  - 🔄 Version matching supporta pattern base, ma non range complessi (>=x.y.z,<x.y.z)

- **Feed Integration**:
  - ✅ NVD feed completamente implementato
  - 🔄 Altri feed (ICS-CERT, CISA, vendor) non ancora implementati
  - 🔄 Auto-sync schedulato non implementato (solo manuale)

### ❌ Non Implementato

- **Scheduled Sync**: Background job per sync automatico feed
- **Feed Parsers**: Parser per feed XML, RSS, CSV (solo JSON NVD attualmente)
- **Notification Service**: Servizio per notifiche vulnerabilità critiche

---

## 4. Frontend - UI

### ✅ Implementato

- **Tab Vulnerabilities in Asset Detail** (`frontend/src/components/features/assets/tabs/AssetDetailVulnerabilitiesTab.vue`)
  - ✅ DataTable con vulnerabilità asset
  - ✅ Colonne: CVE ID (link NVD), Severity (Tag), CVSS Score, Status (Tag), Match Confidence
  - ✅ Pulsante "Cerca Vulnerabilità" per matching automatico
  - ✅ Paginazione (20 righe)
  - ✅ Loading states
  - ✅ Error handling

### 🔄 Parzialmente Implementato

- **Edit Dialog**: 
  - ✅ Pulsante edit presente
  - ❌ Dialog non implementato (TODO nel codice)

### ❌ Non Implementato

- **Pagina Vulnerabilities Dedicata**:
  - ❌ Lista globale vulnerabilità (`/vulnerabilities`)
  - ❌ Filtri avanzati (severity, date range, manufacturer, CVSS range)
  - ❌ Visualizzazione dettaglio vulnerabilità
  - ❌ Dashboard statistiche vulnerabilità

- **Dialog Edit Vulnerability**:
  - ❌ Dialog per modificare status (unpatched → patched/mitigated/false_positive)
  - ❌ Campo `mitigation_notes`
  - ❌ Campo `patched_date`, `patched_by`
  - ❌ Visualizzazione `match_reason`

- **Vulnerability Detail View**:
  - ❌ Pagina dettaglio vulnerabilità con:
    - Descrizione completa
    - CVSS vector breakdown
    - Affected products/manufacturers
    - References
    - Lista asset affetti
    - Timeline (published, modified)

- **Dashboard Vulnerabilities**:
  - ❌ Dashboard con:
    - Statistiche globali (total, by severity, by status)
    - Grafici (severity distribution, status distribution, timeline)
    - Top vulnerabilità critiche
    - Asset più vulnerabili

- **Bulk Operations UI**:
  - ❌ Selezione multipla vulnerabilità
  - ❌ Bulk update status
  - ❌ Bulk matching

---

## 5. Integrazione con Risk Scoring

### ✅ Implementato

- **Risk Scoring Engine** (`backend/app/services/risk_scoring.py`)
  - ✅ Vulnerabilità considerate nel calcolo risk score (35% del peso)
  - ✅ Breakdown vulnerabilità nel risk breakdown:
    - Critical vulnerabilities (+3)
    - High vulnerabilities (+2)
    - High CVSS score (+2)
    - Medium CVSS score (+1)
  - ✅ Visualizzazione nel frontend (`RiskBreakdown.vue`)

### 🔄 Parzialmente Implementato

- **Impact Calculation**:
  - ✅ `VulnerabilityImpactCalculator` implementato
  - 🔄 Impact non sempre aggiornato automaticamente quando cambia status
  - 🔄 Impact non sempre considerato nel risk score finale

---

## 6. Traduzioni

### ✅ Implementato

- **File Traduzioni**:
  - ✅ `frontend/src/locales/it/vulnerabilities.json` (base)
  - ✅ `frontend/src/locales/en/vulnerabilities.json` (presumibilmente presente)

- **Chiavi Base**:
  - ✅ `title`, `noVulnerabilities`, `cveId`, `severity`, `cvssScore`, `status`
  - ✅ `matchConfidence`, `matchVulnerabilities`, `matchSuccess`
  - ✅ `errorLoading`, `errorMatching`
  - ✅ `statuses.unpatched`, `statuses.patched`, `statuses.mitigated`, `statuses.falsePositive`

### ❌ Non Implementato

- **Chiavi Mancanti** (per UI completa):
  - ❌ `editVulnerability`, `updateStatus`, `mitigationNotes`, `patchedDate`
  - ❌ `vulnerabilityDetail`, `affectedAssets`, `references`, `description`
  - ❌ `dashboard`, `statistics`, `filters`, `export`
  - ❌ `bulkUpdate`, `bulkMatch`, `confirmDelete`

---

## 7. Nuovo Design - Requisiti Aggiornati

### 🎯 Cambiamenti Concettuali

**1. Gestione Feed nella Zona Setup** (NUOVO)
- ✅ Aggiungere tile "Vulnerability Feeds" in `Setup.vue`
- ✅ Creare pagina `VulnerabilityFeeds.vue` per gestione feed sources
- ✅ Supporto per:
  - Feed remoti (NVD, ICS-CERT, CISA, vendor) - configurazione URL/API key
  - Feed locali - upload file (JSON, XML, CSV)
  - Abilitazione/disabilitazione feed
  - Configurazione sync interval
  - Visualizzazione stato sync (last sync, status, count)

**2. Matching Automatico** (NUOVO - Cambio Paradigma)
- ❌ **RIMUOVERE** pulsante "Cerca Vulnerabilità" manuale dall'asset
- ✅ **IMPLEMENTARE** matching automatico in background quando:
  - Si sincronizza un feed (auto-match opzionale/configurabile)
  - Si crea/aggiorna un asset (se ha manufacturer/model/firmware)
  - Si aggiunge una nuova vulnerabilità al database
  - Background job periodico per re-match asset esistenti
- ✅ Matching silenzioso in background, notifiche solo per match critici

**3. UI Priorità Alta** (Mantiene ma con nuovo contesto)
- Dialog Edit Vulnerability (status, mitigation notes, patched date)
- Pagina Vulnerabilities dedicata (lista globale con filtri)
- Vulnerability Detail Page (dettaglio completo)

---

## 8. Cosa Manca / Da Fare (Aggiornato)

### 🔴 Priorità Alta

1. **Gestione Feed in Setup** (`frontend/src/pages/VulnerabilityFeeds.vue`)
   - Lista feed sources configurati
   - Form per aggiungere feed:
     - Tipo: Remoto (NVD, ICS-CERT, CISA, Vendor) o Locale (Upload file)
     - Per feed remoti: URL, API key, sync interval
     - Per feed locali: Upload file (JSON/XML/CSV), parser selection
   - Abilitazione/disabilitazione feed
   - Sync manuale con visualizzazione progress
   - Stato sync (last sync, status, errori, count)
   - Filtri per feed (manufacturer, product type)

2. **Matching Automatico** (Backend + Frontend)
   - **Backend**:
     - Hook su `Asset` create/update per trigger matching automatico
     - Hook su `Vulnerability` create per trigger matching automatico
     - Background job per re-match periodico (configurabile)
     - Configurazione matching (min_confidence, auto-match on sync)
   - **Frontend**:
     - Rimuovere pulsante "Cerca Vulnerabilità" da `AssetDetailVulnerabilitiesTab.vue`
     - Aggiungere indicatore "Matching in corso..." se necessario
     - Notifiche toast per match critici trovati

3. **Supporto Feed Locali** (Backend)
   - Endpoint `POST /api/vulnerabilities/feeds/upload` per upload file
   - Parser per JSON (NVD format, custom format)
   - Parser per XML (ICS-CERT format)
   - Parser per CSV (custom format con mapping configurabile)
   - Validazione formato file
   - Storage file temporaneo o permanente

4. **Dialog Edit Vulnerability** (`AssetDetailVulnerabilitiesTab.vue`)
   - Implementare dialog per modificare status vulnerabilità
   - Campi: status (dropdown), mitigation_notes (textarea), patched_date (date picker)
   - Visualizzazione `match_reason` (read-only)
   - Salvataggio via API `PUT /api/vulnerabilities/assets/{asset_id}/vulnerabilities/{asset_vulnerability_id}`

5. **Pagina Vulnerabilities Dedicata** (`frontend/src/pages/Vulnerabilities.vue`)
   - Lista globale vulnerabilità con filtri avanzati
   - DataTable con colonne: CVE ID, Title, Severity, CVSS Score, Published Date, Affected Assets
   - Filtri: severity, date range, manufacturer, CVSS range, source
   - Link a dettaglio vulnerabilità

6. **Vulnerability Detail Page** (`frontend/src/pages/VulnerabilityDetail.vue`)
   - Dettaglio completo vulnerabilità
   - Sezioni: Info base, Description, CVSS Breakdown, Affected Products, References, Affected Assets
   - Azioni: Manual Match to Assets (opzionale, per override), Export

### 🟡 Priorità Media

7. **Dashboard Vulnerabilities** (`frontend/src/pages/VulnerabilitiesDashboard.vue`)
   - Statistiche globali (cards)
   - Grafici (severity distribution, status distribution, timeline)
   - Top vulnerabilità critiche
   - Asset più vulnerabili
   - Feed sync status overview

8. **Miglioramenti Matching**
   - Integrare libreria rapidfuzz per fuzzy matching più accurato
   - Migliorare version matching (range complessi)
   - Aggiungere matching basato su CPE (Common Platform Enumeration)
   - Machine learning per migliorare confidence scores

9. **Scheduled Sync** (Background Jobs)
   - Background job per sync automatico feed (Celery/APScheduler)
   - Configurazione sync interval per feed source
   - Notifiche su sync failures
   - Retry logic per sync falliti

10. **Feed Integration Estesa**
    - Supporto completo per ICS-CERT RSS feed
    - Supporto completo per CISA JSON/CSV feeds
    - Supporto per vendor-specific feeds (Siemens, Schneider, etc.)
    - Template parser configurabili per feed custom

### 🟢 Priorità Bassa

11. **Bulk Operations**
    - UI per selezione multipla vulnerabilità
    - Bulk update status
    - Bulk manual matching (override automatico)

12. **Export**
    - Export vulnerabilità in CSV/JSON
    - Export report vulnerabilità per asset
    - Export feed configuration

13. **Notifications Avanzate**
    - Notifiche automatiche per nuove vulnerabilità critiche
    - Notifiche per vulnerabilità che matchano asset critici
    - Email notifications configurabili
    - Webhook notifications per integrazioni esterne

14. **Advanced Features**
    - Vulnerability remediation tracking
    - Vulnerability lifecycle management
    - Integration con patch management systems
    - Vulnerability scanning integration
    - Compliance mapping (vulnerabilità → Security Requirements)

---

## 8. Note Tecniche

### Matching Algorithm

Il matching attuale usa:
- **Manufacturer matching**: Fuzzy match (0.0-1.0) → +0.4 al confidence
- **Model/Product matching**: Fuzzy match (0.0-1.0) → +0.4 al confidence
- **Firmware version matching**: Exact/pattern/range → +0.2 al confidence
- **Threshold minimo**: 0.6 (configurabile)

**Miglioramenti Possibili**:
- Usare libreria `rapidfuzz` per fuzzy matching più accurato
- Aggiungere matching basato su CPE
- Considerare asset type nel matching
- Machine learning per migliorare confidence

### Feed Integration

**NVD API v2.0**:
- Rate limit: 5 requests per 30 secondi (senza API key)
- Con API key: 50 requests per 30 secondi
- Supporta: recent (last 8 days), modified (last 8 days), all

**Altri Feed**:
- ICS-CERT: RSS feed disponibile
- CISA: JSON/CSV feeds disponibili
- Vendor-specific: Varia per vendor

### Risk Impact Calculation

Formula attuale:
```
base_impact = (CVSS_score / 10.0) * 3.0
multiplier = 1.0 (base)
  - critical: 1.5
  - high: 1.2
  - medium: 1.0
  - low: 0.8
  - exposure_high: *1.3
  - exposure_medium: *1.1
risk_impact = base_impact * multiplier
```

---

## 9. File Chiave

### Backend
- `backend/app/models/vulnerability.py` - Modelli database
- `backend/app/routers/vulnerabilities.py` - API endpoints
- `backend/app/crud/vulnerabilities.py` - CRUD operations
- `backend/app/services/vulnerability_matcher.py` - Matching algorithm
- `backend/app/services/vulnerability_feed.py` - Feed integration
- `backend/app/services/vulnerability_impact.py` - Impact calculation
- `backend/app/schemas/vulnerability.py` - Pydantic schemas

### Frontend
- `frontend/src/components/features/assets/tabs/AssetDetailVulnerabilitiesTab.vue` - Tab vulnerabilità asset
- `frontend/src/locales/it/vulnerabilities.json` - Traduzioni italiano
- `frontend/src/locales/en/vulnerabilities.json` - Traduzioni inglese

### Database
- `backend/alembic/versions/*_create_vulnerability*.py` - Migrazione database (presumibilmente)

---

## 10. Nuovo Flusso Proposto

### Setup Iniziale
1. Admin va in **Setup → Vulnerability Feeds**
2. Configura feed desiderati:
   - NVD (remoto) - URL, API key opzionale
   - ICS-CERT (remoto) - URL RSS
   - Feed locale - Upload file JSON/XML/CSV
3. Abilita feed e configura sync interval
4. Sistema inizia sync automatico in background

### Operazione Normale
1. **Feed Sync Automatico** (background job):
   - Fetch feed configurati secondo interval
   - Parse e store vulnerabilità
   - **Auto-match** con asset esistenti (se configurato)
   - Notifica solo per match critici

2. **Asset Create/Update**:
   - Quando si crea/aggiorna asset con manufacturer/model/firmware
   - Sistema fa **matching automatico** in background
   - Nessun intervento utente necessario

3. **Visualizzazione**:
   - Tab Vulnerabilities nell'asset mostra vulnerabilità trovate automaticamente
   - Pagina Vulnerabilities globale per overview
   - Detail page per drill-down

### Matching Manuale (Opzionale)
- Disponibile solo per override/correzione
- Non è il flusso principale

---

## 11. Conclusioni

La feature vulnerabilità è **ben strutturata a livello backend** con modelli solidi, API complete e servizi funzionanti. Il **matching automatico** esiste ma attualmente richiede azione manuale.

**Cambiamento Paradigma**: Passare da matching manuale a matching automatico trasparente, con gestione feed centralizzata in Setup.

**Prossimi Step Prioritari**:
1. **Gestione Feed in Setup** - UI per configurare feed (remoti + locali)
2. **Matching Automatico** - Rimuovere azione manuale, implementare hook automatici
3. **Supporto Feed Locali** - Upload e parsing file locali
4. **Dialog Edit** - Completare UI per gestione status vulnerabilità
5. **Pagine Dedicata** - Lista e detail vulnerabilità

**Architettura Proposta**:
- Setup centralizzato per feed configuration
- Background jobs per sync e matching automatico
- UI reattiva che mostra risultati senza richiedere azioni manuali
- Notifiche solo per eventi critici

