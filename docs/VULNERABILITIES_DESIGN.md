# Design - Feature Vulnerabilità (Approccio Automatico)

**Data**: 2025-01-XX  
**Versione**: 2.1  
**Status**: Design

## 🎯 Principi Fondamentali

1. **Auto-Discovery (Non Matching)**: Il sistema **suggerisce** vulnerabilità potenzialmente rilevanti basandosi sui metadati degli asset. **NON** afferma che un asset ha certe vulnerabilità - sono solo **candidate associations** che devono essere verificate manualmente.
2. **Gestione Centralizzata Feed**: Tutti i feed (remoti e locali) si configurano in Setup
3. **Background Processing**: Sync e auto-discovery avvengono in background, UI mostra risultati
4. **Notifiche Intelligenti**: Notifiche solo per eventi critici, non per ogni suggerimento
5. **Stato Unreviewed di Default**: Tutte le vulnerabilità suggerite hanno stato "unreviewed" finché non vengono esplicitamente:
   - **Acknowledged**: Confermata come applicabile
   - **Not Applicable**: Confermata come non applicabile
   - **Mitigated**: Mitigata/risolta

## 🔄 Cambiamenti Concettuali

**Terminologia** (concettuale, non necessariamente nel codice):
- `VulnerabilityMatch` → `VulnerabilityCandidate`
- `match_confidence` → `relevance_score` (concettualmente)
- `matched` → `suggested`
- `auto-match` → `auto-discovery`

**Focus**: Industrace **NON** fa vulnerability management, ma evidenzia solo che ci sono vulnerabilità pubbliche potenzialmente rilevanti basate sui metadati degli asset.

---

## 1. Gestione Feed in Setup

### 1.1 UI Setup Page

**File**: `frontend/src/pages/Setup.vue`

Aggiungere nuovo tile:

```vue
<!-- Vulnerability Feeds Tile -->
<div class="setup-tile" @click="goToVulnerabilityFeeds">
  <div class="tile-icon">
    <i class="pi pi-shield"></i>
  </div>
  <div class="tile-content">
    <h3>{{ $t('setup.strings.vulnerabilityFeeds.title') }}</h3>
    <p>{{ $t('setup.strings.vulnerabilityFeeds.description') }}</p>
  </div>
  <div class="tile-status">
    <i class="pi pi-arrow-right"></i>
  </div>
</div>
```

### 1.2 Pagina Vulnerability Feeds

**File**: `frontend/src/pages/VulnerabilityFeeds.vue`

**Layout**:
```
┌─────────────────────────────────────────────────┐
│ Vulnerability Feeds Management                  │
├─────────────────────────────────────────────────┤
│                                                 │
│ [+ Add Feed Source]                             │
│                                                 │
│ ┌───────────────────────────────────────────┐ │
│ │ Feed Sources                               │ │
│ ├───────────────────────────────────────────┤ │
│ │ [Card] NVD CVE Feed                        │ │
│ │   Status: ✅ Enabled | Last Sync: 2h ago   │ │
│ │   Type: Remote | Format: JSON             │ │
│ │   [Sync Now] [Edit] [Disable]              │ │
│ ├───────────────────────────────────────────┤ │
│ │ [Card] ICS-CERT Feed                       │ │
│ │   Status: ⚠️ Disabled                      │ │
│ │   Type: Remote | Format: RSS              │ │
│ │   [Enable] [Edit] [Delete]                  │ │
│ ├───────────────────────────────────────────┤ │
│ │ [Card] Local Feed - Vendor Advisory        │ │
│ │   Status: ✅ Enabled | Last Sync: 1d ago  │ │
│ │   Type: Local | Format: JSON               │ │
│ │   [Sync Now] [Edit] [Disable]              │ │
│ └───────────────────────────────────────────┘ │
│                                                 │
│ Statistics:                                     │
│ - Total Feeds: 3                                │
│ - Active: 2                                     │
│ - Last Sync: 2h ago                            │
└─────────────────────────────────────────────────┘
```

**Funzionalità**:
- Lista feed sources con status (enabled/disabled)
- Card per ogni feed con:
  - Nome, tipo (Remote/Local), formato
  - Status (enabled/disabled)
  - Last sync info (data, status, count, errori)
  - Azioni: Sync Now, Edit, Enable/Disable, Delete
- Pulsante "Add Feed Source" per aggiungere nuovo feed
- Statistiche globali (total feeds, active, last sync)

