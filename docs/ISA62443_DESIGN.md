# ISA/IEC 62443 Integration - Design Document

## ⚠️ Note di Revisione

**Revisione 2025-12-05**: Questo documento è stato rivisto e aggiornato per:
- ✅ Correggere riferimenti a Security Levels (1-4 invece di 0-4, conforme allo standard ISA/IEC 62443)
- ✅ Aggiornare i modelli dati per riflettere l'implementazione reale (campi aggiuntivi implementati)
- ✅ Documentare lo stato attuale dell'implementazione (molte funzionalità sono già implementate)
- ✅ Migliorare la descrizione dei servizi con dettagli sulla logica implementata
- ✅ Aggiungere note su campi aggiuntivi presenti nell'implementazione ma non nel design originale

**Revisione 2025-01-XX**: Aggiornamenti recenti:
- ✅ Fix conteggio asset nelle security zones (ora usa AssetZoneMembership invece di Asset.security_zone_id)
- ✅ Fix calcolo GAP nella compliance tab (corretto controllo null/undefined, distinzione tra 0 e null)
- ✅ Implementata 3-level Compliance Review UX (Dashboard → FR → SR detail)
- ✅ Ricalcolo automatico SL-A dopo aggiornamento compliance status
- ✅ Aggiunte chiavi di traduzione mancanti (flowJustification, ownership, common.search)
- ✅ **Sistema Capability-based per SR Assessment (2025-01-XX)** - **NUOVO**
  - ✅ Modelli: SecurityCapability, SRCapability, AssetCapability, SRAssessment, SRAssessmentEvidence, ConduitAsset
  - ✅ UX guidata per valutazione SR basata su capability richieste e evidenze disponibili
  - ✅ Sistema evidenze: esplicite (dichiarate manualmente) vs inferite (da asset_type)
  - ✅ SRAssessment sostituisce SecurityRequirementCompliance per valutazioni zona/conduit

**Stato Implementazione**: 
- ✅ Modelli base implementati (SecurityZone, Conduit, SecurityRequirement, SecurityRequirementCompliance)
- ✅ Servizio ISA62443ComplianceEngine implementato con logica completa
- ✅ API CRUD per Security Zones e Conduits
- ✅ UI base per gestione Security Zones e Conduits
- 🔄 Integrazione con Risk Scoring parzialmente implementata

## Overview

Questo documento descrive l'integrazione dello standard ISA/IEC 62443 in Industrace per supportare la gestione della sicurezza dei sistemi di controllo industriale (IACS).

**Nota sullo stato dell'implementazione**: Questo documento descrive il design dell'implementazione ISA/IEC 62443. Molte funzionalità sono già state implementate (SecurityZone, Conduit, ISA62443ComplianceEngine). Il documento è stato aggiornato per riflettere lo stato attuale dell'implementazione.

## Obiettivi

1. **Security Zones Management**: Gestione delle zone di sicurezza secondo ISA/IEC 62443
2. **Conduits Management**: Gestione dei canali di comunicazione tra zone
3. **Security Level Assessment**: Calcolo automatico dei Security Levels (SL-T, SL-A, SL-C)
4. **Compliance Tracking**: Tracciamento della conformità ai Security Requirements (SR)
5. **Gap Analysis**: Analisi delle differenze tra Security Level Target e Achieved
6. **Integration with Existing Risk Scoring**: Integrazione con il sistema di risk assessment esistente

## Architettura

### Relazione con Modelli Esistenti

```
Site (Impianto)
├── Area (Area operativa) - già presente
│   └── Location (Location fisica) - già presente
│       └── Asset (Asset) - già presente
│           ├── location_id (fisica) ✅
│           ├── area_id (fisica) ✅
│           ├── purdue_level (0.0-5.0) ✅
│           └── security_zone_id (logica) ⬅️ NUOVO
│
└── SecurityZone (Zona di sicurezza logica) ⬅️ NUOVO
    ├── mapped_locations (many-to-many, opzionale)
    └── mapped_areas (many-to-many, opzionale)
```

### Differenza Concettuale

- **Location/Area**: Posizione fisica dell'asset (dove si trova)
- **Security Zone**: Raggruppamento logico per sicurezza (requisiti di sicurezza simili)

**Esempio pratico:**
- Location fisica: "Control Room"
  - Asset A: Security Zone "DMZ" (SL-2)
  - Asset B: Security Zone "Process Control" (SL-3)

## Modelli Dati

### 1. SecurityZone

**Nota**: Il modello è già implementato in `backend/app/models/security_zone.py` con campi aggiuntivi rispetto a questa descrizione.

```python
class SecurityZone(Base):
    __tablename__ = "security_zones"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    site_id = Column(UUID, ForeignKey("sites.id"), nullable=True)  # Opzionale: zona può estendersi su più site
    
    # Identificazione
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    zone_type = Column(String(50), nullable=True)  # 'process', 'safety', 'control', 'enterprise', 'dmz', etc.
    
    # ISA/IEC 62443 Security Levels
    # Nota: ISA/IEC 62443 definisce Security Levels da 1 a 4 (non 0-4)
    security_level_target = Column(Integer, nullable=True)  # SL-T: 1-4 (Target Security Level)
    security_level_achieved = Column(Integer, nullable=True)  # SL-A: 1-4 (Achieved Security Level, calcolato)
    security_level_capability = Column(Integer, nullable=True)  # SL-C: 1-4 (Capability Security Level)
    
    # Proprietà della Zona
    is_dmz = Column(Boolean, default=False)  # È una zona DMZ?
    is_air_gapped = Column(Boolean, default=False)  # La zona è air-gapped (isolata)?
    network_segment = Column(String(100), nullable=True)  # Segmento di rete/VLAN
    
    # Compliance
    compliance_status = Column(String(20), default="not_assessed")  # 'not_assessed', 'compliant', 'non_compliant', 'partial'
    last_assessment_date = Column(DateTime, nullable=True)
    next_assessment_date = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)  # soft delete
    
    # Relationships
    assets = relationship("Asset", back_populates="security_zone")
    conduits_from = relationship("Conduit", foreign_keys="Conduit.from_zone_id", back_populates="from_zone")
    conduits_to = relationship("Conduit", foreign_keys="Conduit.to_zone_id", back_populates="to_zone")
    locations = relationship("Location", secondary=security_zone_locations, backref="security_zones")  # Mapping opzionale a Locations
    compliance_records = relationship("SecurityRequirementCompliance", back_populates="zone")
```

**Campi aggiuntivi implementati** (non nel design originale):
- `security_level_capability`: Security Level Capability (SL-C)
- `is_dmz`, `is_air_gapped`, `network_segment`: Proprietà di sicurezza della zona
- `compliance_status`, `last_assessment_date`, `next_assessment_date`: Tracking compliance

### 2. Conduit

**Nota**: Il modello è già implementato in `backend/app/models/conduit.py` con campi aggiuntivi rispetto a questa descrizione.

```python
class Conduit(Base):
    __tablename__ = "conduits"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    
    # Zone di origine e destinazione
    from_zone_id = Column(UUID, ForeignKey("security_zones.id"), nullable=False)
    to_zone_id = Column(UUID, ForeignKey("security_zones.id"), nullable=False)
    
    # Identificazione
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    conduit_type = Column(String(50), nullable=True)  # 'network', 'serial', 'wireless', 'vpn', etc.
    
    # Proprietà di Sicurezza
    is_encrypted = Column(Boolean, default=False)
    encryption_type = Column(String(50), nullable=True)  # 'tls', 'ipsec', 'proprietary', etc.
    authentication_required = Column(Boolean, default=True)
    authentication_method = Column(String(50), nullable=True)  # 'certificate', 'psk', 'username_password', etc.
    
    # Dettagli di Rete
    protocol = Column(String(50), nullable=True)  # 'tcp', 'udp', 'modbus', 'opcua', etc.
    port_range = Column(String(100), nullable=True)  # '502', '502-510', etc.
    allowed_direction = Column(String(50), default="bidirectional")  # 'unidirectional', 'bidirectional', 'request_response'
    
    # Governance
    flow_justification = Column(Text, nullable=True)  # Motivazione del flusso (principio "least privilege")
    ownership = Column(String(255), nullable=True)  # Chi è responsabile della manutenzione
    
    # ISA/IEC 62443 Security Levels
    security_level_target = Column(Integer, nullable=True)  # SL-T: 1-4 (Target Security Level)
    security_level_achieved = Column(Integer, nullable=True)  # SL-A: 1-4 (Achieved Security Level, calcolato)
    
    # Compliance
    compliance_status = Column(String(20), default="not_assessed")
    last_assessment_date = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    from_zone = relationship("SecurityZone", foreign_keys=[from_zone_id], back_populates="conduits_from")
    to_zone = relationship("SecurityZone", foreign_keys=[to_zone_id], back_populates="conduits_to")
    compliance_records = relationship("SecurityRequirementCompliance", back_populates="conduit")
```

**Campi aggiuntivi implementati** (non nel design originale):
- Proprietà di sicurezza: `is_encrypted`, `encryption_type`, `authentication_required`, `authentication_method`
- Dettagli di rete: `protocol`, `port_range`, `allowed_direction`
- Governance: `flow_justification`, `ownership`
- Compliance tracking: `compliance_status`, `last_assessment_date`

### 3. SecurityRequirement

**Nota**: Il modello è già implementato in `backend/app/models/security_requirement.py`.

```python
class SecurityRequirement(Base):
    __tablename__ = "security_requirements"
    
    id = Column(UUID, primary_key=True)
    # Nota: SecurityRequirement è system-wide (no tenant_id) - dati di riferimento standard
    
    # Identificazione SR (es: "SR 1.1", "FR 1.1", "CR 1.1")
    requirement_id = Column(String(50), unique=True, nullable=False)  # "SR 1.1"
    requirement_category = Column(String(50), nullable=True)  # 'SR', 'FR', 'CR' (Security, Foundational, Component)
    
    # Dettagli Requisito
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    requirement_text = Column(Text, nullable=True)  # Testo completo del requisito dallo standard
    
    # Applicabilità
    applies_to_zones = Column(Boolean, default=True)  # Si applica a Security Zones
    applies_to_conduits = Column(Boolean, default=True)  # Si applica a Conduits
    applies_to_assets = Column(Boolean, default=False)  # Si applica a singoli Asset
    
    # Security Level Range
    min_security_level = Column(Integer, nullable=True)  # SL minimo richiesto (1-4)
    max_security_level = Column(Integer, nullable=True)  # SL massimo applicabile (1-4, NULL = tutti)
    
    # Metadata Standard
    standard_version = Column(String(20), nullable=True)  # es: "62443-3-3:2013"
    section_reference = Column(String(100), nullable=True)  # Riferimento sezione nello standard
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    compliance_records = relationship("SecurityRequirementCompliance", back_populates="requirement")
```

**Differenze rispetto al design originale**:
- Usa `min_security_level` e `max_security_level` invece di `applies_to_sl` (JSONB)
- Aggiunge flag `applies_to_zones`, `applies_to_conduits`, `applies_to_assets` per specificare applicabilità
- Aggiunge `requirement_text` per testo completo del requisito
- Aggiunge `standard_version` e `section_reference` per tracciabilità standard

### 4. SecurityRequirementCompliance (DEPRECATO)

**Nota (2025-01-XX)**: Questo modello è stato sostituito dal sistema capability-based. Viene mantenuto per retrocompatibilità ma le nuove valutazioni usano `SRAssessment`.

```python
class SecurityRequirementCompliance(Base):
    __tablename__ = "security_requirement_compliance"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"))
    
    # Riferimento
    requirement_id = Column(UUID, ForeignKey("security_requirements.id"))
    zone_id = Column(UUID, ForeignKey("security_zones.id"), nullable=True)
    asset_id = Column(UUID, ForeignKey("assets.id"), nullable=True)
    conduit_id = Column(UUID, ForeignKey("conduits.id"), nullable=True)
    
    # Compliance
    compliance_status = Column(String(20))  # compliant, non-compliant, partial, n/a
    evidence = Column(Text)  # Documentazione/evidenza
    notes = Column(Text)
    
    # Assessment
    assessed_by = Column(UUID, ForeignKey("users.id"))
    assessed_at = Column(DateTime)
    next_assessment = Column(DateTime)
```

**Sostituito da**: `SRAssessment` (vedi sezione "Sistema Capability-based per SR Assessment")

### 5. Estensioni al Modello Asset

```python
# Aggiunte al modello Asset esistente
class Asset(Base):
    # ... campi esistenti ...
    
    # ISA/IEC 62443
    security_zone_id = Column(UUID, ForeignKey("security_zones.id"), nullable=True, index=True)
    # DEPRECATED: Mantenuto per retrocompatibilità. Usare zone_memberships per supportare multiple zone con ruoli diversi.
    
    security_level_target = Column(Integer, nullable=True)  # SL-T: 1-4 (opzionale, può ereditare dalla zona)
    security_level_achieved = Column(Integer, nullable=True)  # SL-A: 1-4 (calcolato)
    isa62443_compliance_status = Column(String(20), nullable=True)  # 'compliant', 'non_compliant', 'partial', 'not_assessed'
    isa62443_last_assessment = Column(DateTime, nullable=True)
    
    # Relationships
    security_zone = relationship("SecurityZone", back_populates="assets", foreign_keys=[security_zone_id])
    zone_memberships = relationship("AssetZoneMembership", back_populates="asset", cascade="all, delete-orphan")
```

### 6. AssetZoneMembership (Zone Membership con Ruoli)

**Nota (2025-01-XX)**: Introdotto il concetto di **Zone Membership con Ruoli** per permettere a un asset di appartenere a più Security Zones con ruoli diversi. Questo è conforme a ISA/IEC 62443 dove un asset può avere interfacce diverse che appartengono a zone diverse.

**Esempio reale**:
- **HMI-01** in **Control Zone** con ruolo `operator_interface`
- **HMI-01** in **DMZ** con ruolo `data_publisher`

Stesso asset, due posture di sicurezza diverse, perfettamente IEC 62443-compliant.

```python
class AssetZoneMembership(Base):
    __tablename__ = "asset_zone_memberships"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    
    # Asset e Zone
    asset_id = Column(UUID, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    security_zone_id = Column(UUID, ForeignKey("security_zones.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Zone Participation Type (definisce come l'asset partecipa alla zona)
    role = Column(String(100), nullable=False)
    # Valori predefiniti (2025-12-17):
    # - 'primary': Asset core della zona, soggetto pienamente ai requisiti
    # - 'supporting': Supporta la zona ma non è il core
    # - 'boundary': Asset al confine (gateway, firewall, historian edge)
    # - 'shared': Asset condiviso tra più zone
    # - 'monitoring': Monitoraggio / visibility
    # - 'maintenance': Accesso manutenzione
    # - 'safety': Funzione safety-related
    # 
    # Nota: Questo campo è informativo e non modifica i requisiti IEC 62443 di per sé.
    # Definisce come questo asset partecipa nella security zone.
    
    # Scope opzionale (quale interfaccia dell'asset appartiene a questa zona)
    interface_scope = Column(String(255), nullable=True)
    # Può essere: nome interfaccia, IP address, o descrizione dell'interfaccia
    
    # Security Level Target override (opzionale, altrimenti usa quello della zona)
    sl_target = Column(Integer, nullable=True)  # 1-4
    
    # Note
    notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    asset = relationship("Asset", back_populates="zone_memberships")
    security_zone = relationship("SecurityZone", back_populates="asset_memberships")
    
    # Constraints
    # Unique constraint: un asset non può avere lo stesso ruolo nella stessa zona
    # (ma può avere ruoli diversi nella stessa zona)
```

**Vantaggi**:
- ✅ **ISA/IEC 62443 Compliant**: Modella correttamente scenari reali dove un asset ha interfacce diverse in zone diverse
- ✅ **Flessibilità**: Supporta asset con multiple posture di sicurezza
- ✅ **Granularità**: Permette di specificare quale interfaccia appartiene a quale zona
- ✅ **Ruoli**: Distingue il ruolo dell'asset in ciascuna zona

**Retrocompatibilità**:
- Il campo `security_zone_id` in Asset è mantenuto per retrocompatibilità
- Gli asset esistenti continuano a funzionare
- La migrazione a `zone_memberships` può essere graduale

## Sistema Capability-based per SR Assessment (2025-01-XX)

**Nota**: Questo sistema è stato implementato per migliorare il processo di valutazione dei Security Requirements, rendendolo più guidato e basato su evidenze concrete.

### Overview

Il sistema capability-based permette di:
1. **Definire Security Capabilities**: Capability di sicurezza system-wide (es: "Session Locking", "Encryption", "Authentication")
2. **Mappare SR → Capabilities**: Ogni Security Requirement richiede 1-3 capability specifiche
3. **Dichiarare Evidenze**: Asset e conduits possono dichiarare esplicitamente di supportare capability
4. **Inferire Evidenze**: Il sistema può inferire capability da asset_type (es: HMI → tipicamente supporta "Session Locking")
5. **Valutare SR**: L'utente valuta lo SR basandosi su capability richieste vs evidenze disponibili

### Modelli Dati

#### 1. SecurityCapability

Capability di sicurezza system-wide. Definisce cosa un asset/conduit può fare in termini di sicurezza.

```python
class SecurityCapability(Base):
    __tablename__ = "security_capabilities"
    
    id = Column(UUID, primary_key=True)
    code = Column(String(100), unique=True, nullable=False)  # es: "session_locking_timeout"
    name = Column(String(255), nullable=False)  # es: "Session Locking with Timeout"
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # 'identity', 'boundary', 'monitoring', 'system_integrity', etc.
    
    # Applicabilità
    applies_to_asset = Column(Boolean, default=True)
    applies_to_zone = Column(Boolean, default=False)
    applies_to_conduit = Column(Boolean, default=True)
    
    # Typical Roles (per inferenza automatica)
    typical_roles = Column(JSONB, default=list)  # es: ['hmi', 'plc', 'firewall']
    # Se un asset ha asset_type.name che matcha un typical_role, il sistema inferisce che supporta questa capability
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

**Esempio**: 
- `code: "session_locking_timeout"`, `name: "Session Locking with Timeout"`, `typical_roles: ['hmi']`
- Se un asset ha `asset_type.name = "HMI"`, il sistema inferisce che supporta questa capability

#### 2. SRCapability

Mapping tra Security Requirement e Security Capability. Definisce quali capability sono richieste per soddisfare uno SR.

```python
class SRCapability(Base):
    __tablename__ = "sr_capabilities"
    
    id = Column(UUID, primary_key=True)
    sr_id = Column(UUID, ForeignKey("security_requirements.id", ondelete="CASCADE"), nullable=False)
    capability_id = Column(UUID, ForeignKey("security_capabilities.id", ondelete="CASCADE"), nullable=False)
    importance = Column(String(50), nullable=False, default="supporting")  # 'primary', 'supporting'
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