### 1.3 Dialog Add/Edit Feed Source

**Componente**: `VulnerabilityFeedDialog.vue`

**Form per Feed Remoto**:
```
┌─────────────────────────────────────┐
│ Add Vulnerability Feed Source       │
├─────────────────────────────────────┤
│ Feed Type: [Remote ▼]               │
│                                     │
│ Name: [NVD CVE Feed        ]        │
│                                     │
│ Source Type: [NVD ▼]                │
│   Options: NVD, ICS-CERT, CISA,     │
│            Vendor, Custom           │
│                                     │
│ Feed URL: [https://...     ]        │
│                                     │
│ Format: [JSON ▼]                    │
│   Options: JSON, XML, RSS, CSV      │
│                                     │
│ API Key (optional): [******]        │
│                                     │
│ Sync Interval: [24] hours           │
│                                     │
│ Auto-match on sync: [✓] Enabled     │
│                                     │
│ Filters (optional):                  │
│   Manufacturers: [Siemens, ...]      │
│   Product Types: [PLC, HMI, ...]    │
│                                     │
│ [Cancel] [Save]                      │
└─────────────────────────────────────┘
```

**Form per Feed Locale**:
```
┌─────────────────────────────────────┐
│ Add Local Vulnerability Feed        │
├─────────────────────────────────────┤
│ Feed Type: [Local ▼]                │
│                                     │
│ Name: [Vendor Advisory Feed]        │
│                                     │
│ Format: [JSON ▼]                    │
│   Options: JSON, XML, CSV            │
│                                     │
│ Upload File: [Choose File]          │
│   Accepted: .json, .xml, .csv       │
│                                     │
│ Parser Template: [NVD Format ▼]    │
│   Options: NVD Format, ICS-CERT,    │
│            Custom (configure)       │
│                                     │
│ Sync Interval: [24] hours           │
│   (re-process file)                 │
│                                     │
│ Auto-match on sync: [✓] Enabled     │
│                                     │
│ [Cancel] [Upload & Save]            │
└─────────────────────────────────────┘
```

**Validazione**:
- Feed remoto: URL valido, formato supportato
- Feed locale: File valido, formato corrispondente, parsing riuscito

### 1.4 API Endpoints (Nuovi/Estesi)

**Backend**: `backend/app/routers/vulnerabilities.py`

**Nuovi Endpoints**:
```python
# Upload feed locale
@router.post("/feeds/upload")
async def upload_local_feed(
    file: UploadFile,
    name: str,
    format: str,
    parser_template: str = "nvd",
    auto_match: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload e processa feed locale"""
    # 1. Valida file
    # 2. Salva file temporaneamente
    # 3. Parse secondo template
    # 4. Crea VulnerabilityFeedSource con type="local"
    # 5. Processa vulnerabilità
    # 6. Auto-match se enabled
    pass

# Sync feed con progress
@router.post("/feeds/{feed_source_id}/sync")
async def sync_feed_with_progress(
    feed_source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync feed con tracking progress (WebSocket o polling)"""
    # Background task con progress tracking
    pass

# Get sync status
@router.get("/feeds/{feed_source_id}/sync-status")
def get_sync_status(
    feed_source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current sync status and progress"""
    pass
```

**Estensioni Esistenti**:
- `POST /api/vulnerabilities/feeds` - Estendere per supportare feed locali
- `GET /api/vulnerabilities/feeds` - Aggiungere filtri e statistiche

---

## 2. Matching Automatico

### 2.1 Trigger Automatici

**Backend Hooks**:

**1. Asset Create/Update Hook**:
```python
# backend/app/models/asset.py
@event.listens_for(Asset, 'after_insert')
@event.listens_for(Asset, 'after_update')
def trigger_vulnerability_matching(mapper, connection, target):
    """Trigger matching automatico quando asset creato/aggiornato"""
    if target.manufacturer or target.model or target.firmware_version:
        # Background task per matching
        match_asset_to_vulnerabilities.delay(target.id, target.tenant_id)
```

**2. Vulnerability Create Hook**:
```python
# backend/app/models/vulnerability.py
@event.listens_for(Vulnerability, 'after_insert')
def trigger_asset_matching(mapper, connection, target):
    """Trigger matching automatico quando vulnerabilità creata"""
    # Background task per matching a tutti gli asset del tenant
    match_vulnerability_to_all_assets.delay(target.id)
```

**3. Feed Sync Hook**:
```python
# backend/app/services/vulnerability_feed.py
def sync_feed(..., auto_match: bool = True):
    """Sync feed con auto-match opzionale"""
    # ... sync vulnerabilities ...
    if auto_match:
        # Match nuove vulnerabilità a asset esistenti
        for vuln in new_vulnerabilities:
            match_vulnerability_to_assets(...)
```

### 2.2 Background Jobs

**File**: `backend/app/services/vulnerability_matching_jobs.py`

```python
from celery import Celery
from app.services.vulnerability_matcher import VulnerabilityMatcher

@celery_app.task
def match_asset_to_vulnerabilities(asset_id: uuid.UUID, tenant_id: uuid.UUID):
    """Background job per match asset → vulnerabilità"""
    with get_db() as db:
        matches = VulnerabilityMatcher.match_asset_to_vulnerabilities(
            db, asset_id, tenant_id, min_confidence=0.6
        )
        # Notifica solo se match critici
        if any(m.vulnerability.severity == 'critical' for m in matches):
            send_notification(...)

@celery_app.task
def match_vulnerability_to_all_assets(vulnerability_id: uuid.UUID):
    """Background job per match vulnerabilità → tutti asset"""
    with get_db() as db:
        # Per ogni tenant
        for tenant in get_all_tenants(db):
            matches = VulnerabilityMatcher.match_vulnerability_to_assets(
                db, vulnerability_id, tenant.id, min_confidence=0.6
            )
            # Notifica solo se match critici
            if any(m.vulnerability.severity == 'critical' for m in matches):
                send_notification(...)

@celery_app.task
def periodic_rematch_assets():
    """Periodic job per re-match asset esistenti (es. settimanale)"""
    # Re-match asset che non hanno vulnerabilità o hanno match vecchi
    pass
```

### 2.3 Configurazione Matching

**File**: `backend/app/models/vulnerability_config.py` (nuovo)

```python
class VulnerabilityMatchingConfig(Base):
    """Configurazione matching automatico"""
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    
    # Matching settings
    auto_match_on_asset_create = Column(Boolean, default=True)
    auto_match_on_asset_update = Column(Boolean, default=True)
    auto_match_on_vulnerability_create = Column(Boolean, default=True)
    auto_match_on_feed_sync = Column(Boolean, default=True)
    
    min_confidence = Column(Float, default=0.6)
    
    # Notification settings
    notify_on_critical_match = Column(Boolean, default=True)
    notify_on_high_match = Column(Boolean, default=False)
    
    # Periodic rematch
    periodic_rematch_enabled = Column(Boolean, default=True)
    periodic_rematch_interval_days = Column(Integer, default=7)
```

### 2.4 Frontend - Rimozione Matching Manuale

**File**: `frontend/src/components/features/assets/tabs/AssetDetailVulnerabilitiesTab.vue`

**Cambiamenti**:
```vue
<template>
  <div class="asset-vulnerabilities-tab">
    <!-- RIMUOVERE pulsante "Cerca Vulnerabilità" -->
    <!-- Aggiungere indicatore se matching in corso (opzionale) -->
    
    <div v-if="matchingInProgress" class="matching-indicator">
      <i class="pi pi-spin pi-spinner"></i>
      {{ t('vulnerabilities.matchingInProgress') }}
    </div>

    <DataTable ...>
      <!-- Tabella vulnerabilità -->
    </DataTable>
  </div>
</template>
```

---

## 3. Supporto Feed Locali

### 3.1 Parser Implementation

**File**: `backend/app/services/vulnerability_parsers.py` (nuovo)

```python
class VulnerabilityParser:
    """Base class per parser vulnerabilità"""
    
    @staticmethod
    def parse(file_path: str, format: str) -> List[VulnerabilityCreate]:
        """Parse file e restituisce lista VulnerabilityCreate"""
        pass

class NVDJSONParser(VulnerabilityParser):
    """Parser per NVD JSON format"""
    @staticmethod
    def parse(file_path: str) -> List[VulnerabilityCreate]:
        # Usa logica esistente da VulnerabilityFeedService.parse_cve_json
        pass

class ICS_CERTXMLParser(VulnerabilityParser):
    """Parser per ICS-CERT XML format"""
    @staticmethod
    def parse(file_path: str) -> List[VulnerabilityCreate]:
        # Parse XML ICS-CERT
        pass

class CSVParser(VulnerabilityParser):
    """Parser per CSV con mapping configurabile"""
    @staticmethod
    def parse(file_path: str, column_mapping: dict) -> List[VulnerabilityCreate]:
        # Parse CSV con mapping colonne
        pass
```