**Esempio**: SR 2.5 (Session Lock) richiede:
- `session_locking_timeout` (primary)
- `session_termination` (supporting)

#### 3. AssetCapability

Evidenza esplicita: un asset dichiara manualmente di supportare (o non supportare) una capability.

```python
class AssetCapability(Base):
    __tablename__ = "asset_capabilities"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    asset_id = Column(UUID, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    capability_id = Column(UUID, ForeignKey("security_capabilities.id", ondelete="CASCADE"), nullable=False)
    
    support_level = Column(String(20), nullable=False, default="unknown")  # 'supported', 'not_supported', 'unknown'
    notes = Column(Text, nullable=True)
    evidence_ref = Column(String(500), nullable=True)  # Riferimento a documento/config
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

**Status nell'UI**:
- `support_level = 'supported'` → status: `'verified'` (✅ verde)
- `support_level = 'not_supported'` → status: `'declared'` (⚠️ arancione)
- `support_level = 'unknown'` → non viene mostrato

#### 4. SRAssessment

Valutazione finale di un Security Requirement per una zona o conduit. Sostituisce `SecurityRequirementCompliance`.

```python
class SRAssessment(Base):
    __tablename__ = "sr_assessments"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    
    sr_id = Column(UUID, ForeignKey("security_requirements.id", ondelete="CASCADE"), nullable=False)
    object_type = Column(String(50), nullable=False)  # 'zone', 'conduit'
    object_id = Column(UUID, nullable=False)  # ID della zona o conduit
    
    status = Column(String(50), nullable=False)  # 'compliant', 'non_compliant', 'partial', 'not_applicable', 'insufficient_info'
    justification = Column(Text, nullable=True)  # Motivazione della decisione
    
    assessor_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    assessed_at = Column(DateTime, default=func.now())
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

#### 5. SRAssessmentEvidence

Evidenze specifiche utilizzate per supportare una valutazione SR.