### 3.2 File Storage

**Opzioni**:
1. **Temporaneo**: File processato e poi eliminato
2. **Permanente**: File salvato per re-processing periodico

**Implementazione**:
```python
# backend/app/services/vulnerability_feed.py
def upload_local_feed(file: UploadFile, ...):
    # Salva file in storage (configurabile)
    file_path = save_uploaded_file(file, feed_source_id)
    
    # Parse file
    parser = get_parser(format, template)
    vulnerabilities = parser.parse(file_path)
    
    # Store vulnerabilities
    # ...
    
    # Se sync interval > 0, mantieni file per re-processing
    if sync_interval > 0:
        feed_source.local_file_path = file_path
    else:
        delete_file(file_path)
```

---

## 4. UI Priorità Alta (Mantiene)

### 4.1 Dialog Edit Vulnerability

**File**: `frontend/src/components/features/assets/tabs/AssetDetailVulnerabilitiesTab.vue`

**Dialog**:
```
┌─────────────────────────────────────┐
│ Edit Vulnerability Status           │
├─────────────────────────────────────┤
│ CVE: CVE-2024-12345                 │
│ Severity: Critical                  │
│                                     │
│ Status: [Patched ▼]                  │
│   Options: Unpatched, Patched,      │
│            Mitigated, False Positive│
│                                     │
│ Match Confidence: 85%                │
│ Match Reason: Manufacturer match    │
│                                     │
│ Patched Date: [2025-01-15]          │
│                                     │
│ Mitigation Notes:                   │
│ [Textarea multilinea...]            │
│                                     │
│ [Cancel] [Save]                      │
└─────────────────────────────────────┘
```

### 4.2 Pagina Vulnerabilities

**File**: `frontend/src/pages/Vulnerabilities.vue`

**Layout**: Standard DataTable con filtri avanzati

### 4.3 Vulnerability Detail Page

**File**: `frontend/src/pages/VulnerabilityDetail.vue`

**Layout**: Multi-section page con tutte le info

---

## 5. Notifiche

### 5.1 Quando Notificare

- ✅ Nuova vulnerabilità critica matchata a asset critico
- ✅ Vulnerabilità critica matchata durante sync feed
- ⚠️ Opzionale: Vulnerabilità high matchata a asset critico
- ❌ Non notificare: Match normali, match low/medium

### 5.2 Formato Notifica

```json
{
  "type": "vulnerability_critical_match",
  "title": "Critical Vulnerability Matched",
  "message": "CVE-2024-12345 matched to asset 'PLC Controller A1'",
  "severity": "critical",
  "vulnerability_id": "...",
  "asset_id": "...",
  "link": "/vulnerabilities/{id}"
}
```

---

## 6. Implementazione Step-by-Step

### Fase 1: Setup Feed Management
1. Aggiungere tile in Setup.vue
2. Creare VulnerabilityFeeds.vue
3. Implementare dialog Add/Edit Feed
4. Estendere API per feed locali

### Fase 2: Matching Automatico
1. Implementare hooks su Asset/Vulnerability
2. Creare background jobs
3. Rimuovere matching manuale da UI
4. Aggiungere configurazione matching

### Fase 3: Feed Locali
1. Implementare parser (JSON, XML, CSV)
2. Endpoint upload file
3. File storage management
4. Re-processing periodico

### Fase 4: UI Priorità Alta
1. Dialog Edit Vulnerability
2. Pagina Vulnerabilities
3. Vulnerability Detail Page

### Fase 5: Notifiche e Polish
1. Sistema notifiche intelligenti
2. Dashboard statistiche
3. Export e bulk operations

---

## 7. Considerazioni Tecniche

### Performance
- Matching in background per non bloccare UI
- Batch processing per match multipli
- Caching risultati matching

### Scalabilità
- Background jobs distribuiti (Celery)
- Queue management per sync feed
- Rate limiting per API esterne (NVD)

### Sicurezza
- Validazione file upload (size, type, content)
- Sanitizzazione input parser
- Access control su feed sources (tenant isolation)

### Monitoring
- Logging sync feed
- Tracking matching performance
- Alert su sync failures