```python
class SRAssessmentEvidence(Base):
    __tablename__ = "sr_assessment_evidence"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    
    sr_assessment_id = Column(UUID, ForeignKey("sr_assessments.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(UUID, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    capability_id = Column(UUID, ForeignKey("security_capabilities.id", ondelete="CASCADE"), nullable=False)
    
    comment = Column(Text, nullable=True)  # Commento specifico su questa evidenza
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

#### 6. ConduitAsset

Asset associati ai conduits con ruolo specifico.

```python
class ConduitAsset(Base):
    __tablename__ = "conduit_assets"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    
    conduit_id = Column(UUID, ForeignKey("conduits.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(UUID, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(100), nullable=False)  # 'enforcement', 'monitoring', 'gateway'
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### Sistema di Evidenze

Le evidenze possono essere di **due tipi**:

#### 1. Evidenze Esplicite (Verified/Declared)

Create manualmente tramite `AssetCapability`:
- **Verified** (`support_level = 'supported'`): Asset dichiara esplicitamente di supportare la capability
- **Declared** (`support_level = 'not_supported'`): Asset dichiara esplicitamente di NON supportare la capability

**Priorità**: Le evidenze esplicite hanno sempre priorità su quelle inferite.

#### 2. Evidenze Inferite (Inferred)

Inferite automaticamente dal sistema:
- Se `asset_type.name` matcha uno dei `typical_roles` della capability → status: `'inferred'`
- Non viene creato un record `AssetCapability`, è solo per visualizzazione

**Esempio**:
- Capability "Session Locking" ha `typical_roles: ['hmi']`
- Asset "HMI Station" ha `asset_type.name = "HMI"`
- Sistema inferisce → status: `'inferred'`

### Flusso di Valutazione SR

1. **Utente seleziona uno SR** nella compliance tab
2. **Sistema mostra**:
   - Required Capabilities: capability richieste dallo SR (primary/supporting)
   - Available Evidence: asset e conduits nella zona che supportano le capability (esplicite + inferite)
   - Missing Capabilities: capability richieste ma non presenti nella zona
3. **Utente valuta**:
   - Esamina le evidenze disponibili
   - Decide lo status finale (compliant/partial/non_compliant/not_applicable)
   - Inserisce justification
4. **Sistema salva**:
   - Crea/aggiorna `SRAssessment`
   - Crea `SRAssessmentEvidence` per le evidenze utilizzate
   - Ricalcola SL-A della zona

### API Endpoints

```python
# Assessment Assist
GET /api/compliance/zone/{zone_id}/sr/{sr_id}/assessment-assist
# Returns:
# {
#   'required_capabilities': [...],
#   'available_evidence': {
#     'assets': [...],  # Asset con capability (esplicite + inferite)
#     'conduits': [...]
#   },
#   'missing_capabilities': [...],
#   'current_assessment': {...}  # Se esiste già
# }

# Create/Update Assessment
POST /api/compliance/zone/{zone_id}/sr/{sr_id}/assessment
# Body: {
#   'status': 'compliant'|'partial'|'non_compliant'|'not_applicable'|'insufficient_info',
#   'justification': str,
#   'evidence': [  # Opzionale: evidenze specifiche utilizzate
#     {'asset_id': UUID, 'capability_id': UUID, 'comment': str}
#   ]
# }
```

### UI - Processo Guidato

**Level 3 - SR Detail View**:

1. **Descrizione SR**: Titolo, descrizione, SL applicabile
2. **Required Capabilities**: Lista capability richieste (primary evidenziate)
3. **Available Evidence**:
   - Asset: mostra asset con capability supportate (badge verified/declared/inferred)
   - Conduits: mostra conduits con asset associati e capability
4. **Missing Capabilities**: Warning per capability richieste ma non presenti
5. **Zone Assessment**:
   - Radio buttons per status finale
   - Textarea per justification
   - Button "Save Assessment"

### Inizializzazione

- **Security Capabilities**: 34 capability inizializzate tramite `init_security_capabilities.py`
- **SR-Capability Mappings**: Mapping SR → Capability inizializzati tramite `init_sr_capability_mappings.py`
- **Integrazione**: Scripts chiamati automaticamente in `setup_system.py`

### Documentazione

Vedi `docs/EVIDENCE_SYSTEM.md` per dettagli completi sul sistema di evidenze.

## Servizi

### 1. ISA62443ComplianceEngine

**Nota**: Il servizio è già implementato in `backend/app/services/isa62443_compliance_engine.py`.

Calcola automaticamente il Security Level Achieved (SL-A) basato su:
- Configurazione dell'asset/zone/conduit
- Security Requirements soddisfatti
- Compliance status dei requisiti
- Proprietà di sicurezza (encryption, authentication, etc.)

```python
class ISA62443ComplianceEngine:
    @staticmethod
    def calculate_zone_security_level_achieved(
        db: Session,
        zone: SecurityZone
    ) -> Optional[int]:
        """
        Calcola SL-A per una Security Zone.
        
        Logica:
        1. Ottiene tutti i compliance records per la zona
        2. Per ogni Security Requirement applicabile allo SL-T della zona
        3. Calcola percentuale di compliance
        4. SL-A è il più alto SL dove tutti i requisiti sono soddisfatti (>= 80%)
        
        Returns: SL-A (1-4) o None se non calcolabile
        """
        # Implementato: vedi backend/app/services/isa62443_compliance_engine.py
    
    @staticmethod
    def calculate_asset_security_level_achieved(
        db: Session,
        asset: Asset
    ) -> Optional[int]:
        """
        Calcola SL-A per un Asset.
        
        Logica:
        1. Se asset ha SL-A esplicito, lo usa
        2. Se asset è in una zona, usa SL-A della zona
        3. Altrimenti, calcola basandosi su compliance records dell'asset
        
        Returns: SL-A (1-4) o None se non calcolabile
        """
        # Implementato: vedi backend/app/services/isa62443_compliance_engine.py
    
    @staticmethod
    def calculate_conduit_security_level_achieved(
        db: Session,
        conduit: Conduit
    ) -> Optional[int]:
        """
        Calcola SL-A per un Conduit.
        
        Logica:
        1. Verifica encryption e authentication
        2. Verifica compliance con requisiti conduit
        3. Calcola SL-A basandosi su proprietà di sicurezza
        
        Returns: SL-A (1-4) o None se non calcolabile
        """
        # Implementato: vedi backend/app/services/isa62443_compliance_engine.py
    
    @staticmethod
    def calculate_zone_compliance_status(
        db: Session,
        zone: SecurityZone
    ) -> str:
        """
        Calcola lo stato di compliance complessivo per una zona.
        Returns: 'compliant', 'non_compliant', 'partial', 'not_assessed'
        """
        # Implementato: vedi backend/app/services/isa62443_compliance_engine.py
    
    @staticmethod
    def get_compliance_gap_analysis(
        db: Session,
        zone_id: str
    ) -> Dict:
        """
        Ottiene gap analysis per una zona (SL-T vs SL-A, requisiti mancanti, etc.)
        """
        # Implementato: vedi backend/app/services/isa62443_compliance_engine.py
```

**Logica di calcolo SL-A implementata**:
- Per Zone: SL-A è il più alto SL (1-target_sl) dove compliance >= 80%
- Per Asset: Se in zona, eredita SL-A zona; altrimenti calcola da compliance records
- Per Conduit: Basato su encryption/authentication + compliance records

### 2. ZoneRiskCalculator

Estende il risk assessment esistente per includere:
- Security Level gap (SL-T vs SL-A)
- Non-compliance come fattore di rischio
- Zone isolation violations

```python
class ZoneRiskCalculator:
    def calculate_zone_risk(self, zone: SecurityZone) -> Dict:
        """
        Calcola il rischio aggregato di una Security Zone
        """
        pass
    
    def detect_isolation_violations(self, zone: SecurityZone) -> List:
        """
        Rileva violazioni di isolamento tra zone
        """
        pass
```

## API Endpoints

### Security Zones

- `GET /api/security-zones` - Lista zone
- `GET /api/security-zones/{id}` - Dettaglio zona (include asset_count calcolato via AssetZoneMembership)
- `POST /api/security-zones` - Crea zona
- `PUT /api/security-zones/{id}` - Aggiorna zona
- `DELETE /api/security-zones/{id}` - Elimina zona (soft delete)
- `GET /api/security-zones/{id}/assets` - Asset nella zona
- `GET /api/security-zones/{id}/compliance` - Compliance status
- `POST /api/security-zones/{id}/calculate-sl` - Ricalcola SL-A (chiamato automaticamente dopo aggiornamento compliance)
- `GET /api/security-zones/{id}/memberships` - Lista zone memberships per zona
- `POST /api/security-zones/{id}/memberships` - Aggiungi asset a zona con ruolo
- `PUT /api/security-zones/{id}/memberships/{membership_id}` - Aggiorna membership
- `DELETE /api/security-zones/{id}/memberships/{membership_id}` - Rimuovi membership

### Assets (Estensioni IEC 62443)

- `GET /api/assets/{id}/zone-memberships` - Lista zone memberships per asset - **NUOVO (2025-01-XX)**

### Conduits

- `GET /api/conduits` - Lista conduits
- `GET /api/conduits/{id}` - Dettaglio conduit
- `POST /api/conduits` - Crea conduit
- `PUT /api/conduits/{id}` - Aggiorna conduit
- `DELETE /api/conduits/{id}` - Elimina conduit

### Compliance

- `GET /api/compliance/requirements` - Lista Security Requirements
- `GET /api/compliance/zone/{zone_id}` - Compliance per zona
- `GET /api/compliance/zone/{zone_id}/summary` - Compliance summary per dashboard (SL-T, SL-A, GAP, SR status counts) - **Usa SRAssessment**
- `GET /api/compliance/zone/{zone_id}/foundation-requirements` - Foundation Requirements per zona (con percentuale compliance) - **Usa SRAssessment**
- `GET /api/compliance/zone/{zone_id}/security-requirements/{fr_id}` - Security Requirements per Foundation Requirement - **Usa SRAssessment**
- `GET /api/compliance/zone/{zone_id}/sr/{sr_id}/assets` - Asset coinvolti in un Security Requirement (DEPRECATO)
- `GET /api/compliance/zone/{zone_id}/sr/{sr_id}/conduits` - Conduits coinvolti in un Security Requirement (DEPRECATO)
- `GET /api/compliance/asset/{asset_id}` - Compliance per asset
- `POST /api/compliance/assess` - Valuta compliance (triggera ricalcolo automatico SL-A) (DEPRECATO)
- `PUT /api/compliance/records/{compliance_id}` - Aggiorna compliance record (triggera ricalcolo automatico SL-A) (DEPRECATO)
- `GET /api/compliance/gap-analysis` - Gap analysis report
- **Capability-based Assessment (2025-01-XX)** - **NUOVO**
  - `GET /api/compliance/zone/{zone_id}/sr/{sr_id}/assessment-assist` - Dati per valutazione SR (required capabilities, available evidence, missing capabilities)
  - `POST /api/compliance/zone/{zone_id}/sr/{sr_id}/assessment` - Crea/aggiorna SRAssessment con justification ed evidenze

**Nota (2025-01-XX)**: L'endpoint `GET /api/compliance/asset/{asset_id}` è utilizzato dalla tab "IEC 62443" in Asset Detail per mostrare i Security Requirements compliance per l'asset.

## UI/Frontend

### Nuove Pagine

1. **Security Zones Management** (`SecurityZones.vue`, `SecurityZoneDetail.vue`)
   - Lista zone con SL-T e SL-A
   - Creazione/modifica zone
   - **Tab "Details"** (2025-01-XX):
     - Informazioni zona con conteggio asset corretto (calcolato via AssetZoneMembership) - **FIX**
   - **Tab "Assets"** (2025-12-17):
     - Visualizzazione asset nella zona con tipo di partecipazione
     - Colonna "Other Zones" che mostra le altre zone a cui appartiene ogni asset
     - Dialog "Add Asset" con gestione individuale del tipo di partecipazione per ogni asset
     - Tabella degli asset selezionati dove ogni asset può avere il proprio tipo di partecipazione, interface scope e SL target
     - Dropdown "Applica a tutti" per applicare un tipo di partecipazione predefinito a tutti gli asset selezionati
   - **Tab "Conduits"**: Visualizzazione conduits collegati alla zona
   - **Tab "Compliance"** (2025-01-XX): **3-level Compliance Review UX** (`ZoneComplianceTab.vue`) - **NUOVO**
     - **Level 1 (Dashboard)**: Sintesi compatta con SL-T, SL-A, GAP, SR status summary (basato su SRAssessment)
     - **Level 2 (Foundation Requirements)**: Lista FR con percentuale compliance e colore, titoli completi (es: "FR1 - Identification & Authentication")
     - **Level 3 (Security Requirements)**: Dettaglio SR con **processo capability-based guidato** - **NUOVO (2025-01-XX)**
       - Visualizzazione Required Capabilities per SR
       - Available Evidence: asset e conduits con capability (esplicite e inferite)
       - Missing Capabilities: capability richieste ma non presenti
       - Zone Assessment: valutazione finale con status e justification
       - Evidenze esplicite (verified/declared) vs inferite (inferred)
       - Status visuale: verified (verde), declared (arancione), inferred (blu/grigio)
     - Ricalcolo automatico SL-A dopo aggiornamento compliance status - **FIX**
     - Calcolo GAP corretto (distinzione tra null/undefined e 0) - **FIX**
     - Integrazione con SRAssessment (sostituisce SecurityRequirementCompliance) - **NUOVO (2025-01-XX)**
   - **Rimosso Tab "Zone Memberships"** (2025-12-17): Le memberships sono ora gestite direttamente nel tab "Assets"

2. **Conduits Management**
   - Lista conduits tra zone
   - Visualizzazione grafica Zone & Conduit
   - Creazione/modifica conduits

3. **Compliance Dashboard**
   - Overview compliance ISA/IEC 62443
   - Gap analysis (SL-T vs SL-A)
   - Security Requirements checklist
   - Report di compliance

4. **Zone & Conduit Visualization**
   - Grafico interattivo delle zone e conduits
   - Visualizzazione asset nelle zone
   - Highlighting di zone non-compliant

### Estensioni a Pagine Esistenti

1. **Asset Detail**
   - ✅ **Tab "IEC 62443"** - Implementato (2025-01-XX)
     - Riepilogo Compliance: SL-T, SL-A, Gap, Compliance Status
     - Zone Memberships: Lista memberships con ruoli, interface scope, SL target override
     - Security Requirements Compliance: Lista requisiti con stato compliance
     - Gestione memberships: Aggiungi/modifica/rimuovi zone memberships con ruoli
   - ❌ Campo `security_zone_id` nel form di modifica asset - **DEPRECATO** (2025-01-XX)
     - Il campo dropdown `security_zone_id` in `AssetLocationForm.vue` è stato rimosso
     - La gestione delle zone avviene tramite la tab "IEC 62443" che supporta multiple memberships con ruoli

**Nota (2025-01-XX)**: La pagina Asset Detail è stata rivisitata con un nuovo layout a 4 macro-sezioni:
- **Panoramica**: Overview asset con alert banner per problemi critici
- **Relazioni**: Dipendenze, connessioni, comunicazioni
- **Sicurezza e Rischi**: Rischio completo, vulnerabilità, conformità IEC 62443
- **Gestione**: Documenti, contatti, review, fornitori

La conformità IEC 62443 è integrata nella macro-sezione "Sicurezza e Rischi" con sezione collassabile dedicata. Il nuovo layout è disponibile su route alternativa `/assets-new/:id` per test.

**Nota (2025-01-XX)**: La tab "IEC 62443" è stata aggiunta anche al layout originale (`AssetDetail.vue`) per fornire una vista completa della compliance IEC 62443 dell'asset, inclusa la gestione delle zone memberships con ruoli.

2. **Dashboard**
   - Widget compliance ISA/IEC 62443
   - Zone risk overview
   - Gap analysis summary

## Integrazione con Risk Scoring Esistente

Estendere `CompositeRiskScoringEngine` per includere:

```python
# Aggiunte al calcolo del risk score
def calculate(self, asset, language="en") -> Dict[str, Any]:
    # ... calcolo esistente ...
    
    # ISA/IEC 62443 factors
    if asset.security_zone_id:
        zone = get_security_zone(asset.security_zone_id)
        if zone and zone.security_level_target and zone.security_level_achieved:
            sl_gap = zone.security_level_target - zone.security_level_achieved
            if sl_gap > 0:
                vuln_score += sl_gap * 0.5  # Penalità per gap SL
    
    # Non-compliance penalty
    if asset.isa62443_compliance_status == "non-compliant":
        vuln_score += 2
    elif asset.isa62443_compliance_status == "partial":
        vuln_score += 1
    
    # ... resto del calcolo ...
```

## Database Migrations

1. Creare tabelle `security_zones`, `conduits`, `security_requirements`, `security_requirement_compliance`
2. Aggiungere colonne a `assets` per ISA/IEC 62443
3. Creare indici per performance
4. Popolare `security_requirements` con i requisiti standard ISA/IEC 62443

## Fasi di Implementazione

### Fase 1: Modelli Base
- [ ] Modello SecurityZone
- [ ] Modello Conduit
- [ ] Estensioni al modello Asset
- [ ] Migrazioni database

### Fase 2: API Base
- [ ] CRUD Security Zones
- [ ] CRUD Conduits
- [ ] Assignment asset a zone

### Fase 3: Compliance Engine
- [ ] ISA62443ComplianceEngine
- [ ] Calcolo automatico SL-A
- [ ] Security Requirements base

### Fase 4: UI Base
- [ ] Pagina Security Zones Management
- [ ] Pagina Conduits Management
- [ ] Estensioni Asset Detail

### Fase 5: Compliance Tracking
- [ ] Security Requirements compliance
- [ ] Compliance dashboard
- [ ] Gap analysis

### Fase 6: Integrazione Risk Scoring
- [ ] Estensione CompositeRiskScoringEngine
- [ ] Zone risk calculator
- [ ] Dashboard integration

## Note

- Le Security Zones sono **logiche**, non fisiche
- Un asset può essere in una Location fisica ma in una Security Zone diversa
- Il mapping Zone → Locations/Areas è opzionale (solo per documentazione)
- Il Purdue Level rimane una proprietà dell'asset, non della zona
- Security Level (SL) è indipendente dal Purdue Level
- **ISA/IEC 62443 definisce Security Levels da 1 a 4** (non 0-4)
  - SL-1: Protezione contro accesso casuale o involontario
  - SL-2: Protezione contro accesso intenzionale usando mezzi semplici
  - SL-3: Protezione contro accesso intenzionale usando mezzi sofisticati
  - SL-4: Protezione contro accesso intenzionale usando mezzi estremamente sofisticati

### Zone Membership con Ruoli (2025-01-XX)

**Concetto Chiave**: Un asset può appartenere a **multiple Security Zones** con **ruoli diversi**. Questo è conforme a ISA/IEC 62443 e permette di modellare scenari reali dove un asset ha interfacce diverse che appartengono a zone diverse.

**Esempio**:
- **HMI-01** in **Control Zone** con ruolo `operator_interface`
- **HMI-01** in **DMZ** con ruolo `data_publisher`

**Implementazione**:
- Modello `AssetZoneMembership` per gestire multiple memberships
- Campo `role` per distinguere il ruolo dell'asset in ciascuna zona
- Campo `interface_scope` opzionale per specificare quale interfaccia appartiene a quella zona
- Campo `sl_target` opzionale per override del Security Level Target per quella specifica membership

**Retrocompatibilità**:
- Il campo `security_zone_id` in Asset è mantenuto per retrocompatibilità (DEPRECATED)
- Gli asset esistenti continuano a funzionare
- La migrazione a `zone_memberships` può essere graduale

### Zone Participation Type (2025-12-17)

**Aggiornamento**: Il campo `role` è stato rinominato concettualmente in **"Zone Participation Type"** per meglio riflettere il suo scopo. Questo campo definisce **come questo asset partecipa nella security zone** ed è informativo (non modifica i requisiti IEC 62443 di per sé).

**Valori Predefiniti** (implementati come dropdown nella UI):
- **`primary`**: Asset core della zona, soggetto pienamente ai requisiti
- **`supporting`**: Supporta la zona ma non è il core
- **`boundary`**: Asset al confine (gateway, firewall, historian edge)
- **`shared`**: Asset condiviso tra più zone
- **`monitoring`**: Monitoraggio / visibility
- **`maintenance`**: Accesso manutenzione
- **`safety`**: Funzione safety-related

**UI Implementation**:
- Il tipo di partecipazione è selezionabile tramite dropdown con descrizioni
- Ogni valore ha una descrizione che viene mostrata all'utente
- La visualizzazione mostra il label invece del valore raw (es: "Primary" invece di "primary")

## Stato dell'Implementazione

### ✅ Implementato

- **Modelli**: SecurityZone, Conduit, SecurityRequirement, SecurityRequirementCompliance (DEPRECATO, sostituito da SRAssessment)
- **Sistema Capability-based (2025-01-XX)**: SecurityCapability, SRCapability, AssetCapability, SRAssessment, SRAssessmentEvidence, ConduitAsset
- **Servizi**: ISA62443ComplianceEngine (calcolo SL-A per zone, asset, conduits)
- **API**: CRUD Security Zones, CRUD Conduits, Compliance endpoints, Capability-based assessment endpoints
- **UI**: Pagine Security Zones, Conduits, integrazione in Asset Detail, 3-level compliance review con processo capability-based
- **Database**: Migrazioni per tutti i modelli ISA 62443, migrazione capability-based, inizializzazione capability e mapping SR

### 🔄 In Sviluppo / Da Migliorare

- Integrazione completa con Risk Scoring esistente
- Zone Risk Calculator avanzato
- Visualizzazione grafica Zone & Conduit
- Compliance Dashboard completo
- Gap Analysis avanzata
- **Sistema Capability-based**:
  - UI per gestione manuale AssetCapability (creare/modificare evidenze esplicite)
  - Visualizzazione capability in Asset Detail
  - Miglioramento inferenza capability da asset_type (matching più sofisticato)

### 📋 Da Implementare

- Zone isolation violations detection
- Advanced compliance reporting
- Security Requirements popolamento standard ISA/IEC 62443
- UI completa per gestione AssetCapability (endpoint API per creare/modificare evidenze esplicite)
- Visualizzazione capability in Asset Detail

## Asset Ownership e Point-of-Contact

### Requisiti

Aggiungere due nuovi concetti per gli asset:
- **Ownership**: Proprietari/responsabili dell'asset (può essere multiplo)
- **Point-of-Contact**: Contatti principali per supporto/operazioni (può essere multiplo)

### Soluzione: Estendere Relazione Many-to-Many con Ruoli

Estendere la tabella `asset_contacts` esistente per includere un campo `role` che permette di distinguere i diversi tipi di contatti:

```python
# Nuova struttura per asset_contacts
asset_contacts = Table(
    "asset_contacts",
    Base.metadata,
    Column("asset_id", UUID, ForeignKey("assets.id"), primary_key=True),
    Column("contact_id", UUID, ForeignKey("contacts.id"), primary_key=True),
    Column("role", String(50), nullable=False, default="other")  
    # Valori possibili: 'owner', 'point_of_contact', 'other', 'technical', 'administrative', etc.
)
```

### Ruoli Supportati

- `owner`: Proprietario/responsabile dell'asset
- `point_of_contact`: Contatto principale per supporto/operazioni
- `other`: Contatto generico (mantiene compatibilità con dati esistenti)
- `technical`: Contatto tecnico (opzionale, per estensibilità futura)
- `administrative`: Contatto amministrativo (opzionale, per estensibilità futura)

### Modifiche al Modello Asset

```python
class Asset(Base):
    # ... campi esistenti ...
    
    # Relationships esistenti (mantenute per compatibilità)
    contacts = relationship("Contact", secondary=asset_contacts, backref="assets")
    
    # Nuove properties per accesso facilitato
    @property
    def owners(self):
        """Lista dei contatti con ruolo 'owner'"""
        return [c for c in self.contacts if self._get_contact_role(c.id) == 'owner']
    
    @property
    def points_of_contact(self):
        """Lista dei contatti con ruolo 'point_of_contact'"""
        return [c for c in self.contacts if self._get_contact_role(c.id) == 'point_of_contact']
```

**Nota**: Per performance, è meglio usare query dirette invece di properties. Vedere sezione API.

### Migrazione Database

1. **Creare nuova colonna `role`** nella tabella `asset_contacts`
2. **Valore default**: 'other' per tutti i record esistenti (mantiene compatibilità)
3. **Aggiungere constraint**: CHECK per valori validi di `role`
4. **Indici**: Aggiungere indice su `(asset_id, role)` per performance

### API Endpoints

```python
# Endpoints esistenti estesi
GET /api/assets/{id}/contacts
# Ora include il campo 'role' per ogni contatto

PUT /api/assets/{id}/contacts
# Accetta lista di {contact_id, role}

# Nuovi endpoints specifici
GET /api/assets/{id}/owners
# Lista dei contatti con ruolo 'owner'

GET /api/assets/{id}/points-of-contact
# Lista dei contatti con ruolo 'point_of_contact'

POST /api/assets/{id}/contacts
# Aggiunge un contatto con ruolo specifico
# Body: {contact_id: UUID, role: 'owner'|'point_of_contact'|'other'}

DELETE /api/assets/{id}/contacts/{contact_id}
# Rimuove un contatto (indipendentemente dal ruolo)

# Filtri per asset list
GET /api/assets?owner_contact_id={id}  # Asset con questo owner
GET /api/assets?point_of_contact_id={id}  # Asset con questo point-of-contact
GET /api/assets?contact_role={role}  # Asset con contatti di questo ruolo
```

### Schema API

```python
class AssetContactSchema(BaseModel):
    contact_id: uuid.UUID
    role: str  # 'owner', 'point_of_contact', 'other', etc.
    contact: ContactSchema  # Dati completi del contatto

class AssetContactCreate(BaseModel):
    contact_id: uuid.UUID
    role: str = Field(..., pattern="^(owner|point_of_contact|other|technical|administrative)$")
```

### UI

- **Asset Form**: 
  - Sezione "Owners" con lista multipla di contatti
  - Sezione "Points of Contact" con lista multipla di contatti
  - Sezione "Other Contacts" per contatti generici
  
- **Asset Detail**: 
  - Tab "Contacts" con filtri per ruolo
  - Sezioni separate per Owners, Points of Contact, Other
  
- **Asset List**: 
  - Colonna opzionale per mostrare owners/points-of-contact
  - Filtri per owner o point-of-contact
  
- **Contact Management**:
  - Mostra in quali asset un contatto è owner/point-of-contact

### Compatibilità Retroattiva

- Tutti i contatti esistenti avranno `role='other'` di default
- Gli endpoint esistenti continuano a funzionare
- Le query esistenti funzionano (tutti i contatti vengono restituiti)
- Nuovi filtri opzionali per ruoli specifici

## Domande Aperte

1. **Security Requirements**: Quali SR includere inizialmente? (Foundation, System, Component)
2. **SL-A Calculation**: Quali fattori pesare di più nel calcolo automatico?
3. **Compliance Assessment**: Manuale, automatico, o ibrido?
4. **Reporting**: Quali report sono prioritari?
5. **Integration**: Quanto integrare con il risk scoring esistente vs. mantenerli separati?
6. **Ownership/Point-of-Contact**: ✅ Implementato con ruoli nella many-to-many (Opzione 2) per supportare multipli owner e point-of-contact

---

## Asset Dependencies e Risk Propagation

### Requisiti

Aggiungere un sistema per tracciare:
- **Dipendenze funzionali** tra asset (non solo connessioni di rete)
- **Point-of-failure analysis**: Identificare asset critici in una catena
- **Risk propagation**: Come i rischi si propagano tra asset correlati
- **Dependency chains**: Catene di dipendenza per analisi di impatto

### Differenza con AssetConnection Esistente

**AssetConnection** (già presente):
- Connessioni di rete fisiche
- Porte, protocolli, interfacce
- Livello tecnico/infrastrutturale

**AssetDependency** (nuovo):
- Dipendenze funzionali/logiche
- Relazioni di business/processo
- Livello logico/operativo

**Esempio:**
- AssetConnection: "PLC-1 è connesso a Switch-1 via Ethernet"
- AssetDependency: "Processo-Produzione dipende da PLC-1" (se PLC-1 fallisce, il processo si ferma)

### Visibilità Incrociata: Connessioni e Dipendenze

**Principio**: Mantenere connessioni e dipendenze come sezioni separate, ma fornire visibilità incrociata per identificare:
- Connessioni senza dipendenza corrispondente (potenziale gap)
- Connessioni con dipendenza corrispondente (modellazione completa)
- Dipendenze senza connessione (dipendenze logiche/pure)

#### Stati di Relazione Connessione-Dipendenza

Per ogni connessione tra due asset, il sistema può identificare lo stato della relazione:

1. **Connessione con Dipendenza** ✅
   - Esiste sia AssetConnection che AssetDependency tra gli stessi asset
   - Badge: Verde "Dependency Exists"
   - Indica modellazione completa (sia livello fisico che logico)

2. **Connessione senza Dipendenza** ⚠️
   - Esiste AssetConnection ma NON AssetDependency
   - Badge: Giallo "No Dependency"
   - Potenziale gap: potrebbe essere necessario modellare anche la dipendenza funzionale
   - Non sempre critico (es: connessioni di rete puramente infrastrutturali)

3. **Dipendenze senza Connessione** ℹ️
   - Esiste AssetDependency ma NON AssetConnection
   - Badge: Blu "Logical Dependency"
   - Dipendenze logiche/pure (es: processo dipende da asset senza connessione diretta)

4. **Criticità: Dipendenza Mancante** 🔴
   - Connessione critica (es: controllo, sicurezza) senza dipendenza corrispondente
   - Badge: Rosso "Missing Dependency"
   - Alert quando:
     - Connessione ha `connection_type` critico ('control', 'safety', 'operational')
     - E non esiste dipendenza corrispondente
   - Suggerisce di creare dipendenza per analisi di impatto completa

#### Servizio ConnectionDependencyAnalyzer

```python
class ConnectionDependencyAnalyzer:
    def get_connection_dependency_status(
        self,
        connection: AssetConnection
    ) -> Dict:
        """
        Analizza lo stato di relazione tra una connessione e le dipendenze.
        
        Returns:
            Dict con:
            - 'has_dependency': bool
            - 'dependency_id': UUID (se esiste)
            - 'status': 'complete'|'missing'|'logical_only'|'connection_only'
            - 'severity': 'info'|'warning'|'critical'
            - 'suggested_action': str
        """
        pass
    
    def get_connections_with_dependency_status(
        self,
        asset_id: UUID
    ) -> List[Dict]:
        """
        Ottiene tutte le connessioni di un asset con il loro stato di dipendenza.
        """
        pass
    
    def find_missing_dependencies(
        self,
        tenant_id: UUID,
        critical_only: bool = True
    ) -> List[Dict]:
        """
        Trova connessioni critiche senza dipendenza corrispondente.
        """
        pass
    
    def suggest_dependencies_from_connections(
        self,
        connection: AssetConnection
    ) -> Dict:
        """
        Suggerisce tipo di dipendenza basandosi sul tipo di connessione.
        Es: connection_type='control' → dependency_type='control'
        """
        pass
```

#### API Endpoints Estesi

```python
# Estensione endpoint connessioni esistenti
GET /api/assets/{id}/connections
# Ora include campo 'dependency_status' per ogni connessione:
# {
#   "id": "...",
#   "parent_asset": {...},
#   "child_asset": {...},
#   "connection_type": "ethernet",
#   "dependency_status": {
#     "has_dependency": true,
#     "dependency_id": "...",
#     "status": "complete",
#     "severity": "info"
#   }
# }

# Nuovi endpoint per analisi incrociata
GET /api/assets/{id}/connections/dependency-analysis
# Analisi completa: connessioni con stato dipendenze
# Query params: ?show_missing_only=true

GET /api/assets/{id}/missing-dependencies
# Lista connessioni critiche senza dipendenza
# Query params: ?critical_only=true

POST /api/assets/{id}/connections/{connection_id}/suggest-dependency
# Suggerisce creazione dipendenza basata su connessione
# Returns: DependencyCreate suggerito
```

#### UI - Estensioni Tab Connessioni

**Asset Detail - Tab "Connections" (Estesa)**:

- **Lista Connessioni con Badge**:
  - Badge colorato per ogni connessione:
    - 🟢 Verde "Dependency": Connessione con dipendenza
    - 🟡 Giallo "No Dependency": Connessione senza dipendenza
    - 🔴 Rosso "Missing": Connessione critica senza dipendenza
    - 🔵 Blu "Logical": Solo dipendenza logica (mostrato in tab Dependencies)
  
  - Colonne:
    - Asset collegato
    - Tipo connessione
    - Protocollo/Porta
    - **Badge Dependency Status** ← NUOVO
    - Azioni (View, Edit, Delete)
  
- **Filtri**:
  - "Show connections with dependencies"
  - "Show connections without dependencies"
  - "Show critical missing dependencies"
  
- **Quick Actions**:
  - "Create Dependency" (quando manca dipendenza)
  - "View Dependency" (quando esiste)
  - "Suggest Dependency" (suggerisce tipo basato su connessione)

- **Sezione "Missing Dependencies"** (se ci sono):
  - Lista connessioni critiche senza dipendenza
  - Button "Create Dependency" per ciascuna
  - Pre-compila form con suggerimenti basati su connessione

#### UI - Network Topology Enhancement

**Network Map / Topology View**:

- **Edge Styling**:
  - Connessioni con dipendenza: Edge verde solido
  - Connessioni senza dipendenza: Edge giallo tratteggiato
  - Connessioni critiche senza dipendenza: Edge rosso spesso
  
- **Tooltip su Hover**:
  - Mostra informazioni connessione
  - Mostra stato dipendenza
  - Link rapido "View/Create Dependency"
  
- **Legenda**:
  - Spiega colori e stili edge
  - Distingue connessioni fisiche vs dipendenze logiche

#### Logica di Matching Connessione-Dipendenza

**Matching Criteria**:
- Due asset sono "matchati" se:
  - Connessione: `parent_asset_id` ↔ `child_asset_id`
  - Dipendenza: `dependent_asset_id` ↔ `dependency_asset_id`
  - Direzione: Può essere bidirezionale (A→B connessione può matchare B→A dipendenza)

**Esempi**:
```
Connessione: PLC-1 (parent) → Switch-1 (child)
Dipendenze possibili:
  ✅ PLC-1 → Switch-1 (stessa direzione)
  ✅ Switch-1 → PLC-1 (direzione inversa, se logico)
  ❌ Nessuna (no match)
```

#### Integrazione con Risk Assessment

Le connessioni critiche senza dipendenza possono influenzare il risk assessment:

```python
# Estendere calcolo risk per includere "missing dependencies"
def calculate(self, asset, language="en") -> Dict[str, Any]:
    # ... calcolo esistente ...
    
    # Missing dependency penalty (solo per connessioni critiche)
    critical_connections_without_dep = get_critical_connections_without_dependency(asset.id)
    if critical_connections_without_dep:
        vuln_score += 0.5  # Penalità leggera per modellazione incompleta
        vuln_break.append(f"{len(critical_connections_without_dep)} critical connections without dependency")
    
    return breakdown
```

### Distinzione Concettuale: Processi come First-Class Citizen (Futuro)

**Nota**: Attualmente, quando si modella una dipendenza come "Processo-Produzione dipende da PLC-1", il processo viene rappresentato come un Asset (es: Asset con `asset_type='process'`). Questo approccio funziona per ora, ma quando il sistema crescerà sarà necessario distinguere:

**Oggi (Implementazione Attuale)**:
- Processo = Asset (con `asset_type='process'` o simile)
- AssetDependency: `dependent_asset_id` può essere un processo rappresentato come Asset

**Domani (Quando Crescerà)**:
- **Processo** come entità separata (`BusinessProcess` o `OperationalProcess`)
- Modello dedicato per processi con proprietà specifiche:
  - Business impact
  - Operational criticality
  - Service level agreements (SLA)
  - Process dependencies (processo → processo)
- Nuovo modello `ProcessDependency` per dipendenze processo → asset
- Estensione `AssetDependency` per supportare anche dipendenze processo → asset

**Vantaggi della Separazione Futura**:
- Modellazione più accurata di processi business vs asset tecnici
- Analisi di impatto business separata da analisi tecnica
- Reporting dedicato per processi
- Gestione SLA e metriche di processo

**Migrazione**: Quando si implementerà, gli Asset con `asset_type='process'` potranno essere migrati al nuovo modello `BusinessProcess` mantenendo le dipendenze esistenti.

### Modello AssetDependency

```python
class AssetDependency(Base):
    __tablename__ = "asset_dependencies"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    
    # Asset dipendente e asset da cui dipende
    dependent_asset_id = Column(UUID, ForeignKey("assets.id"), nullable=False)
    dependency_asset_id = Column(UUID, ForeignKey("assets.id"), nullable=False)
    
    # Tipo di dipendenza
    dependency_type = Column(String(50), nullable=False)
    # Valori: 'functional', 'operational', 'data', 'control', 'safety', 'power', 'network'
    # Nota: In futuro sarà normalizzato tramite DependencyType (vedi sezione "Normalizzazione Dependency Type")
    
    # Criticità della dipendenza
    criticality = Column(String(20), nullable=False, default="medium")
    # Valori: 'low', 'medium', 'high', 'critical'
    
    # Confidence e Source della dipendenza
    confidence = Column(String(20), default="medium")
    # Valori: 'low', 'medium', 'high'
    # 'low': Ipotesi o dipendenza incerta
    # 'medium': Dipendenza probabile o basata su assessment preliminare
    # 'high': Dipendenza certa, verificata manualmente
    
    source = Column(String(50), nullable=True)
    # Valori: 'manual', 'assessment', 'import', 'template'
    # 'manual': Creata manualmente dall'utente
    # 'assessment': Derivata da assessment/analisi automatica
    # 'import': Importata da fonte esterna
    # 'template': Ereditata da template o configurazione standard
    
    # Descrizione
    description = Column(Text)
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    dependent_asset = relationship("Asset", foreign_keys=[dependent_asset_id])
    dependency_asset = relationship("Asset", foreign_keys=[dependency_asset_id])
```

**Nota su Confidence e Source**:
- **Confidence**: Permette di distinguere dipendenze certe da ipotesi, evitando sovrastima del rischio
- **Source**: Traccia l'origine della dipendenza per audit trail e comprensione del contesto
- Le dipendenze con `confidence='low'` possono essere pesate meno nel calcolo del rischio propagato

### Tipi di Dipendenza

- `functional`: Dipendenza funzionale (es: processo dipende da asset)
- `operational`: Dipendenza operativa (es: asset richiede altro asset per operare)
- `data`: Dipendenza dati (es: asset richiede dati da altro asset)
- `control`: Dipendenza di controllo (es: asset controllato da altro asset)
- `safety`: Dipendenza di sicurezza (es: asset di sicurezza dipende da altro)
- `power`: Dipendenza energetica (es: asset richiede alimentazione da altro)
- `network`: Dipendenza di rete (logica, diversa da AssetConnection fisica)

### Normalizzazione Dependency Type (Futuro)

**Nota**: Attualmente `dependency_type` è una stringa. Quando il sistema scalerà e richiederà:
- Reporting avanzato per tipo
- Pesi diversi nel calcolo del rischio per tipo
- Algoritmi di propagazione diversi per tipo

Sarà necessario normalizzare in un modello dedicato:

```python
class DependencyType(Base):
    __tablename__ = "dependency_types"
    
    id = Column(UUID, primary_key=True)
    
    # Codice tipo (es: 'data', 'control', 'safety')
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Proprietà di propagazione
    default_weight = Column(Float, default=1.0)  # Peso default nel calcolo rischio (0.0-2.0)
    propagates_risk = Column(Boolean, default=True)  # Se propaga rischio upstream
    propagates_impact = Column(Boolean, default=True)  # Se propaga impatto downstream
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

**Esempi di configurazione**:
- `data`: `propagates_risk=True`, `propagates_impact=False`, `default_weight=0.5` (impatto basso)
- `control`: `propagates_risk=True`, `propagates_impact=True`, `default_weight=1.5` (risk e impatto alti)
- `safety`: `propagates_risk=False`, `propagates_impact=True`, `default_weight=2.0` (impatto massimo, risk separato)

**Migrazione futura**: Quando si implementerà DependencyType, `AssetDependency.dependency_type` diventerà una foreign key a `DependencyType.code`.

### Servizi per Analisi

#### 1. DependencyChainAnalyzer

```python
class DependencyChainAnalyzer:
    def get_dependency_chain(
        self, 
        asset_id: UUID, 
        direction: str = "downstream",
        max_depth: int = 10,
        visited: Set[UUID] = None
    ) -> Dict:
        """
        Trova la catena di dipendenze con protezione da loop.
        
        Args:
            asset_id: Asset di partenza
            direction: 'downstream' (asset che dipendono) o 'upstream' (da cui dipende)
            max_depth: Profondità massima della catena (default: 10)
            visited: Set di asset già visitati (per rilevare loop)
        
        Returns:
            Dict con:
            - 'chain': Lista di asset nella catena
            - 'loops_detected': Lista di loop rilevati (se presenti)
            - 'depth': Profondità raggiunta
        """
        if visited is None:
            visited = set()
        
        if asset_id in visited:
            # Loop rilevato
            return {
                'chain': [],
                'loops_detected': [list(visited) + [asset_id]],
                'depth': len(visited),
                'error': 'dependency_loop_detected'
            }
        
        if len(visited) >= max_depth:
            return {
                'chain': [],
                'loops_detected': [],
                'depth': max_depth,
                'warning': 'max_depth_reached'
            }
        
        visited.add(asset_id)
        # ... logica di ricerca dipendenze ...
        # Ricorsione con visited aggiornato
        pass
    
    def detect_dependency_loops(self, tenant_id: UUID) -> List[Dict]:
        """
        Rileva tutti i loop di dipendenza nel tenant.
        Utile per validazione dati e report.
        
        Returns:
            Lista di loop rilevati, ciascuno con:
            - 'assets': Lista UUID degli asset nel loop
            - 'dependencies': Lista delle dipendenze che formano il loop
            - 'severity': 'critical' se coinvolge asset critici
        """
        pass
    
    def find_point_of_failures(self, asset_id: UUID) -> List[Dict]:
        """
        Identifica point-of-failure:
        - Asset critici nella catena
        - Asset con molte dipendenze downstream
        - Asset con criticality 'critical'
        - Considera confidence delle dipendenze (dipendenze low-confidence pesano meno)
        """
        pass
    
    def get_impact_scope(
        self, 
        asset_id: UUID,
        consider_confidence: bool = True
    ) -> Dict:
        """
        Calcola l'impatto se un asset fallisce:
        - Quanti asset sono affetti (downstream)
        - Quali processi sono interrotti
        - Risk score aggregato degli asset affetti
        - Considera confidence delle dipendenze se consider_confidence=True
        """
        pass
```

**Protezione da Loop**:
- **Visited Set**: Mantiene traccia degli asset già visitati durante la traversata
- **Max Depth**: Limita la profondità massima per evitare loop infiniti
- **Loop Detection**: Rileva e segnala loop quando vengono trovati
- **Real-world**: I loop sono possibili in ambienti OT (es: A→B→C→A), quindi la logica deve gestirli senza crashare

#### 2. RiskPropagationEngine

```python
class RiskPropagationEngine:
    def calculate_propagated_risk(
        self, 
        asset: Asset,
        consider_confidence: bool = True
    ) -> Dict:
        """
        Calcola il rischio propagato:
        - Risk score dell'asset stesso
        - Risk score degli asset upstream (da cui dipende), pesato per confidence
        - Risk score degli asset downstream (che dipendono da questo), pesato per confidence
        - Risk aggregato della catena
        
        Se consider_confidence=True:
        - Dipendenze con confidence='low' hanno peso ridotto (es: 0.5x)
        - Dipendenze con confidence='high' hanno peso completo (1.0x)
        - Dipendenze con confidence='medium' hanno peso standard (0.75x)
        """
        pass
    
    def identify_risk_chains(
        self, 
        threshold: float = 7.0,
        min_confidence: str = "low"
    ) -> List[Dict]:
        """
        Identifica catene di rischio:
        - Catene dove tutti gli asset hanno risk > threshold
        - Catene critiche (tutti criticality = 'critical')
        - Considera solo dipendenze con confidence >= min_confidence
        """
        pass
    
    def get_risk_propagation_path(
        self, 
        from_asset_id: UUID, 
        to_asset_id: UUID,
        max_depth: int = 10
    ) -> Dict:
        """
        Trova il percorso di propagazione del rischio tra due asset.
        Include protezione da loop e considera confidence delle dipendenze.
        
        Returns:
            Dict con:
            - 'path': Lista di asset nel percorso
            - 'total_risk': Risk score aggregato del percorso
            - 'confidence': Confidence media del percorso
            - 'loops_detected': Se ci sono loop nel percorso
        """
        pass
```

### API Endpoints

```python
# Dependency Management
GET /api/assets/{id}/dependencies
# Lista dipendenze (upstream: da cui dipende, downstream: che dipendono da questo)

POST /api/assets/{id}/dependencies
# Crea nuova dipendenza
# Body: {
#   dependency_asset_id: UUID, 
#   dependency_type: str, 
#   criticality: str, 
#   confidence: str (opzionale, default: 'medium'),
#   source: str (opzionale, default: 'manual'),
#   description: str
# }

DELETE /api/assets/{id}/dependencies/{dependency_id}
# Rimuove dipendenza

# Analysis Endpoints
GET /api/assets/{id}/dependency-chain
# Query params: ?direction=upstream|downstream&max_depth=5

GET /api/assets/{id}/point-of-failures
# Identifica point-of-failure nella catena

GET /api/assets/{id}/impact-scope
# Calcola impatto se asset fallisce

GET /api/assets/{id}/risk-propagation
# Calcola rischio propagato

GET /api/risk-chains
# Query params: ?threshold=7.0&criticality=critical
# Lista catene di rischio critiche

# Loop Detection
GET /api/dependencies/loops
# Rileva tutti i loop di dipendenza nel tenant
# Query params: ?severity=critical (opzionale, filtra solo loop critici)

GET /api/assets/{id}/dependency-chain
# Query params aggiuntivi: ?max_depth=10&detect_loops=true
# Include informazioni su loop rilevati nella catena
```

### UI

#### Asset Detail - Nuova Tab "Dependencies"

- **Upstream Dependencies**: Asset da cui questo asset dipende
  - Lista con tipo, criticità, confidence, source, risk score
  - Badge colorato per confidence (low=giallo, medium=arancione, high=verde)
  - Icona per source (manual, assessment, import, template)
  - **Badge "Has Connection"**: Mostra se esiste anche AssetConnection corrispondente
  - Visualizzazione grafica della catena upstream
  - Warning se loop rilevati nella catena
  
- **Downstream Dependencies**: Asset che dipendono da questo
  - Lista con tipo, criticità, confidence, source, risk score
  - Badge colorato per confidence
  - **Badge "Has Connection"**: Mostra se esiste anche AssetConnection corrispondente
  - Visualizzazione grafica della catena downstream
  
- **Dependency Graph**: Grafo interattivo delle dipendenze
  - Highlighting di point-of-failure
  - Color coding per risk score e confidence
  - Visualizzazione loop (se presenti) con edge rosso tratteggiato
  - **Overlay opzionale**: Mostra anche connessioni fisiche (AssetConnection) con stile diverso
  - Filtri per tipo di dipendenza, confidence, source
  - Tooltip con dettagli confidence e source
  - Link rapido "View Connection" se esiste connessione corrispondente

**Nota**: Per visibilità incrociata completa, vedere anche Tab "Connections" che mostra badge di stato dipendenze per ogni connessione.

#### Dashboard - Nuova Sezione

- **Critical Dependencies**: Asset con dipendenze critiche
- **Point-of-Failure Analysis**: Top asset critici
- **Risk Chains**: Catene di rischio identificate
- **Impact Analysis**: Asset con maggiore impatto downstream
- **Dependency Loops**: Alert se loop critici rilevati (con link a dettagli)
- **Low Confidence Dependencies**: Dipendenze con confidence bassa che necessitano verifica

#### Network Map Enhancement

- **Dual Layer Visualization**:
  - Layer 1: Connessioni fisiche (AssetConnection) - Edge grigio/blu
  - Layer 2: Dipendenze logiche (AssetDependency) - Edge verde/arancione
  - Toggle per mostrare/nascondere ciascun layer
  
- **Edge Styling con Badge**:
  - Connessioni con dipendenza corrispondente: Edge verde solido + badge "Dependency"
  - Connessioni senza dipendenza: Edge giallo tratteggiato + badge "No Dependency"
  - Connessioni critiche senza dipendenza: Edge rosso spesso + badge "Missing Dependency"
  - Solo dipendenze (senza connessione): Edge blu tratteggiato + badge "Logical Only"
  
- **Tooltip su Hover**:
  - Mostra tipo connessione/dipendenza
  - Mostra stato di relazione (con/senza corrispondenza)
  - Link rapidi "View/Create Dependency" o "View Connection"
  
- **Legenda Interattiva**:
  - Spiega colori e stili per connessioni e dipendenze
  - Mostra statistiche: X connessioni, Y dipendenze, Z match, W missing

### Integrazione con Risk Scoring

Estendere `CompositeRiskScoringEngine`:

```python
def calculate(self, asset, language="en") -> Dict[str, Any]:
    # ... calcolo esistente ...
    
    # Risk propagation factors (considera confidence)
    upstream_risk = self._calculate_upstream_risk(asset, consider_confidence=True)
    downstream_impact = self._calculate_downstream_impact(asset, consider_confidence=True)
    
    # Aggiungi al breakdown
    breakdown["upstream_risk"] = upstream_risk
    breakdown["downstream_impact"] = downstream_impact
    
    # Modifica final_score se necessario
    # Solo dipendenze con confidence alta/medium contribuiscono significativamente
    if upstream_risk > 7.0:
        final_score = min(10, final_score + 0.5)  # Penalità per dipendenze ad alto rischio
    
    return breakdown

def _calculate_upstream_risk(self, asset, consider_confidence=True) -> float:
    """
    Calcola rischio upstream pesato per confidence delle dipendenze.
    """
    dependencies = get_upstream_dependencies(asset.id)
    total_risk = 0.0
    
    for dep in dependencies:
        dep_asset_risk = dep.dependency_asset.risk_score or 0.0
        
        # Applica peso basato su confidence
        if consider_confidence:
            if dep.confidence == 'low':
                weight = 0.5  # Dipendenze incerte pesano meno
            elif dep.confidence == 'medium':
                weight = 0.75
            else:  # 'high'
                weight = 1.0
        else:
            weight = 1.0
        
        total_risk += dep_asset_risk * weight
    
    return total_risk / len(dependencies) if dependencies else 0.0
```

### Esempi d'Uso

**Scenario 1: Point-of-Failure Analysis**
```
Asset: "Main Production Line Controller"
Dependencies:
  - Upstream: "Power Supply Unit" (criticality: critical, confidence: high, source: manual)
  - Upstream: "Network Switch" (criticality: high, confidence: high, source: manual)
  - Downstream: "Robot Arm 1" (criticality: high, confidence: high, source: manual)
  - Downstream: "Robot Arm 2" (criticality: high, confidence: high, source: manual)
  - Downstream: "Quality Control System" (criticality: medium, confidence: medium, source: assessment)

Analysis:
  - Point-of-Failure: Se "Main Production Line Controller" fallisce, 
    3 asset downstream sono affetti (considerando solo dipendenze high-confidence)
  - Impact Score: 8.5 (alto)
  - Recommendation: Implementare ridondanza
```

**Scenario 2: Risk Propagation con Confidence**
```
Asset: "PLC-1" (risk_score: 6.5)
Dependencies:
  - Upstream: "HMI-1" (risk_score: 8.0, confidence: high) ← alto rischio upstream, alta confidence
  - Upstream: "Sensor-1" (risk_score: 7.0, confidence: low) ← rischio alto ma confidence bassa
  - Downstream: "Valve-1" (risk_score: 4.0, confidence: high)
  - Downstream: "Valve-2" (risk_score: 4.0, confidence: high)

Propagated Risk:
  - Base risk: 6.5
  - Upstream risk influence: +1.0 (HMI-1: 8.0 * 1.0) + +0.35 (Sensor-1: 7.0 * 0.5 per low confidence)
  - Propagated risk: 7.85
  - Recommendation: Ridurre rischio di HMI-1 per mitigare rischio propagato
  - Note: Sensor-1 ha rischio alto ma confidence bassa, verificare dipendenza reale
```

**Scenario 3: Dependency Loop Detection**
```
Asset: "PLC-A" → dipende da "PLC-B"
Asset: "PLC-B" → dipende da "PLC-C"
Asset: "PLC-C" → dipende da "PLC-A" ← LOOP RILEVATO

Analysis:
  - Loop rilevato: PLC-A → PLC-B → PLC-C → PLC-A
  - Warning: Loop può causare calcoli infiniti di risk propagation
  - Action: DependencyChainAnalyzer limita profondità e segnala loop
  - Recommendation: Verificare dipendenze reali, potrebbe essere errore di modellazione
```

### Migrazione Database

1. Creare tabella `asset_dependencies` con campi:
   - Campi base (id, tenant_id, dependent_asset_id, dependency_asset_id)
   - `dependency_type` (String, con CHECK constraint)
   - `criticality` (String, con CHECK constraint, default: 'medium')
   - `confidence` (String, con CHECK constraint, default: 'medium')
   - `source` (String, nullable, con CHECK constraint)
   - Campi descrittivi (description, notes)
   - Metadata (created_at, updated_at, deleted_at)

2. Aggiungere indici:
   - `(dependent_asset_id, dependency_type)`
   - `(dependency_asset_id, criticality)`
   - `(tenant_id, deleted_at)`
   - `(confidence)` per filtri su confidence
   - `(source)` per filtri su source

3. Aggiungere constraint:
   - CHECK per `dependency_type` validi: 'functional', 'operational', 'data', 'control', 'safety', 'power', 'network'
   - CHECK per `criticality` validi: 'low', 'medium', 'high', 'critical'
   - CHECK per `confidence` validi: 'low', 'medium', 'high'
   - CHECK per `source` validi: 'manual', 'assessment', 'import', 'template' (se non NULL)
   - Prevent self-dependency: `dependent_asset_id != dependency_asset_id`

4. **Nota per il futuro**: Quando si implementerà `DependencyType`, aggiungere colonna `dependency_type_id` (FK) e mantenere `dependency_type` (String) per compatibilità durante migrazione graduale.

### Fasi di Implementazione

#### Fase 1: Modello Base
- [ ] Modello AssetDependency
- [ ] Migrazione database
- [ ] CRUD base

#### Fase 2: API Base
- [ ] Endpoints per gestire dipendenze
- [ ] Endpoints per query base (upstream/downstream)

#### Fase 3: Analysis Engine
- [ ] DependencyChainAnalyzer
- [ ] RiskPropagationEngine
- [ ] Endpoints di analisi

#### Fase 4: UI Base
- [ ] Tab Dependencies in Asset Detail
- [ ] Visualizzazione grafica base

#### Fase 5: Visibilità Incrociata Connessioni-Dipendenze
- [ ] ConnectionDependencyAnalyzer service
- [ ] Estensione endpoint connessioni con campo `dependency_status`
- [ ] Endpoint `missing-dependencies` per trovare gap
- [ ] Endpoint `suggest-dependency` per suggerimenti
- [ ] Badge e indicatori nella UI Tab Connections
- [ ] Badge "Has Connection" nella UI Tab Dependencies
- [ ] Network Map enhancement con dual layer visualization
- [ ] Filtri e quick actions per creare dipendenze da connessioni

#### Fase 6: Advanced Features
- [ ] Point-of-Failure Analysis
- [ ] Risk Propagation Visualization
- [ ] Dashboard integration

#### Fase 7: Risk Scoring Integration
- [ ] Estensione CompositeRiskScoringEngine
- [ ] Risk propagation nel calcolo
- [ ] Penalità per missing dependencies (connessioni critiche senza dipendenza)

---

## Asset Review e Maintenance Reminder System

### Requisiti

Implementare un sistema di reminder periodico per la verifica degli asset:
- **Review Periodica**: Promemoria per verificare asset non aggiornati da X mesi
- **Conferma Stato**: Chiedere conferma che l'asset sia ancora valido/aggiornato
- **Dashboard Review**: Lista asset che necessitano review
- **Configurabile**: Periodo di review configurabile (default: 6 mesi)

### Obiettivi

1. Mantenere i dati degli asset aggiornati
2. Identificare asset obsoleti o non più in uso
3. Promuovere best practice di manutenzione dati
4. Ridurre dati stale nel sistema

### Modello Asset - Estensioni

```python
class Asset(Base):
    # ... campi esistenti ...
    
    # Review e Maintenance
    last_review_date = Column(DateTime, nullable=True)
    # Data ultima verifica/conferma dello stato dell'asset
    
    next_review_date = Column(DateTime, nullable=True)
    # Data prossima review calcolata (last_review_date + review_interval)
    
    review_status = Column(String(20), default="pending")
    # Valori: 'pending', 'reviewed', 'overdue', 'skipped'
    
    review_notes = Column(Text, nullable=True)
    # Note della review (es: "Nessun cambiamento", "Aggiornato firmware")
    
    # Configurazione review (può essere ereditata da tenant/site)
    review_interval_months = Column(Integer, default=6)
    # Intervallo in mesi tra le review (default: 6)
```

### Configurazione a Livello Tenant/Site

```python
class Tenant(Base):
    # ... campi esistenti ...
    
    default_review_interval_months = Column(Integer, default=6)
    # Intervallo di review di default per tutti gli asset del tenant

class Site(Base):
    # ... campi esistenti ...
    
    review_interval_months = Column(Integer, nullable=True)
    # Intervallo di review specifico per il site (override del tenant)
```

### Servizio AssetReviewService

```python
class AssetReviewService:
    def calculate_next_review_date(self, asset: Asset) -> datetime:
        """
        Calcola la prossima data di review basata su:
        - last_review_date o updated_at (se last_review_date è None)
        - review_interval_months dell'asset, site o tenant
        """
        pass
    
    def get_assets_due_for_review(
        self, 
        tenant_id: UUID,
        days_ahead: int = 30
    ) -> List[Asset]:
        """
        Trova asset che necessitano review:
        - Asset con next_review_date entro 'days_ahead' giorni
        - Asset con review_status = 'overdue'
        """
        pass
    
    def get_overdue_assets(self, tenant_id: UUID) -> List[Asset]:
        """
        Asset con review scaduta (next_review_date < oggi)
        """
        pass
    
    def mark_as_reviewed(
        self, 
        asset_id: UUID, 
        reviewed_by: UUID,
        notes: str = None,
        next_review_override: datetime = None
    ) -> Asset:
        """
        Marca asset come reviewato:
        - Aggiorna last_review_date
        - Calcola next_review_date
        - Aggiorna review_status
        """
        pass
    
    def skip_review(
        self,
        asset_id: UUID,
        skipped_by: UUID,
        reason: str,
        next_review_date: datetime
    ) -> Asset:
        """
        Salta la review (es: asset in manutenzione)
        """
        pass
```

### Calcolo Automatico Next Review Date

**Logica:**
1. Se `last_review_date` esiste → `next_review_date = last_review_date + review_interval_months`
2. Se `last_review_date` è None → usa `updated_at` come base
3. Se anche `updated_at` è molto vecchio → usa `created_at`
4. `review_interval_months` viene preso da:
   - Asset (se specificato)
   - Site (se specificato)
   - Tenant (default)

### API Endpoints

```python
# Review Management
GET /api/assets/{id}/review-status
# Restituisce: last_review_date, next_review_date, review_status, days_until_review

POST /api/assets/{id}/review
# Marca asset come reviewato
# Body: {notes: str, next_review_override: datetime (opzionale)}

POST /api/assets/{id}/review/skip
# Salta review
# Body: {reason: str, next_review_date: datetime}

# Review Dashboard
GET /api/assets/review/due
# Query params: ?days_ahead=30&status=pending|overdue
# Lista asset che necessitano review

GET /api/assets/review/overdue
# Lista asset con review scaduta

GET /api/assets/review/upcoming
# Query params: ?days=30
# Lista asset con review in arrivo nei prossimi N giorni

# Bulk Review
POST /api/assets/review/bulk
# Marca multipli asset come reviewati
# Body: {asset_ids: List[UUID], notes: str}

# Configuration
GET /api/tenant/review-config
# Configurazione review del tenant

PUT /api/tenant/review-config
# Aggiorna configurazione review
# Body: {default_review_interval_months: int}
```

### UI

#### Dashboard - Nuova Sezione "Asset Review"

- **Widget "Review Due"**: 
  - Numero asset che necessitano review
  - Breakdown per status (pending, overdue)
  - Link a lista dettagliata

- **Widget "Overdue Reviews"**:
  - Lista asset con review scaduta
  - Giorni di ritardo
  - Quick action: "Mark as Reviewed"

- **Widget "Upcoming Reviews"**:
  - Asset con review in arrivo (prossimi 30 giorni)
  - Timeline visuale

#### Asset List - Filtri e Colonne

- **Colonna "Review Status"**:
  - Badge colorato: pending (giallo), reviewed (verde), overdue (rosso)
  - Mostra giorni fino alla prossima review o giorni di ritardo

- **Filtri**:
  - `review_status`: pending, reviewed, overdue
  - `review_due_in_days`: asset con review entro X giorni
  - `overdue`: solo asset con review scaduta

#### Asset Detail - Sezione "Review"

- **Review Status Card**:
  - Ultima review: data e utente
  - Prossima review: data calcolata
  - Status: badge colorato
  - Note della review

- **Quick Actions**:
  - Button "Mark as Reviewed" (se review è dovuta)
  - Button "Skip Review" (con motivo)
  - Button "Update Review Date"

- **Review History** (opzionale, futuro):
  - Timeline delle review passate

#### Pagina Dedicata "Asset Review"

- **Lista Asset da Revieware**:
  - Tab "Overdue" (scadute)
  - Tab "Due Soon" (prossime)
  - Tab "All Pending" (tutte in attesa)

- **Bulk Actions**:
  - Seleziona multipli asset
  - "Mark All as Reviewed"
  - "Update Review Interval"

- **Filtri Avanzati**:
  - Per site, area, location
  - Per asset type
  - Per giorni fino alla review

### Notifiche e Reminder

#### Notifiche In-App

- Banner/Toast quando ci sono asset con review scaduta
- Notifica quando un asset si avvicina alla data di review (es: 7 giorni prima)

#### Email Reminder (Futuro)

- Email settimanale con lista asset che necessitano review
- Email quando asset raggiunge data di review
- Configurabile per tenant

### Integrazione con Audit Trail

Tutte le azioni di review vengono tracciate:
- `review_marked`: Asset marcato come reviewato
- `review_skipped`: Review saltata
- `review_interval_updated`: Intervallo di review modificato

### Esempio di Flusso

**Scenario: Asset non aggiornato da 6 mesi**

1. Sistema calcola `next_review_date` = `updated_at` + 6 mesi
2. Se `next_review_date` < oggi → `review_status = 'overdue'`
3. Asset appare in Dashboard "Overdue Reviews"
4. Utente apre Asset Detail → vede banner "Review Overdue"
5. Utente clicca "Mark as Reviewed"
6. Sistema aggiorna:
   - `last_review_date` = oggi
   - `next_review_date` = oggi + 6 mesi
   - `review_status` = 'reviewed'
7. Asset scompare dalla lista "Overdue"

### Configurazione Default

- **Review Interval**: 6 mesi (configurabile)
- **Overdue Threshold**: 0 giorni (immediato)
- **Reminder Ahead**: 30 giorni (notifica 30 giorni prima)
- **Auto-calculation**: Basato su `updated_at` se `last_review_date` è None

### Fasi di Implementazione

#### Fase 1: Modello Base
- [ ] Aggiungere campi review al modello Asset
- [ ] Aggiungere configurazione a Tenant/Site
- [ ] Migrazione database

#### Fase 2: Servizio Base
- [ ] AssetReviewService con calcolo date
- [ ] Query per asset da revieware
- [ ] Mark as reviewed

#### Fase 3: API
- [ ] Endpoints review management
- [ ] Endpoints review dashboard
- [ ] Bulk operations

#### Fase 4: UI Base
- [ ] Widget Dashboard
- [ ] Sezione Review in Asset Detail
- [ ] Filtri in Asset List

#### Fase 5: Pagina Dedicata
- [ ] Pagina "Asset Review"
- [ ] Bulk actions
- [ ] Filtri avanzati

#### Fase 6: Notifiche (Futuro)
- [ ] In-app notifications
- [ ] Email reminders
- [ ] Configurazione notifiche

### Note Future: Scoping Esteso Asset

Per il futuro, considerare aggiungere campi per:
- **Physical Access**: Chiavi fisiche necessarie per accensione/spegnimento
- **Data Movement**: Se l'asset sposta dati
- **Read-Only**: Se l'asset è in modalità read-only
- **Connection Loss Behavior**: Cosa succede se perde connessione
- Altri attributi operativi rilevanti

Questi possono essere aggiunti come:
- Campi dedicati nel modello Asset
- Custom fields (già presente)
- Asset attributes (nuovo modello per attributi estesi)

---

## Enterprise Authentication (EntraID / Azure AD)

### Requisiti

Implementare autenticazione enterprise con Microsoft EntraID (Azure AD):
- **Single Sign-On (SSO)**: Autenticazione integrata con EntraID
- **Setup Semplificato**: Processo "Connect" che configura automaticamente l'Enterprise App in Microsoft 365
- **User Provisioning**: Collegamento automatico utenti EntraID con utenti Industrace
- **Fallback**: Mantenere autenticazione locale come fallback

### Obiettivi

1. Semplificare l'accesso per organizzazioni enterprise
2. Ridurre la gestione delle password
3. Integrazione seamless con Microsoft 365
4. Setup guidato e automatico

### Approccio Proposto

**Workflow "Connect":**
1. Utente clicca "Connect with Microsoft 365" in Setup/Configuration
2. Redirect a Microsoft 365 per autorizzazione
3. Sistema crea automaticamente Enterprise App in Azure AD
4. Configurazione automatica di OAuth2/OIDC
5. Mapping utenti EntraID → Utenti Industrace
6. Test connessione e completamento setup

### Componenti Necessari

#### Backend
- OAuth2/OIDC client per EntraID
- Endpoint per callback OAuth
- User provisioning service
- Configurazione tenant per SSO

#### Frontend
- Setup wizard per "Connect with Microsoft 365"
- Login page con opzione SSO
- Gestione sessioni SSO

### Librerie Consigliate

- **Python**: `msal` (Microsoft Authentication Library)
- **Vue.js**: `@azure/msal-browser` o `@microsoft/microsoft-graph-client`

### Configurazione

```python
class TenantSSOConfig(Base):
    __tablename__ = "tenant_sso_config"
    
    tenant_id = Column(UUID, ForeignKey("tenants.id"), primary_key=True)
    enabled = Column(Boolean, default=False)
    
    # EntraID Configuration
    client_id = Column(String(255))  # Azure AD App ID
    client_secret = Column(String(255), nullable=True)  # Encrypted
    tenant_domain = Column(String(255))  # tenant.onmicrosoft.com
    
    # OAuth2/OIDC
    authorization_endpoint = Column(String(500))
    token_endpoint = Column(String(500))
    userinfo_endpoint = Column(String(500))
    
    # User Mapping
    email_domain = Column(String(100))  # Auto-map users by domain
    auto_provision = Column(Boolean, default=True)  # Auto-create users
    
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### API Endpoints

```python
# SSO Setup
GET /api/sso/connect
# Inizia processo di connessione, redirect a Microsoft 365

GET /api/sso/callback
# Callback da Microsoft 365 dopo autorizzazione

POST /api/sso/configure
# Configurazione manuale (alternativa a Connect)

GET /api/sso/status
# Stato configurazione SSO per tenant

POST /api/sso/test
# Test connessione SSO

DELETE /api/sso/disconnect
# Disconnette SSO, torna ad autenticazione locale

# Login
GET /api/auth/login/sso
# Redirect a Microsoft 365 per login

GET /api/auth/login/sso/callback
# Callback dopo login SSO
```

### UI

#### Setup Wizard - "Connect with Microsoft 365"

1. **Step 1: Introduction**
   - Spiega cosa fa il "Connect"
   - Benefici SSO
   - Cosa verrà configurato

2. **Step 2: Microsoft 365 Authorization**
   - Button "Connect with Microsoft 365"
   - Redirect a Microsoft 365
   - Richiesta permessi per creare Enterprise App

3. **Step 3: Configuration**
   - Mostra configurazione creata
   - Opzioni:
     - Auto-provision users
     - Email domain mapping
     - Default role for new users

4. **Step 4: Test**
   - Test connessione
   - Test login con account di prova
   - Conferma completamento

#### Login Page

- **Opzione SSO**: Button "Sign in with Microsoft 365"
- **Fallback**: Link "Sign in with email/password" (se SSO non configurato o fallback abilitato)

### User Provisioning

**Auto-provisioning:**
- Quando utente EntraID fa login per la prima volta
- Crea automaticamente utente in Industrace
- Mapping basato su email
- Assegna ruolo default (configurabile)

**Mapping:**
- Email → Email
- Display Name → Name
- EntraID User ID → External ID (per tracking)

### Sicurezza

- Client Secret encrypted nel database
- Token refresh automatico
- Session management sicuro
- Audit log per login SSO

### Note Implementazione

- **Setup Automatico**: Richiede permessi admin in Azure AD per creare Enterprise App
- **Fallback**: Mantenere sempre autenticazione locale come opzione
- **Multi-tenant**: Ogni tenant può avere la propria configurazione SSO
- **Testing**: Ambiente di test con Azure AD sandbox

### Fasi di Implementazione

#### Fase 1: Setup Base
- [ ] Integrazione OAuth2/OIDC con EntraID
- [ ] Modello TenantSSOConfig
- [ ] Endpoint callback base

#### Fase 2: Connect Wizard
- [ ] Setup wizard UI
- [ ] Auto-configurazione Enterprise App
- [ ] Test connessione

#### Fase 3: Login SSO
- [ ] Login page con opzione SSO
- [ ] User provisioning
- [ ] Session management

#### Fase 4: User Management
- [ ] Mapping utenti
- [ ] Sync utenti (opzionale)
- [ ] Gestione ruoli

#### Fase 5: Advanced
- [ ] Multi-domain support
- [ ] Conditional access
- [ ] Audit logging avanzato

---

## Syslog Server e SIEM Forwarding

### Overview

Implementare un sistema syslog completo che:

- **Log Collection**: Raccoglie log da asset industriali via syslog (UDP/TCP/TLS)
- **Log Storage**: Archivia e mantiene tutti i log nel sistema per analisi e correlazione
- **SIEM Forwarding**: Forwarda log a SIEM esterni in modo nativo (Splunk, QRadar, ArcSight, etc.)
- **BAS/CS Support**: Base per Behavioral Alerting Sets for Control Systems - analisi comportamentale e rilevamento anomalie

**Visione**: Industrace diventa un log collector centralizzato per l'ambiente industriale, mantenendo i log per analisi avanzate (BAS/CS) e forwardandoli a SIEM esterni per integrazione con security operations esistenti.

**Differenza chiave rispetto all'approccio iniziale**: 
- **Prima**: Solo invio di eventi Industrace a SIEM esterni
- **Ora**: Industrace raccoglie, mantiene e forwarda log da asset industriali, diventando un hub centrale per log management e analisi comportamentale

### Obiettivi

1. **Centralized Log Collection**: Un unico punto di raccolta per tutti i log industriali
2. **Dual Purpose**: Log mantenuti per analisi BAS/CS + forwardati a SIEM esistenti
3. **Flexibility**: Supporto multipli SIEM, formati diversi, filtri configurabili
4. **BAS/CS Ready**: Base dati completa per analisi comportamentale avanzata
5. **Integration**: Integrazione nativa con asset management e risk assessment
6. Supportare analisi forense e troubleshooting
7. Rilevare anomalie e security events
8. Correlare log con asset nel sistema

### Architettura

```
Asset (Remote) → Syslog → Industrace Syslog Server → Log Storage → Analysis/Alerting
                                                      ↓
                                              SIEM Forwarding (Splunk, QRadar, etc.)
                                                      ↓
                                              BAS/CS Analysis (Behavioral Detection)
```

### Componenti

#### 1. Syslog Server (Collector)

- **UDP/TCP Syslog Server**: Riceve log su porta standard (514 UDP, 514 TCP)
- **TLS Support**: Supporto per syslog over TLS (RFC 5425)
- **Parser**: Parsing di vari formati syslog (RFC 3164, RFC 5424)
- **High-Volume Handling**: Gestione di alto volume di log con buffer e queue
- **Reliable Delivery**: Meccanismi per garantire delivery (acknowledgment, retry)
- **Rate Limiting**: Protezione da flood

#### 2. Log Storage

- **Database**: Tabella dedicata per log syslog
- **Retention**: Policy di retention configurabile
- **Indexing**: Indici per ricerca veloce
- **Archiving**: Archiviazione log vecchi (opzionale)

#### 3. Asset Correlation

- **IP-based**: Correla log a asset tramite IP source
- **Hostname-based**: Correla tramite hostname nel log
- **Manual Mapping**: Mapping manuale IP/Hostname → Asset

### Modello Dati

```python
class SyslogEntry(Base):
    __tablename__ = "syslog_entries"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    
    # Syslog Fields
    timestamp = Column(DateTime, nullable=False, index=True)
    facility = Column(Integer)  # 0-23
    severity = Column(Integer)  # 0-7
    hostname = Column(String(255), index=True)
    source_ip = Column(String(45), index=True)  # IPv4/IPv6
    tag = Column(String(50))
    message = Column(Text, nullable=False)
    
    # Parsed Fields
    program = Column(String(100))  # Program name
    pid = Column(Integer)  # Process ID
    structured_data = Column(JSONB)  # RFC 5424 structured data
    
    # Asset Correlation
    asset_id = Column(UUID, ForeignKey("assets.id"), nullable=True)
    # Auto-correlato tramite IP o hostname
    
    # Metadata
    raw_message = Column(Text)  # Original syslog message
    protocol = Column(String(10))  # UDP, TCP, TLS
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    asset = relationship("Asset", back_populates="syslog_entries")
    tenant = relationship("Tenant")
```

### SIEM Forwarding Configuration

```python
class SyslogForwardingConfig(Base):
    __tablename__ = "syslog_forwarding_configs"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    
    # SIEM Configuration
    siem_type = Column(String(50), nullable=False)  # 'splunk', 'qradar', 'arcsight', 'generic_syslog'
    enabled = Column(Boolean, default=True)
    
    # Connection
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    protocol = Column(String(10), default="tcp")  # 'udp', 'tcp', 'tls'
    
    # Authentication
    api_key = Column(String(500), nullable=True)  # Encrypted
    username = Column(String(255), nullable=True)
    password_encrypted = Column(String(500), nullable=True)  # Encrypted
    
    # Filtering
    filters = Column(JSONB, nullable=True)  # Filtri per severity, facility, asset, etc.
    forward_all = Column(Boolean, default=True)  # Forward tutti i log o solo filtrati
    
    # Format
    format = Column(String(50), default="syslog")  # 'syslog', 'json', 'cef', 'leef'
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_forward_at = Column(DateTime, nullable=True)
    last_forward_count = Column(Integer, nullable=True)
    last_forward_error = Column(Text, nullable=True)
```

### Asset Correlation Rules

```python
class SyslogCorrelationRule(Base):
    __tablename__ = "syslog_correlation_rules"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"))
    
    # Rule Type
    rule_type = Column(String(50))  # 'ip', 'hostname', 'pattern'
    
    # Matching
    match_value = Column(String(255))  # IP, hostname, o pattern regex
    asset_id = Column(UUID, ForeignKey("assets.id"))
    
    # Priority (se più regole match)
    priority = Column(Integer, default=0)
    
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime)
```

### API Endpoints

```python
# Syslog Server Configuration
GET /api/syslog/config
# Configurazione syslog server (porta, protocollo, etc.)

PUT /api/syslog/config
# Aggiorna configurazione syslog server
# Body: {port: int, protocol: 'udp'|'tcp'|'tls', enabled: bool}

# SIEM Forwarding
GET /api/syslog/forwarding
# Lista configurazioni forwarding

POST /api/syslog/forwarding
# Crea nuova configurazione forwarding

PUT /api/syslog/forwarding/{id}
# Aggiorna configurazione forwarding

DELETE /api/syslog/forwarding/{id}
# Elimina configurazione forwarding

POST /api/syslog/forwarding/{id}/test
# Test connessione SIEM

GET /api/syslog/forwarding/{id}/status
# Status ultimo forwarding

# Log Query
GET /api/syslog/entries
# Query params: 
#   ?asset_id={id}
#   &severity={0-7}
#   &from={datetime}
#   &to={datetime}
#   &search={text}
#   &limit={n}

GET /api/syslog/entries/{id}
# Dettaglio log entry

# Asset Correlation
GET /api/syslog/correlation-rules
# Lista regole di correlazione

POST /api/syslog/correlation-rules
# Crea regola di correlazione

PUT /api/syslog/correlation-rules/{id}
# Aggiorna regola

DELETE /api/syslog/correlation-rules/{id}
# Elimina regola

POST /api/syslog/correlate
# Correla manualmente log entry a asset
# Body: {log_id: UUID, asset_id: UUID}

# Statistics
GET /api/syslog/stats
# Statistiche: total logs, by severity, by asset, etc.
```

### UI

#### Syslog Dashboard

- **Log Viewer**: 
  - Tabella log con filtri
  - Ricerca full-text
  - Filtri per severity, facility, asset, time range
  
- **Statistics**:
  - Log per severity (grafico)
  - Top assets per volume log
  - Log trends (timeline)

- **Asset Correlation**:
  - Lista log non correlati
  - Auto-correlation suggestions
  - Manual correlation tool

#### Asset Detail - Tab "Syslog"

- **Recent Logs**: Ultimi log per questo asset
- **Log Statistics**: Statistiche log per asset
- **Correlation Status**: Se asset è configurato per syslog

#### Configuration Page

- **Syslog Server Settings**:
  - Porta UDP/TCP
  - TLS configuration
  - Log retention policy
  
- **SIEM Forwarding**:
  - Lista SIEM configurati
  - Status forwarding
  - Test connection
  - Forwarding statistics
  - Port configuration
  - Protocol selection (UDP/TCP/TLS)
  - Enable/disable
  
- **Correlation Rules**:
  - Lista regole
  - Create/edit/delete rules
  - Test rules

### Alerting (Futuro)

- Pattern matching nei log
- Alert su eventi specifici
- Integration con notification system

### Fasi di Implementazione

### Architettura Log Flow

```
Asset Industriali
    ↓ (syslog UDP/TCP/TLS)
Industrace Syslog Server
    ↓
┌─────────────────────────────────────┐
│  Log Storage (PostgreSQL)           │
│  - Parsing e normalizzazione        │
│  - Correlation con asset           │
│  - Retention policy                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  BAS/CS Analysis                    │
│  - Behavioral pattern detection   │
│  - Anomaly detection               │
│  - Alert generation                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  SIEM Forwarding                    │
│  - Splunk HEC                       │
│  - QRadar                           │
│  - Generic syslog (UDP/TCP)        │
│  - Format conversion (JSON/CEF)    │
└─────────────────────────────────────┘
```

### Vantaggi Architettura

1. **Centralized Log Collection**: Un unico punto di raccolta per tutti i log industriali
2. **Dual Purpose**: Log mantenuti per analisi BAS/CS + forwardati a SIEM esistenti
3. **Flexibility**: Supporto multipli SIEM, formati diversi, filtri configurabili
4. **BAS/CS Ready**: Base dati completa per analisi comportamentale avanzata
5. **Integration**: Integrazione nativa con asset management e risk assessment

### Fasi di Implementazione

#### Fase 1: Syslog Server Base
- [ ] UDP syslog receiver
- [ ] TCP syslog receiver
- [ ] TLS syslog support (RFC 5425)
- [ ] Log parsing (RFC 3164, RFC 5424)
- [ ] Log storage in database (con partizionamento)
- [ ] Asset correlation automatica (IP/MAC matching)
- [ ] Basic correlation rules
- [ ] Log retention policy
- [ ] High-volume handling (queue, buffering)

#### Fase 2: SIEM Forwarding
- [ ] Forwarding configuration model (SyslogForwardingConfig)
- [ ] Splunk HEC (HTTP Event Collector) integration
- [ ] QRadar integration (syslog over TCP/TLS)
- [ ] Generic syslog forwarding (UDP/TCP/TLS)
- [ ] Format conversion (JSON, CEF, LEEF, raw syslog)
- [ ] Filtering and routing (per severity, facility, asset, etc.)
- [ ] Retry and error handling
- [ ] Forwarding status monitoring
- [ ] Batch forwarding per performance
- [ ] Encryption per credenziali SIEM

#### Fase 3: Asset Correlation
- [ ] IP-based correlation
- [ ] Hostname-based correlation
- [ ] Correlation rules
- [ ] Manual mapping UI

#### Fase 4: UI Base
- [ ] Log viewer
- [ ] Filtri e ricerca
- [ ] Asset correlation UI
- [ ] SIEM forwarding configuration UI
- [ ] Forwarding status dashboard

#### Fase 5: BAS/CS Foundation
- [ ] Event tagging system (già progettato)
- [ ] Behavioral pattern detection
- [ ] Anomaly detection
- [ ] Alert generation
- [ ] Integration con risk assessment
- [ ] Dashboard BAS/CS

#### Fase 6: Advanced
- [ ] Log retention policies avanzate
- [ ] Statistics e analytics avanzate
- [ ] Pattern matching avanzato
- [ ] Alert rules configurabili
- [ ] Notifications integration

### Note Implementazione

#### Performance Considerations

- **Volume Log**: Asset industriali possono generare migliaia di log/secondo
- **Partizionamento**: Partizionare `syslog_entries` per data (mensile/trimestrale)
- **Indexing**: Indici su `timestamp`, `asset_id`, `severity`, `facility`
- **Archiving**: Archiviare log vecchi (> retention period) su storage secondario
- **Forwarding Queue**: Queue asincrona per forwarding a SIEM (non bloccare collection)

#### SIEM Integration Details

**Splunk HEC**:
- Endpoint: `https://splunk-server:8088/services/collector/event`
- Format: JSON
- Authentication: Bearer token
- Batch: Multiple events per request

**QRadar**:
- Protocol: Syslog over TCP/TLS
- Format: CEF (Common Event Format) o LEEF
- Port: 514 (TCP) o 6514 (TLS)

**Generic Syslog**:
- Protocol: UDP/TCP/TLS
- Format: RFC 5424 o custom
- Supporto per multipli destinatari

#### Security Considerations

- **TLS**: Supporto TLS per syslog collection e forwarding
- **Encryption**: Credenziali SIEM encrypted nel database
- **Access Control**: Solo admin possono configurare forwarding
- **Audit**: Log di tutte le configurazioni forwarding
- **Network Isolation**: Syslog server può essere su network isolato

---

## Change Management Review

### Requisiti

Ricontrollare e migliorare il sistema di change management sugli asset:
- **Change Tracking**: Verificare che tutti i cambiamenti siano tracciati
- **Change Approval**: Workflow di approvazione per cambiamenti critici
- **Change History**: Storico completo e consultabile
- **Change Impact**: Analisi impatto dei cambiamenti
- **Rollback**: Possibilità di rollback cambiamenti

### Aree da Rivedere

1. **Audit Trail Esistente**
   - Verificare completezza del tracking
   - Assicurarsi che tutti i campi modificati siano tracciati
   - Verificare performance con molti cambiamenti

2. **Change Workflow**
   - Approvazione per cambiamenti critici (es: configurazione sicurezza)
   - Notifiche per cambiamenti importanti
   - Change requests vs. direct changes

3. **Change History UI**
   - Migliorare visualizzazione timeline
   - Filtri avanzati
   - Export change history

4. **Change Impact Analysis**
   - Analisi impatto prima di applicare cambiamento
   - Warning per cambiamenti rischiosi
   - Dependency check

5. **Rollback Capability**
   - Snapshot prima di cambiamenti critici
   - Rollback automatico o manuale
   - History di rollback

### Componenti da Verificare

- `audit_log.py` - Sistema di audit esistente
- `AssetTimelineTab.vue` - UI timeline cambiamenti
- Change tracking in tutti i router assets
- Performance con molti audit log entries

### TODO

- [ ] Audit completo di sistema change management esistente
- [ ] Identificare gap e miglioramenti necessari
- [ ] Progettare workflow di approvazione
- [ ] Progettare sistema di rollback
- [ ] Migliorare UI change history
- [ ] Implementare change impact analysis

---

## BAS/CS™ Integration (Behavioral Alerting Sets for Control Systems)

### Status: ON HOLD / FUTURE

**Nota**: BAS/CS™ richiede di implementare un log collector completo. Per ora questa feature è messa in pausa e verrà rivalutata in futuro quando il sistema sarà più maturo come log collector.

### Overview

Integrare il framework BAS/CS™ sviluppato da Johns Hopkins APL per standardizzare l'analisi comportamentale e il rilevamento di minacce nei sistemi di controllo industriale.

**Riferimento**: [BAS/CS™ - Johns Hopkins APL](https://www.jhuapl.edu/work/projects-and-missions/bascs)

### Obiettivi

1. **Behavior Tagging**: Normalizzare eventi da diverse fonti in comportamenti standardizzati
2. **Correlation Rules**: Identificare pattern di comportamenti sospetti attraverso regole di correlazione
3. **Threat Detection**: Rilevare minacce reali riducendo falsi positivi
4. **Integration**: Integrare con syslog server (log collection e forwarding), audit trail, e risk assessment esistente

### Concetti Chiave BAS/CS™

#### Behavior Tags

Comportamenti normalizzati che categorizzano eventi indipendentemente dal vendor:
- **PRO03**: New Command/Scripting
- **IDS04**: OT Write Command
- Altri behavior tags standard BAS/CS™

#### Correlation Alerts

Alert generati quando pattern di behavior tags vengono identificati:
- **BAS 8.2**: Unexpected OT Command and Control Shell Alert
- Altri alert standard BAS/CS™

### Architettura

```
Event Sources → Behavior Tagging → Correlation Engine → Alert Generation → Risk Assessment
     ↓              ↓                      ↓                    ↓                  ↓
  Syslog      Normalize Events      Pattern Detection    BAS/CS Alerts    Update Risk Score
  Audit Log   Vendor Agnostic       Time Windows         Severity Levels  Asset/Zone Risk
  Network     Behavior Tags         System Context       Notifications    Compliance Status
```

### Modello Dati

#### Behavior Tag Definition

```python
class BASBehaviorTag(Base):
    __tablename__ = "bas_behavior_tags"
    
    id = Column(UUID, primary_key=True)
    
    # BAS/CS Standard
    tag_code = Column(String(20), unique=True, nullable=False)  # es: "PRO03", "IDS04"
    tag_name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # 'process', 'network', 'access', etc.
    
    # Metadata
    bas_version = Column(String(20))  # Versione standard BAS/CS
    severity_base = Column(Integer)  # 0-7, severity base del tag
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

#### Event Behavior Mapping

```python
class EventBehaviorMapping(Base):
    __tablename__ = "event_behavior_mappings"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"))
    
    # Event Source
    event_source = Column(String(50))  # 'syslog', 'audit_log', 'network', 'asset'
    event_type = Column(String(100))  # Tipo evento specifico del vendor
    event_pattern = Column(Text)  # Pattern regex o matching rule
    
    # Behavior Tag
    behavior_tag_id = Column(UUID, ForeignKey("bas_behavior_tags.id"))
    
    # Mapping Configuration
    confidence = Column(Float, default=1.0)  # 0.0-1.0, confidence del mapping
    enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

#### Tagged Event

```python
class TaggedEvent(Base):
    __tablename__ = "tagged_events"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"))
    
    # Original Event
    source_event_id = Column(UUID)  # ID evento originale (syslog, audit, etc.)
    source_type = Column(String(50))  # 'syslog', 'audit_log', etc.
    
    # Behavior Tagging
    behavior_tag_id = Column(UUID, ForeignKey("bas_behavior_tags.id"))
    tagged_at = Column(DateTime, default=func.now(), index=True)
    
    # Context
    asset_id = Column(UUID, ForeignKey("assets.id"), nullable=True)
    zone_id = Column(UUID, ForeignKey("security_zones.id"), nullable=True)
    source_ip = Column(String(45))
    destination_ip = Column(String(45))
    
    # Event Details
    event_data = Column(JSONB)  # Dati originali dell'evento
    severity = Column(Integer)  # 0-7
    
    # Relationships
    behavior_tag = relationship("BASBehaviorTag")
    asset = relationship("Asset")
    zone = relationship("SecurityZone")
```

#### Correlation Rule

```python
class BASCorrelationRule(Base):
    __tablename__ = "bas_correlation_rules"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"))
    
    # BAS/CS Standard Alert
    alert_code = Column(String(20))  # es: "BAS 8.2"
    alert_name = Column(String(255))
    description = Column(Text)
    
    # Rule Definition
    behavior_tags_required = Column(JSONB)  # Lista di behavior tag codes richiesti
    # Es: ["PRO03", "IDS04"]
    
    time_window_seconds = Column(Integer, default=300)  # Finestra temporale
    system_scope = Column(String(50))  # 'same_asset', 'same_zone', 'any'
    
    # Alert Configuration
    severity = Column(Integer)  # 0-7
    auto_escalate = Column(Boolean, default=False)
    requires_manual_review = Column(Boolean, default=False)
    
    # Status
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

#### BAS Alert

```python
class BASAlert(Base):
    __tablename__ = "bas_alerts"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"))
    
    # Alert Info
    alert_code = Column(String(20))  # es: "BAS 8.2"
    alert_name = Column(String(255))
    severity = Column(Integer)  # 0-7
    status = Column(String(20))  # 'new', 'acknowledged', 'investigating', 'resolved', 'false_positive'
    
    # Triggered By
    correlation_rule_id = Column(UUID, ForeignKey("bas_correlation_rules.id"))
    triggered_events = Column(JSONB)  # Lista di tagged_event_ids che hanno triggerato l'alert
    
    # Context
    asset_id = Column(UUID, ForeignKey("assets.id"), nullable=True)
    zone_id = Column(UUID, ForeignKey("security_zones.id"), nullable=True)
    
    # Timeline
    detected_at = Column(DateTime, default=func.now(), index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Details
    description = Column(Text)
    investigation_notes = Column(Text)
    resolution_notes = Column(Text)
    
    # Relationships
    correlation_rule = relationship("BASCorrelationRule")
    asset = relationship("Asset")
    zone = relationship("SecurityZone")
```

### Servizi

#### BehaviorTaggingService

```python
class BehaviorTaggingService:
    def tag_event(self, event: Dict, source_type: str) -> List[TaggedEvent]:
        """
        Tagga un evento con behavior tags BAS/CS
        - Cerca mapping per event_type/pattern
        - Applica behavior tags corrispondenti
        - Crea TaggedEvent records
        """
        pass
    
    def tag_syslog_entry(self, syslog_entry: SyslogEntry) -> List[TaggedEvent]:
        """
        Tagga un syslog entry
        """
        pass
    
    def tag_audit_log(self, audit_log: AuditLog) -> List[TaggedEvent]:
        """
        Tagga un audit log entry
        """
        pass
```

#### BASCorrelationEngine

```python
class BASCorrelationEngine:
    def evaluate_correlation_rules(
        self, 
        tagged_events: List[TaggedEvent],
        time_window: int = 300
    ) -> List[BASAlert]:
        """
        Valuta regole di correlazione su tagged events
        - Raggruppa eventi per time window
        - Verifica pattern di behavior tags
        - Genera alert quando pattern matchano
        """
        pass
    
    def check_rule(
        self, 
        rule: BASCorrelationRule,
        events: List[TaggedEvent]
    ) -> bool:
        """
        Verifica se una regola matcha gli eventi
        """
        pass
    
    def generate_alert(
        self,
        rule: BASCorrelationRule,
        triggering_events: List[TaggedEvent]
    ) -> BASAlert:
        """
        Genera un alert BAS/CS
        """
        pass
```

### Integrazione con Componenti Esistenti

#### 1. Syslog Collection e Forwarding

```python
# Quando arriva un syslog entry
syslog_entry = receive_syslog(...)

# 1. Store nel database
store_syslog_entry(syslog_entry)

# 2. Forward a SIEM configurati (se abilitato)
if forwarding_enabled:
    forward_to_siems(syslog_entry)

# 3. Process per BAS/CS
tagged_events = behavior_tagging_service.tag_syslog_entry(syslog_entry)

# Valuta correlation rules
alerts = correlation_engine.evaluate_correlation_rules(tagged_events)

# Se alert generati, aggiorna risk score asset
if alerts:
    update_asset_risk_from_bas_alerts(asset_id, alerts)
```

#### 2. Audit Log Integration

```python
# Quando viene creato un audit log
audit_log = create_audit_log(...)

# Tagga con behavior tags (es: modifiche critiche = PRO03)
tagged_events = behavior_tagging_service.tag_audit_log(audit_log)

# Valuta correlation
alerts = correlation_engine.evaluate_correlation_rules(tagged_events)
```

#### 3. Risk Assessment Integration

```python
# Estendere CompositeRiskScoringEngine
def calculate(self, asset, language="en") -> Dict[str, Any]:
    # ... calcolo esistente ...
    
    # BAS/CS Alert factors
    bas_alerts = get_recent_bas_alerts(asset.id, days=30)
    if bas_alerts:
        high_severity_count = sum(1 for a in bas_alerts if a.severity >= 6)
        if high_severity_count > 0:
            vuln_score += min(3, high_severity_count * 0.5)
            vuln_break.append(f"BAS/CS alerts: {high_severity_count} high severity")
    
    return breakdown
```

### API Endpoints

```python
# Behavior Tags
GET /api/bas/behavior-tags
# Lista behavior tags BAS/CS standard

GET /api/bas/behavior-tags/{id}
# Dettaglio behavior tag

# Event Mapping
GET /api/bas/event-mappings
# Lista mapping eventi → behavior tags

POST /api/bas/event-mappings
# Crea nuovo mapping
# Body: {event_source, event_type, event_pattern, behavior_tag_id, confidence}

PUT /api/bas/event-mappings/{id}
# Aggiorna mapping

DELETE /api/bas/event-mappings/{id}
# Elimina mapping

# Tagged Events
GET /api/bas/tagged-events
# Query params: ?asset_id={id}&tag_id={id}&from={datetime}&to={datetime}

GET /api/bas/tagged-events/{id}
# Dettaglio tagged event

# Correlation Rules
GET /api/bas/correlation-rules
# Lista regole di correlazione

POST /api/bas/correlation-rules
# Crea regola
# Body: {alert_code, alert_name, behavior_tags_required, time_window_seconds, ...}

PUT /api/bas/correlation-rules/{id}
# Aggiorna regola

DELETE /api/bas/correlation-rules/{id}
# Elimina regola

# BAS Alerts
GET /api/bas/alerts
# Query params: ?status=new|acknowledged|resolved&severity_min={0-7}&asset_id={id}

GET /api/bas/alerts/{id}
# Dettaglio alert

POST /api/bas/alerts/{id}/acknowledge
# Marca alert come acknowledged

POST /api/bas/alerts/{id}/resolve
# Body: {resolution_notes: str, is_false_positive: bool}
# Risolve alert

POST /api/bas/alerts/{id}/investigate
# Body: {investigation_notes: str}
# Aggiunge note di investigazione

# Statistics
GET /api/bas/stats
# Statistiche: alerts per severity, per asset, trends, etc.
```

### UI

#### BAS/CS Dashboard

- **Alert Overview**:
  - Widget con alert per severity
  - Alert non acknowledged
  - Trend alert nel tempo
  
- **Behavior Tags**:
  - Lista behavior tags più frequenti
  - Grafico distribuzione tags
  
- **Correlation Rules**:
  - Lista regole attive
  - Statistiche trigger per regola

#### Alert Management Page

- **Alert List**:
  - Tab "New" (non acknowledged)
  - Tab "Investigating"
  - Tab "Resolved"
  - Tab "False Positives"
  
- **Alert Detail**:
  - Informazioni alert (BAS code, severity)
  - Eventi che hanno triggerato l'alert
  - Timeline eventi
  - Asset/Zone coinvolti
  - Azioni: Acknowledge, Investigate, Resolve, Mark False Positive

#### Asset Detail - Tab "BAS/CS"

- **Recent Alerts**: Ultimi alert BAS/CS per questo asset
- **Tagged Events**: Eventi taggati recenti
- **Behavior Tags Distribution**: Grafico behavior tags per asset
- **Risk Impact**: Come gli alert BAS/CS influenzano il risk score

#### Configuration Page

- **Behavior Tags Management**:
  - Lista behavior tags BAS/CS standard
  - Import/export tags
  
- **Event Mapping**:
  - Lista mapping eventi → tags
  - Create/edit/delete mappings
  - Test mappings
  
- **Correlation Rules**:
  - Lista regole
  - Create/edit/delete rules
  - Test rules con eventi di esempio

### Popolamento Iniziale

#### Behavior Tags Standard BAS/CS™

Importare i behavior tags standard dal framework BAS/CS:
- PRO03: New Command/Scripting
- IDS04: OT Write Command
- Altri tags standard BAS/CS™

#### Correlation Rules Standard

Implementare le correlation rules standard BAS/CS:
- BAS 8.2: Unexpected OT Command and Control Shell Alert
- Altri alert standard BAS/CS™

### Fasi di Implementazione

#### Fase 1: Behavior Tagging Base
- [ ] Modello BASBehaviorTag
- [ ] Popolamento behavior tags standard BAS/CS
- [ ] BehaviorTaggingService base
- [ ] Syslog server (UDP/TCP/TLS receiver)
- [ ] Log storage e retention
- [ ] SIEM forwarding (Splunk, QRadar, generic syslog)
- [ ] Tagging di syslog entries

#### Fase 2: Event Mapping
- [ ] Modello EventBehaviorMapping
- [ ] UI per gestire mapping
- [ ] Pattern matching engine

#### Fase 3: Correlation Engine
- [ ] Modello BASCorrelationRule
- [ ] BASCorrelationEngine
- [ ] Implementazione regole standard BAS/CS
- [ ] Alert generation

#### Fase 4: Alert Management
- [ ] Modello BASAlert
- [ ] API alert management
- [ ] UI alert dashboard
- [ ] Alert workflow (acknowledge, investigate, resolve)

#### Fase 5: Integration
- [ ] Integrazione con risk assessment
- [ ] Integrazione con Security Zones
- [ ] Notifiche alert
- [ ] Reporting

#### Fase 6: Advanced
- [ ] Machine learning per pattern detection (futuro)
- [ ] Custom correlation rules
- [ ] Alert tuning e false positive reduction

### Note

- **Standard BAS/CS™**: Seguire le specifiche ufficiali BAS/CS™ di Johns Hopkins APL
- **Vendor Agnostic**: Behavior tags normalizzano eventi da diverse fonti
- **False Positive Reduction**: BAS/CS™ è progettato per ridurre falsi positivi attraverso correlation rules sofisticate
- **Real-time**: Processing in real-time o near-real-time per detection rapida

### Riferimenti

- [BAS/CS™ - Johns Hopkins APL](https://www.jhuapl.edu/work/projects-and-missions/bascs)
- BAS/CS™ Behavior Tag Definitions
- BAS/CS™ Correlation Alert Examples

---

## Notification System (Email Notifications)

### Requisiti

Implementare un sistema di notifiche email interno per:
- **Asset Review Reminders**: Notifiche per review scadute o in scadenza
- **Risk Alerts**: Notifiche per asset ad alto rischio
- **Compliance Alerts**: Notifiche per problemi di compliance
- **System Events**: Notifiche per eventi di sistema importanti
- **Customizable**: Configurabile per tenant e utente

### Obiettivi

1. Mantenere utenti informati su eventi importanti
2. Promuovere azioni proattive (es: review asset)
3. Ridurre rischio di dati obsoleti
4. Migliorare engagement con il sistema

### Architettura

```
Event Trigger → Notification Service → Email Template → SMTP → User Email
     ↓                  ↓                    ↓            ↓          ↓
  Review Due      Check Preferences    Format Message   Send     Inbox
  Risk Change     User Subscriptions   Personalize      Queue    Action
  Compliance      Notification Rules   Localization     Retry
```

### Modello Dati

#### Notification Template

```python
class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=True)  # NULL = system-wide
    
    # Template Info
    template_code = Column(String(50), unique=True, nullable=False)  # es: "asset_review_due"
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Email Content
    subject_template = Column(String(500), nullable=False)  # Template string con variabili
    body_template_html = Column(Text, nullable=False)  # HTML template
    body_template_text = Column(Text)  # Plain text fallback
    
    # Variables
    variables = Column(JSONB)  # Lista variabili disponibili: ["asset_name", "days_until_review", etc.]
    
    # Status
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

#### Notification Preference

```python
class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    
    # Notification Type
    notification_type = Column(String(50), nullable=False)  # 'asset_review', 'risk_alert', etc.
    
    # Channels
    email_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)  # Per futuro
    
    # Frequency
    frequency = Column(String(20), default="immediate")  # 'immediate', 'daily_digest', 'weekly_digest'
    
    # Filters
    severity_min = Column(Integer, nullable=True)  # Solo alert con severity >= questo
    filters = Column(JSONB)  # Filtri aggiuntivi (es: solo asset di certi site)
    
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # Unique constraint: user + notification_type
    __table_args__ = (
        UniqueConstraint('user_id', 'notification_type', name='uq_user_notification_type'),
    )
```

#### Notification Queue

```python
class NotificationQueue(Base):
    __tablename__ = "notification_queue"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    
    # Recipient
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    email = Column(String(255), nullable=False)
    
    # Notification
    notification_type = Column(String(50), nullable=False)
    template_id = Column(UUID, ForeignKey("notification_templates.id"))
    
    # Content (rendered)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text)
    
    # Context
    context_data = Column(JSONB)  # Dati contestuali (asset_id, etc.)
    
    # Status
    status = Column(String(20), default="pending")  # 'pending', 'sent', 'failed', 'cancelled'
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Scheduling
    scheduled_for = Column(DateTime, default=func.now(), index=True)
    created_at = Column(DateTime, default=func.now())
```

#### Notification Log

```python
class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    
    # Notification Info
    notification_type = Column(String(50), nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    
    # Result
    status = Column(String(20))  # 'sent', 'failed', 'skipped'
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Context
    context_data = Column(JSONB)
    
    created_at = Column(DateTime, default=func.now(), index=True)
```

### Servizi

#### NotificationService

```python
class NotificationService:
    def send_notification(
        self,
        user_id: UUID,
        notification_type: str,
        context_data: Dict,
        scheduled_for: datetime = None
    ) -> NotificationQueue:
        """
        Crea e accoda una notifica
        - Verifica preferenze utente
        - Renderizza template
        - Aggiunge a coda
        """
        pass
    
    def send_asset_review_reminder(
        self,
        asset_id: UUID,
        days_until_review: int = 0
    ):
        """
        Invia reminder per asset review
        - Trova owner/point-of-contact dell'asset
        - Invia notifica a ciascuno
        """
        pass
    
    def send_risk_alert(
        self,
        asset_id: UUID,
        risk_score: float,
        risk_level: str
    ):
        """
        Invia alert per asset ad alto rischio
        """
        pass
    
    def send_bulk_notifications(
        self,
        notification_type: str,
        context_list: List[Dict],
        user_ids: List[UUID] = None
    ):
        """
        Invia notifiche multiple (es: digest giornaliero)
        """
        pass
```

#### EmailService

```python
class EmailService:
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str = None
    ) -> bool:
        """
        Invia email via SMTP
        """
        pass
    
    def process_queue(self, batch_size: int = 50):
        """
        Processa coda notifiche
        - Prende notifiche pending
        - Invia email
        - Aggiorna status
        - Log risultati
        """
        pass
```

### Template Email

#### Asset Review Due

**Subject**: `Asset Review Due: {{asset_name}}`

**Body HTML**:
```html
<p>Dear {{user_name}},</p>
<p>The following asset requires review:</p>
<ul>
  <li><strong>Asset:</strong> {{asset_name}}</li>
  <li><strong>Site:</strong> {{site_name}}</li>
  <li><strong>Last Review:</strong> {{last_review_date}}</li>
  <li><strong>Days Overdue:</strong> {{days_overdue}}</li>
</ul>
<p><a href="{{asset_url}}">Review Asset</a></p>
```

#### Asset Review Upcoming

**Subject**: `Asset Review Upcoming: {{asset_name}} ({{days_until_review}} days)`

#### Risk Alert

**Subject**: `High Risk Alert: {{asset_name}} (Risk Score: {{risk_score}})`

**Body HTML**:
```html
<p>Dear {{user_name}},</p>
<p>The following asset has a high risk score:</p>
<ul>
  <li><strong>Asset:</strong> {{asset_name}}</li>
  <li><strong>Risk Score:</strong> {{risk_score}} ({{risk_level}})</li>
  <li><strong>Site:</strong> {{site_name}}</li>
</ul>
<p><a href="{{asset_url}}">View Asset Details</a></p>
```

### Configurazione SMTP

```python
class TenantSMTPConfig(Base):
    __tablename__ = "tenant_smtp_config"
    
    tenant_id = Column(UUID, ForeignKey("tenants.id"), primary_key=True)
    
    # SMTP Settings
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, default=587)
    smtp_use_tls = Column(Boolean, default=True)
    smtp_username = Column(String(255))
    smtp_password = Column(String(255))  # Encrypted
    
    # Email Settings
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255), default="Industrace")
    reply_to = Column(String(255), nullable=True)
    
    # Status
    enabled = Column(Boolean, default=True)
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

**Nota**: Esiste già `TenantSMTPConfig` nel sistema, verificare se può essere riutilizzato.

### API Endpoints

```python
# Notification Preferences
GET /api/notifications/preferences
# Lista preferenze notifiche dell'utente corrente

PUT /api/notifications/preferences/{id}
# Aggiorna preferenza
# Body: {email_enabled: bool, frequency: str, filters: dict}

POST /api/notifications/preferences
# Crea nuova preferenza

# Notification Queue (Admin)
GET /api/notifications/queue
# Query params: ?status=pending|sent|failed&limit={n}
# Lista notifiche in coda

POST /api/notifications/queue/{id}/retry
# Riprova invio notifica fallita

DELETE /api/notifications/queue/{id}
# Cancella notifica dalla coda

# Notification Log
GET /api/notifications/logs
# Query params: ?user_id={id}&type={type}&from={date}&to={date}
# Storico notifiche inviate

# Test Notification
POST /api/notifications/test
# Body: {template_code: str, email: str}
# Invia email di test

# SMTP Configuration
GET /api/tenant/smtp-config
# Configurazione SMTP tenant

PUT /api/tenant/smtp-config
# Aggiorna configurazione SMTP
# Body: {smtp_host, smtp_port, smtp_username, smtp_password, from_email, ...}

POST /api/tenant/smtp-config/test
# Test connessione SMTP
```

### UI

#### User Settings - Notifications Tab

- **Notification Preferences**:
  - Lista tipi di notifiche disponibili
  - Toggle email/in-app per ciascun tipo
  - Frequency selection (immediate, daily digest, weekly digest)
  - Filtri avanzati (es: solo asset di certi site)
  
- **Email Preferences**:
  - Email address (prelevato da profilo utente)
  - Test email button

#### Admin - Notification Management

- **SMTP Configuration**:
  - Form configurazione SMTP
  - Test connection button
  - Verifica configurazione
  
- **Notification Queue**:
  - Lista notifiche pending/sent/failed
  - Retry failed notifications
  - View notification details
  
- **Notification Logs**:
  - Storico notifiche inviate
  - Filtri per user, type, date
  - Export logs

#### Template Management (Admin)

- **Email Templates**:
  - Lista template disponibili
  - Edit template (subject, body HTML/text)
  - Preview template
  - Variables documentation

### Integrazione con Asset Review

```python
# Quando asset review è dovuta
def check_asset_reviews():
    overdue_assets = get_overdue_assets()
    for asset in overdue_assets:
        # Trova owners e points-of-contact
        owners = get_asset_owners(asset.id)
        points_of_contact = get_asset_points_of_contact(asset.id)
        
        # Invia notifica a ciascuno
        for user in owners + points_of_contact:
            notification_service.send_asset_review_reminder(
                asset_id=asset.id,
                user_id=user.id,
                days_until_review=0  # overdue
            )

# Quando asset review si avvicina (es: 7 giorni prima)
def check_upcoming_reviews():
    upcoming_assets = get_assets_review_due_in_days(7)
    # ... stesso processo
```

### Scheduled Tasks

#### Background Worker

```python
# Cron job o scheduled task
@schedule.every(1).hours
def process_notification_queue():
    email_service.process_queue(batch_size=50)

@schedule.daily(at="09:00")
def check_asset_reviews():
    # Controlla asset con review scaduta o in scadenza
    check_asset_reviews()
    check_upcoming_reviews()

@schedule.daily(at="08:00")
def send_daily_digest():
    # Invia digest giornaliero a utenti con preferenza "daily_digest"
    send_daily_digest_emails()
```

### Fasi di Implementazione

#### Fase 1: SMTP Configuration
- [ ] Verificare/estendere TenantSMTPConfig esistente
- [ ] UI configurazione SMTP
- [ ] Test connessione SMTP
- [ ] EmailService base

#### Fase 2: Notification Templates
- [ ] Modello NotificationTemplate
- [ ] Template base (review due, risk alert)
- [ ] Template rendering engine
- [ ] Variables system

#### Fase 3: Notification Service
- [ ] NotificationService base
- [ ] NotificationQueue
- [ ] NotificationPreference
- [ ] Integration con Asset Review

#### Fase 4: Email Sending
- [ ] EmailService completo
- [ ] Queue processing
- [ ] Retry logic
- [ ] Error handling

#### Fase 5: UI
- [ ] User preferences UI
- [ ] Admin notification management
- [ ] Template management (admin)

#### Fase 6: Scheduled Tasks
- [ ] Background worker per queue
- [ ] Scheduled checks (review, risk alerts)
- [ ] Daily/weekly digests

### Note

- **SMTP Esistente**: Verificare se `TenantSMTPConfig` esistente può essere riutilizzato
- **Email Templates**: Supportare HTML e plain text fallback
- **Localization**: Template multilingua (IT/EN)
- **Rate Limiting**: Proteggere da spam/abuse
- **Privacy**: Rispettare preferenze utente, opt-out sempre disponibile

---

## Vulnerability Intelligence Feed Integration

### Requisiti

Implementare un sistema per integrare feed di vulnerabilità note (CVE, security advisories) con gli asset:
- **Feed Collection**: Leggere feed da fonti standard (CVE, vendor advisories)
- **Vulnerability Matching**: Correlare vulnerabilità con asset basandosi su manufacturer, model, firmware
- **Risk Impact**: Aggiornare risk score asset quando vulnerabilità correlate vengono trovate
- **Alerting**: Notificare quando nuove vulnerabilità vengono trovate per asset esistenti
- **Tracking**: Tracciare vulnerabilità per asset e loro stato (patched, unpatched, mitigated)

### Obiettivi

1. Mantenere asset aggiornati con vulnerabilità note
2. Identificare asset vulnerabili automaticamente
3. Prioritizzare remediation basandosi su risk score
4. Supportare compliance e security posture assessment

### Fonti Feed Possibili

- **CVE Database**: National Vulnerability Database (NVD) - https://nvd.nist.gov/
- **CVE JSON Feed**: https://nvd.nist.gov/feeds/json/cve/1.1/
- **Vendor Advisories**: Feed specifici per manufacturer (Siemens, Rockwell, Schneider, etc.)
- **ICS-CERT Advisories**: Industrial Control Systems Cyber Emergency Response Team
- **CISA Advisories**: Cybersecurity and Infrastructure Security Agency

### Architettura

```
Vulnerability Feeds → Feed Parser → Vulnerability Database → Asset Matcher → Risk Update → Notifications
     ↓                    ↓                  ↓                    ↓              ↓            ↓
  CVE/NVD           Parse CVE JSON      Store CVE Data    Match by          Update      Alert Users
  Vendor Feeds       Parse Advisories    Store Advisory   Manufacturer      Risk Score   New Vulns
  ICS-CERT          Normalize Data      Track Status      Model/Firmware    Compliance   Patches
```

### Modello Dati

#### Vulnerability

```python
class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    
    id = Column(UUID, primary_key=True)
    
    # Identification
    cve_id = Column(String(20), unique=True, nullable=True)  # es: "CVE-2024-12345"
    advisory_id = Column(String(100), nullable=True)  # Vendor advisory ID
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    # Severity
    cvss_v3_score = Column(Float, nullable=True)  # 0.0-10.0
    cvss_v3_vector = Column(String(100), nullable=True)
    cvss_v2_score = Column(Float, nullable=True)
    severity = Column(String(20))  # 'critical', 'high', 'medium', 'low'
    
    # Affected Products
    affected_manufacturers = Column(JSONB)  # Lista manufacturer names
    affected_products = Column(JSONB)  # Lista prodotti/modelli
    affected_versions = Column(JSONB)  # Versioni firmware/software affette
    
    # Dates
    published_date = Column(DateTime, nullable=True)
    modified_date = Column(DateTime, nullable=True)
    
    # References
    references = Column(JSONB)  # Lista URL references
    vendor_advisory_url = Column(String(500), nullable=True)
    patch_url = Column(String(500), nullable=True)
    
    # Source
    source = Column(String(50))  # 'nvd', 'vendor', 'ics-cert', 'cisa'
    source_url = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

#### Asset Vulnerability

```python
class AssetVulnerability(Base):
    __tablename__ = "asset_vulnerabilities"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    asset_id = Column(UUID, ForeignKey("assets.id"), nullable=False)
    vulnerability_id = Column(UUID, ForeignKey("vulnerabilities.id"), nullable=False)
    
    # Match Confidence
    match_confidence = Column(Float, default=1.0)  # 0.0-1.0
    match_reason = Column(Text)  # Perché è stato matchato (manufacturer+model, firmware version, etc.)
    
    # Status
    status = Column(String(20), default="unpatched")  # 'unpatched', 'patched', 'mitigated', 'false_positive', 'not_applicable'
    
    # Remediation
    patched_date = Column(DateTime, nullable=True)
    patched_by = Column(UUID, ForeignKey("users.id"), nullable=True)
    mitigation_notes = Column(Text, nullable=True)
    
    # Impact
    risk_impact = Column(Float, nullable=True)  # Impatto sul risk score dell'asset
    
    # Dates
    detected_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    asset = relationship("Asset", back_populates="vulnerabilities")
    vulnerability = relationship("Vulnerability", back_populates="asset_vulnerabilities")
    patched_by_user = relationship("User", foreign_keys=[patched_by])
```

#### Vulnerability Feed Source

```python
class VulnerabilityFeedSource(Base):
    __tablename__ = "vulnerability_feed_sources"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=True)  # NULL = system-wide
    
    # Source Info
    name = Column(String(255), nullable=False)  # es: "NVD CVE Feed"
    source_type = Column(String(50), nullable=False)  # 'nvd', 'vendor', 'ics-cert', 'cisa', 'custom'
    
    # Feed Configuration
    feed_url = Column(String(500), nullable=False)
    feed_format = Column(String(20))  # 'json', 'xml', 'rss', 'csv'
    api_key = Column(String(255), nullable=True)  # Se richiesto
    
    # Sync Configuration
    sync_enabled = Column(Boolean, default=True)
    sync_interval_hours = Column(Integer, default=24)  # Quanto spesso sincronizzare
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(20))  # 'success', 'failed', 'partial'
    last_sync_error = Column(Text, nullable=True)
    
    # Filtering
    filters = Column(JSONB)  # Filtri per manufacturer, product type, etc.
    
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### Servizi

#### VulnerabilityFeedService

```python
class VulnerabilityFeedService:
    def fetch_nvd_feed(self, feed_type: str = "recent") -> List[Dict]:
        """
        Fetch CVE feed da NVD
        feed_type: 'recent', 'modified', 'all'
        """
        pass
    
    def fetch_vendor_advisory(self, vendor: str, feed_url: str) -> List[Dict]:
        """
        Fetch advisory da vendor specifico
        """
        pass
    
    def parse_cve_json(self, cve_data: Dict) -> Vulnerability:
        """
        Parse CVE JSON da NVD in Vulnerability object
        """
        pass
    
    def sync_feed(self, feed_source_id: UUID) -> Dict:
        """
        Sincronizza feed da una fonte
        - Fetch feed
        - Parse entries
        - Store/update vulnerabilities
        - Match con asset
        """
        pass
```

#### VulnerabilityMatcher

```python
class VulnerabilityMatcher:
    def match_vulnerability_to_assets(
        self,
        vulnerability: Vulnerability
    ) -> List[AssetVulnerability]:
        """
        Trova asset che potrebbero essere affetti da una vulnerabilità
        Matching basato su:
        - Manufacturer name (fuzzy match)
        - Product/model name (fuzzy match)
        - Firmware version (exact/range match)
        """
        pass
    
    def match_asset_to_vulnerabilities(
        self,
        asset: Asset
    ) -> List[Vulnerability]:
        """
        Trova vulnerabilità potenzialmente rilevanti per un asset
        """
        pass
    
    def calculate_match_confidence(
        self,
        asset: Asset,
        vulnerability: Vulnerability
    ) -> float:
        """
        Calcola confidence del match (0.0-1.0)
        - Manufacturer match: +0.4
        - Model match: +0.4
        - Firmware version match: +0.2
        """
        pass
```

#### VulnerabilityImpactCalculator

```python
class VulnerabilityImpactCalculator:
    def calculate_risk_impact(
        self,
        asset: Asset,
        vulnerability: Vulnerability
    ) -> float:
        """
        Calcola impatto della vulnerabilità sul risk score dell'asset
        Basato su:
        - CVSS score
        - Asset criticality
        - Asset exposure
        """
        pass
    
    def update_asset_risk_from_vulnerabilities(
        self,
        asset_id: UUID
    ) -> Asset:
        """
        Aggiorna risk score asset basandosi su vulnerabilità
        """
        pass
```

### Matching Logic

#### Manufacturer Matching

```python
# Fuzzy matching per manufacturer names
# Es: "Siemens AG" matches "Siemens", "Siemens Automation", etc.
manufacturer_match_score = fuzzy_match(asset.manufacturer.name, vuln.affected_manufacturers)
```

#### Product/Model Matching

```python
# Fuzzy matching per product/model names
# Es: "SIMATIC S7-1500" matches "S7-1500", "SIMATIC S7-1500 PLC", etc.
product_match_score = fuzzy_match(asset.model, vuln.affected_products)
```

#### Firmware Version Matching

```python
# Version matching (exact, range, pattern)
# Es: "V2.1.0" matches "V2.1.0", "2.1.x", ">=2.1.0,<2.2.0"
version_match = check_version_match(asset.firmware_version, vuln.affected_versions)
```

### API Endpoints

```python
# Vulnerabilities
GET /api/vulnerabilities
# Query params: ?cve_id={id}&severity={level}&manufacturer={name}

GET /api/vulnerabilities/{id}
# Dettaglio vulnerabilità

# Asset Vulnerabilities
GET /api/assets/{id}/vulnerabilities
# Lista vulnerabilità per asset
# Query params: ?status={status}

POST /api/assets/{id}/vulnerabilities/{vuln_id}/status
# Aggiorna status vulnerabilità
# Body: {status: 'patched'|'mitigated'|'false_positive', notes: str, patched_date: datetime}

GET /api/vulnerabilities/assets
# Lista asset con vulnerabilità
# Query params: ?severity_min={score}&status={status}

# Feed Sources
GET /api/vulnerability-feeds
# Lista feed sources configurati

POST /api/vulnerability-feeds
# Aggiungi nuovo feed source

PUT /api/vulnerability-feeds/{id}
# Aggiorna feed source

POST /api/vulnerability-feeds/{id}/sync
# Sincronizza feed manualmente

GET /api/vulnerability-feeds/{id}/status
# Status ultima sincronizzazione

# Matching
POST /api/vulnerabilities/{id}/match-assets
# Match manuale vulnerabilità con asset

POST /api/assets/{id}/match-vulnerabilities
# Match manuale asset con vulnerabilità

# Statistics
GET /api/vulnerabilities/stats
# Statistiche: total vulns, by severity, by status, by manufacturer, etc.
```

### UI

#### Vulnerability Dashboard

- **Overview**:
  - Total vulnerabilità trovate
  - Vulnerabilità per severity
  - Asset con vulnerabilità critiche
  - Vulnerabilità non patched
  
- **Recent Vulnerabilities**:
  - Nuove vulnerabilità trovate (ultimi 7 giorni)
  - Vulnerabilità aggiornate
  
- **Top Affected Assets**:
  - Asset con più vulnerabilità
  - Asset con vulnerabilità critiche

#### Asset Detail - Tab "Vulnerabilities"

- **Vulnerability List**:
  - Lista vulnerabilità per asset
  - Filtri per status, severity
  - Colonna: CVE ID, Severity, Status, Detected Date
  
- **Vulnerability Detail**:
  - Dettaglio CVE
  - CVSS score e vector
  - Description
  - References e patch URL
  - Status e remediation notes
  
- **Actions**:
  - "Mark as Patched"
  - "Mark as Mitigated"
  - "Mark as False Positive"
  - "View CVE Details" (link esterno)

#### Vulnerability Management Page

- **Vulnerability List**:
  - Lista tutte vulnerabilità nel sistema
  - Filtri: CVE ID, severity, manufacturer, status
  - Search
  
- **Vulnerability Detail**:
  - Informazioni complete CVE
  - Affected assets
  - Remediation status
  
- **Feed Sources**:
  - Lista feed configurati
  - Status sincronizzazione
  - Manual sync button
  - Add/edit feed source

#### Configuration - Feed Sources

- **Feed Source Management**:
  - Lista feed sources
  - Add/edit/delete feed
  - Test feed connection
  - Configure sync interval
  - Filters configuration

### Integrazione con Risk Assessment

```python
# Estendere CompositeRiskScoringEngine
def calculate(self, asset, language="en") -> Dict[str, Any]:
    # ... calcolo esistente ...
    
    # Vulnerability factors
    unpatched_vulns = get_unpatched_vulnerabilities(asset.id)
    if unpatched_vulns:
        critical_vulns = [v for v in unpatched_vulns if v.vulnerability.severity == 'critical']
        high_vulns = [v for v in unpatched_vulns if v.vulnerability.severity == 'high']
        
        if critical_vulns:
            vuln_score += 3
            vuln_break.append(f"{len(critical_vulns)} critical vulnerabilities")
        if high_vulns:
            vuln_score += 2
            vuln_break.append(f"{len(high_vulns)} high severity vulnerabilities")
        
        # CVSS score impact
        max_cvss = max([v.vulnerability.cvss_v3_score or 0 for v in unpatched_vulns])
        if max_cvss >= 9.0:
            vuln_score += 2
        elif max_cvss >= 7.0:
            vuln_score += 1
    
    return breakdown
```

### Notifiche

Integrare con Notification System:
- **New Vulnerability Alert**: Quando nuova vulnerabilità viene matchata con asset
- **Critical Vulnerability Alert**: Quando vulnerabilità critica viene trovata
- **Vulnerability Status Update**: Quando vulnerabilità viene patched

### Scheduled Tasks

```python
@schedule.daily(at="02:00")
def sync_vulnerability_feeds():
    """
    Sincronizza tutti i feed abilitati
    """
    feed_sources = get_enabled_feed_sources()
    for feed in feed_sources:
        vulnerability_feed_service.sync_feed(feed.id)

@schedule.every(6).hours
def match_new_vulnerabilities():
    """
    Match nuove vulnerabilità con asset esistenti
    """
    new_vulns = get_unmatched_vulnerabilities()
    for vuln in new_vulns:
        vulnerability_matcher.match_vulnerability_to_assets(vuln)
```

### Fasi di Implementazione

#### Fase 1: Modelli Base
- [ ] Modello Vulnerability
- [ ] Modello AssetVulnerability
- [ ] Modello VulnerabilityFeedSource
- [ ] Migrazioni database

#### Fase 2: Feed Parser
- [ ] NVD CVE JSON parser
- [ ] VulnerabilityFeedService base
- [ ] Store vulnerabilities

#### Fase 3: Matching Engine
- [ ] VulnerabilityMatcher
- [ ] Manufacturer/product matching
- [ ] Firmware version matching
- [ ] Confidence calculation

#### Fase 4: API Base
- [ ] CRUD vulnerabilities
- [ ] Asset vulnerabilities endpoints
- [ ] Feed management endpoints

#### Fase 5: UI Base
- [ ] Vulnerability dashboard
- [ ] Asset vulnerabilities tab
- [ ] Vulnerability detail view

#### Fase 6: Integration
- [ ] Risk assessment integration
- [ ] Notification integration
- [ ] Scheduled sync tasks

#### Fase 7: Advanced
- [ ] Vendor-specific feed parsers
- [ ] Advanced matching algorithms
- [ ] Remediation tracking
- [ ] Reporting

### Note Implementazione

- **NVD API**: NVD offre API REST e JSON feeds - https://nvd.nist.gov/developers/vulnerabilities
- **Rate Limiting**: Rispettare rate limits delle API (NVD: 5 requests/second)
- **Data Volume**: CVE database è grande, considerare pagination e incremental updates
- **Matching Accuracy**: Fuzzy matching può generare falsi positivi, permettere review manuale
- **Vendor Feeds**: Ogni vendor ha formato diverso, richiede parser specifici

### Fonti Feed Standard

1. **NVD CVE Feed**: https://nvd.nist.gov/feeds/json/cve/1.1/
2. **ICS-CERT Advisories**: https://www.cisa.gov/news-events/cybersecurity-advisories
3. **Vendor Advisories**: 
   - Siemens: https://cert-portal.siemens.com/
   - Rockwell: https://www.rockwellautomation.com/security-advisories
   - Schneider: https://www.se.com/ww/en/download/

---

**Status**: Draft - In Review  
**Last Updated**: 2025-12-05  
**Author**: Maurizio Bertaboni

### Changelog Design

**2025-12-05**: 
- Aggiornata sezione Remote Syslog → Syslog Server e SIEM Forwarding
- Aggiunta architettura dual-purpose: log collection + SIEM forwarding
- Enfasi su BAS/CS support tramite log storage completo
- Aggiunto modello SyslogForwardingConfig per configurazione SIEM
- Aggiunte considerazioni performance e security

