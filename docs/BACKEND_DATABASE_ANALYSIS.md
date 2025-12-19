# Backend e Database - Analisi Organizzativa

## Overview

Questo documento analizza la struttura attuale del backend e propone un'organizzazione ottimale per implementare tutte le nuove feature progettate, mantenendo coerenza, performance e manutenibilità.

**Data Analisi**: 2025-12-04  
**Versione Backend**: FastAPI + SQLAlchemy + PostgreSQL  
**Sistema Migrazioni**: Alembic

---

## 1. Struttura Attuale

### 1.1 Organizzazione Modelli Esistenti

```
backend/app/models/
├── Core/Infrastructure:
│   ├── tenant.py (Tenant)
│   ├── user.py (User)
│   ├── role.py (Role)
│   └── api_key.py (ApiKey)
│
├── Physical Organization:
│   ├── site.py (Site)
│   ├── area.py (Area)
│   └── location.py (Location, LocationFloorplan)
│
├── Asset Management:
│   ├── asset.py (Asset) ⭐ Core
│   ├── asset_type.py (AssetType)
│   ├── asset_status.py (AssetStatus)
│   ├── asset_interface.py (AssetInterface)
│   ├── asset_connection.py (AssetConnection)
│   ├── asset_communication.py (AssetCommunication)
│   ├── asset_document.py (AssetDocument)
│   └── asset_photo.py (AssetPhoto)
│
├── Reference Data:
│   ├── manufacturer.py (Manufacturer)
│   ├── supplier.py (Supplier, SupplierDocument)
│   └── contact.py (Contact)
│
├── System:
│   ├── audit_log.py (AuditLog)
│   ├── tenant_smtp_config.py (TenantSMTPConfig)
│   ├── print_template.py (PrintTemplate)
│   └── print_history.py (PrintHistory)
│
└── Many-to-Many Tables:
    └── asset_contacts (in asset.py)
    └── asset_suppliers (in asset.py)
```

### 1.2 Pattern Architetturali Attuali

- **Models**: SQLAlchemy ORM con Base declarative
- **Schemas**: Pydantic per validazione API
- **CRUD**: Operazioni database separate (app/crud/)
- **Services**: Business logic (app/services/)
- **Routers**: API endpoints (app/routers/)
- **Migrations**: Alembic con auto-discovery da Base.metadata

### 1.3 Relazioni Chiave Esistenti

```python
# Asset è il modello centrale
Asset:
  - tenant_id → Tenant
  - site_id → Site
  - location_id → Location (fisica)
  - area_id → Area (fisica)
  - manufacturer_id → Manufacturer
  - asset_type_id → AssetType
  - status_id → AssetStatus
  - contacts (many-to-many) → Contact
  - suppliers (many-to-many) → Supplier
  - interfaces (one-to-many) → AssetInterface
  - connections (one-to-many) → AssetConnection
  - communications (one-to-many) → AssetCommunication
```

---

## 2. Nuovi Modelli da Implementare

### 2.1 ISA/IEC 62443

#### 2.1.1 SecurityZone
```python
# backend/app/models/security_zone.py
class SecurityZone(Base):
    __tablename__ = "security_zones"
    
    # Relazioni
    tenant_id → Tenant
    site_id → Site
    assets (one-to-many) → Asset.security_zone_id
    conduits_from (one-to-many) → Conduit.from_zone_id
    conduits_to (one-to-many) → Conduit.to_zone_id
```

**Considerazioni**:
- Zone logiche separate da Location/Area (fisiche)
- Mapping opzionale a Locations/Areas (many-to-many, tabella separata)
- Indici: `(tenant_id, site_id)`, `(tenant_id, deleted_at)`

#### 2.1.2 Conduit
```python
# backend/app/models/conduit.py
class Conduit(Base):
    __tablename__ = "conduits"
    
    # Relazioni
    tenant_id → Tenant
    from_zone_id → SecurityZone
    to_zone_id → SecurityZone
    # Opzionale: many-to-many con AssetConnection
```

**Considerazioni**:
- Indici: `(from_zone_id, to_zone_id)`, `(tenant_id)`

#### 2.1.3 SecurityRequirement
```python
# backend/app/models/security_requirement.py
class SecurityRequirement(Base):
    __tablename__ = "security_requirements"
    
    # Standard ISA/IEC 62443
    # NO tenant_id (system-wide, standard)
```

**Considerazioni**:
- Dati di riferimento standard, popolati da seed data
- Indice: `requirement_id` (unique)

#### 2.1.4 SecurityRequirementCompliance
```python
# backend/app/models/security_requirement_compliance.py
class SecurityRequirementCompliance(Base):
    __tablename__ = "security_requirement_compliance"
    
    # Relazioni
    tenant_id → Tenant
    requirement_id → SecurityRequirement
    zone_id → SecurityZone (nullable)
    asset_id → Asset (nullable)
    conduit_id → Conduit (nullable)
    assessed_by → User
```

**Considerazioni**:
- Indici: `(tenant_id, zone_id)`, `(tenant_id, asset_id)`, `(requirement_id)`

### 2.2 Asset Ownership e Point-of-Contact

#### 2.2.1 Estensione asset_contacts
```python
# Modifica backend/app/models/asset.py
asset_contacts = Table(
    "asset_contacts",
    Base.metadata,
    Column("asset_id", UUID, ForeignKey("assets.id"), primary_key=True),
    Column("contact_id", UUID, ForeignKey("contacts.id"), primary_key=True),
    Column("role", String(50), nullable=False, default="other")  # ⬅️ NUOVO
)
```

**Migrazione**:
- Aggiungere colonna `role` con default 'other'
- Aggiungere constraint CHECK per valori validi
- Indice: `(asset_id, role)`

### 2.3 Asset Dependencies

#### 2.3.1 AssetDependency
```python
# backend/app/models/asset_dependency.py
class AssetDependency(Base):
    __tablename__ = "asset_dependencies"
    
    # Relazioni
    tenant_id → Tenant
    dependent_asset_id → Asset
    dependency_asset_id → Asset
```

**Considerazioni**:
- Self-referential relationship (Asset → Asset)
- Constraint: `dependent_asset_id != dependency_asset_id`
- Indici: `(dependent_asset_id)`, `(dependency_asset_id)`, `(tenant_id, dependency_type)`

### 2.4 Asset Review

#### 2.4.1 Estensioni Asset
```python
# Modifica backend/app/models/asset.py
class Asset(Base):
    # ... campi esistenti ...
    
    # Review fields ⬅️ NUOVO
    last_review_date = Column(DateTime)
    next_review_date = Column(DateTime, index=True)  # Per query performance
    review_status = Column(String(20), default="pending", index=True)
    review_notes = Column(Text)
    review_interval_months = Column(Integer, default=6)
```

**Considerazioni**:
- Indici: `next_review_date`, `review_status` (per query asset da revieware)

#### 2.4.2 Estensioni Tenant/Site
```python
# Modifica backend/app/models/tenant.py
class Tenant(Base):
    default_review_interval_months = Column(Integer, default=6)

# Modifica backend/app/models/site.py
class Site(Base):
    review_interval_months = Column(Integer, nullable=True)
```

### 2.5 Notification System

#### 2.5.1 NotificationTemplate
```python
# backend/app/models/notification_template.py
class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    
    # tenant_id nullable (NULL = system-wide)
```

**Considerazioni**:
- Indice: `template_code` (unique)

#### 2.5.2 NotificationPreference
```python
# backend/app/models/notification_preference.py
class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    
    # Relazioni
    user_id → User
    tenant_id → Tenant
```

**Considerazioni**:
- Unique constraint: `(user_id, notification_type)`
- Indice: `(user_id, tenant_id)`

#### 2.5.3 NotificationQueue
```python
# backend/app/models/notification_queue.py
class NotificationQueue(Base):
    __tablename__ = "notification_queue"
    
    # Relazioni
    tenant_id → Tenant
    user_id → User
    template_id → NotificationTemplate
```

**Considerazioni**:
- Indice: `scheduled_for` (per processing queue)
- Indice: `(status, scheduled_for)` (per query pending)

#### 2.5.4 NotificationLog
```python
# backend/app/models/notification_log.py
class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    # Relazioni
    tenant_id → Tenant
    user_id → User
```

**Considerazioni**:
- Indice: `created_at` (per query storiche)
- Indice: `(tenant_id, user_id, created_at)`

**Nota**: `TenantSMTPConfig` già esiste, riutilizzare.

### 2.6 Vulnerability Intelligence

#### 2.6.1 Vulnerability
```python
# backend/app/models/vulnerability.py
class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    
    # NO tenant_id (system-wide, CVE database)
    # cve_id unique
```

**Considerazioni**:
- Dati system-wide (CVE database)
- Indice: `cve_id` (unique)
- Indice: `(severity, published_date)`
- Indice: `affected_manufacturers` (GIN index su JSONB)

#### 2.6.2 AssetVulnerability
```python
# backend/app/models/asset_vulnerability.py
class AssetVulnerability(Base):
    __tablename__ = "asset_vulnerabilities"
    
    # Relazioni
    tenant_id → Tenant
    asset_id → Asset
    vulnerability_id → Vulnerability
    patched_by → User
```

**Considerazioni**:
- Indici: `(asset_id, status)`, `(tenant_id, status)`, `(vulnerability_id)`

#### 2.6.3 VulnerabilityFeedSource
```python
# backend/app/models/vulnerability_feed_source.py
class VulnerabilityFeedSource(Base):
    __tablename__ = "vulnerability_feed_sources"
    
    # tenant_id nullable (NULL = system-wide)
```

**Considerazioni**:
- Indice: `(tenant_id, sync_enabled)`

### 2.7 Enterprise Authentication (Futuro)

#### 2.7.1 TenantSSOConfig
```python
# backend/app/models/tenant_sso_config.py
class TenantSSOConfig(Base):
    __tablename__ = "tenant_sso_config"
    
    # Relazioni
    tenant_id → Tenant (primary_key)
```

**Considerazioni**:
- One-to-one con Tenant
- Client secret encrypted

### 2.8 Remote Syslog (Futuro)

#### 2.8.1 SyslogEntry
```python
# backend/app/models/syslog_entry.py
class SyslogEntry(Base):
    __tablename__ = "syslog_entries"
    
    # Relazioni
    tenant_id → Tenant
    asset_id → Asset (nullable, auto-correlated)
```

**Considerazioni**:
- **Volume alto**: Considerare partizionamento per data
- Indici: `timestamp`, `(tenant_id, timestamp)`, `(asset_id, timestamp)`
- Indice: `(severity, timestamp)` per alerting

#### 2.8.2 SyslogCorrelationRule
```python
# backend/app/models/syslog_correlation_rule.py
class SyslogCorrelationRule(Base):
    __tablename__ = "syslog_correlation_rules"
    
    # Relazioni
    tenant_id → Tenant
    asset_id → Asset
```

---

## 3. Organizzazione File Backend

### 3.1 Struttura Modelli Proposta

```
backend/app/models/
├── __init__.py
│
├── Core/ (esistenti)
│   ├── tenant.py
│   ├── user.py
│   ├── role.py
│   └── api_key.py
│
├── Physical/ (esistenti)
│   ├── site.py
│   ├── area.py
│   └── location.py
│
├── Asset/ (esistenti + modifiche)
│   ├── asset.py ⭐ (modificare: aggiungere campi review, security_zone_id)
│   ├── asset_type.py
│   ├── asset_status.py
│   ├── asset_interface.py
│   ├── asset_connection.py
│   ├── asset_communication.py
│   ├── asset_document.py
│   ├── asset_photo.py
│   ├── asset_dependency.py ⬅️ NUOVO
│   └── asset_vulnerability.py ⬅️ NUOVO
│
├── Security/ ⬅️ NUOVO
│   ├── security_zone.py
│   ├── conduit.py
│   ├── security_requirement.py
│   └── security_requirement_compliance.py
│
├── Vulnerability/ ⬅️ NUOVO
│   ├── vulnerability.py
│   └── vulnerability_feed_source.py
│
├── Notification/ ⬅️ NUOVO
│   ├── notification_template.py
│   ├── notification_preference.py
│   ├── notification_queue.py
│   └── notification_log.py
│
├── Reference/ (esistenti)
│   ├── manufacturer.py
│   ├── supplier.py
│   └── contact.py
│
└── System/ (esistenti + nuovi)
    ├── audit_log.py
    ├── tenant_smtp_config.py (esistente, riutilizzare)
    ├── tenant_sso_config.py ⬅️ NUOVO (futuro)
    ├── print_template.py
    ├── print_history.py
    ├── syslog_entry.py ⬅️ NUOVO (futuro)
    └── syslog_correlation_rule.py ⬅️ NUOVO (futuro)
```

### 3.2 Struttura Servizi Proposta

```
backend/app/services/
├── __init__.py
│
├── Core/ (esistenti)
│   ├── auth.py
│   ├── rbac.py
│   └── create_tenant.py
│
├── Asset/ (esistenti + nuovi)
│   ├── asset_sync.py (esistente)
│   ├── asset_review_service.py ⬅️ NUOVO
│   └── dependency_chain_analyzer.py ⬅️ NUOVO
│
├── Security/ ⬅️ NUOVO
│   ├── isa62443_compliance_engine.py
│   └── zone_risk_calculator.py
│
├── Risk/ (esistente + estensioni)
│   ├── risk_scoring.py ⭐ (estendere per nuove feature)
│   └── risk_propagation_engine.py ⬅️ NUOVO
│
├── Vulnerability/ ⬅️ NUOVO
│   ├── vulnerability_feed_service.py
│   ├── vulnerability_matcher.py
│   └── vulnerability_impact_calculator.py
│
├── Notification/ ⬅️ NUOVO
│   ├── notification_service.py
│   └── email_service.py (estendere da esistente)
│
└── System/ (esistenti)
    ├── audit_log.py
    ├── email_service.py (esistente, estendere)
    ├── dashboard_cache.py
    └── pcap_parser.py
```

### 3.3 Struttura Router Proposta

```
backend/app/routers/
├── __init__.py
│
├── Core/ (esistenti)
│   ├── users.py
│   ├── tenants.py
│   └── roles.py
│
├── Physical/ (esistenti)
│   ├── sites.py
│   ├── areas.py
│   └── locations.py
│
├── Asset/ (esistenti + nuovi)
│   ├── assets.py ⭐ (estendere con nuovi endpoints)
│   ├── asset_types.py
│   ├── asset_statuses.py
│   ├── asset_connections.py
│   ├── asset_dependencies.py ⬅️ NUOVO
│   └── asset_reviews.py ⬅️ NUOVO
│
├── Security/ ⬅️ NUOVO
│   ├── security_zones.py
│   ├── conduits.py
│   └── compliance.py
│
├── Vulnerability/ ⬅️ NUOVO
│   ├── vulnerabilities.py
│   └── vulnerability_feeds.py
│
├── Notification/ ⬅️ NUOVO
│   └── notifications.py
│
└── System/ (esistenti)
    ├── audit_logs.py
    ├── smtp_config.py (esistente)
    ├── dashboards.py
    └── search.py
```

### 3.4 Struttura CRUD Proposta

```
backend/app/crud/
├── __init__.py
│
├── Core/ (esistenti)
│   ├── users.py
│   ├── tenants.py
│   └── roles.py
│
├── Asset/ (esistenti + nuovi)
│   ├── assets.py ⭐ (estendere)
│   ├── asset_types.py
│   ├── asset_dependencies.py ⬅️ NUOVO
│   └── asset_reviews.py ⬅️ NUOVO
│
├── Security/ ⬅️ NUOVO
│   ├── security_zones.py
│   ├── conduits.py
│   └── compliance.py
│
├── Vulnerability/ ⬅️ NUOVO
│   ├── vulnerabilities.py
│   └── vulnerability_feeds.py
│
└── Notification/ ⬅️ NUOVO
    └── notifications.py
```

---

## 4. Migrazioni Database

### 4.1 Strategia Migrazioni

**Approccio Incrementale**: Una migrazione per feature/fase logica

#### Fase 1: Asset Ownership e Review (Priorità Alta)
```
alembic/versions/
├── add_asset_contacts_role.py
├── add_asset_review_fields.py
└── add_tenant_site_review_config.py
```

#### Fase 2: ISA/IEC 62443 (Priorità Alta)
```
alembic/versions/
├── create_security_zones.py
├── create_conduits.py
├── create_security_requirements.py
├── create_security_requirement_compliance.py
└── add_asset_security_zone_fields.py
```

#### Fase 3: Asset Dependencies (Priorità Media)
```
alembic/versions/
└── create_asset_dependencies.py
```

#### Fase 4: Notification System (Priorità Media)
```
alembic/versions/
├── create_notification_templates.py
├── create_notification_preferences.py
├── create_notification_queue.py
└── create_notification_logs.py
```

#### Fase 5: Vulnerability Intelligence (Priorità Bassa)
```
alembic/versions/
├── create_vulnerabilities.py
├── create_asset_vulnerabilities.py
└── create_vulnerability_feed_sources.py
```

### 4.2 Best Practices Migrazioni - Compatibilità e Aggiornabilità

**Principio Fondamentale**: Ogni migrazione deve garantire che il sistema possa essere aggiornato da qualsiasi versione precedente senza perdita di dati o funzionalità.

#### 4.2.1 Naming Convention
- **Formato**: `{timestamp}_{description}.py`
- **Esempi**: 
  - `20241204_123456_add_asset_contacts_role.py`
  - `20241204_234567_add_asset_review_fields.py`
- **Descrizione**: Deve essere chiara e descrittiva

#### 4.2.2 Compatibilità Retroattiva

**Regole d'Oro**:

1. **Valori Default Sempre Presenti**
   ```python
   # ✅ CORRETTO
   op.add_column('assets', 
       sa.Column('review_status', sa.String(20), 
                 nullable=False, server_default='pending'))
   
   # ❌ SBAGLIATO (nullable senza default)
   op.add_column('assets', 
       sa.Column('review_status', sa.String(20), nullable=False))
   ```

2. **Colonne Nullable per Transizione Graduale**
   ```python
   # ✅ CORRETTO - Permette transizione graduale
   op.add_column('assets', 
       sa.Column('security_zone_id', UUID, nullable=True))
   
   # Poi in migrazione successiva, se necessario:
   # op.alter_column('assets', 'security_zone_id', nullable=False)
   ```

3. **Migrazione Dati Esistenti**
   ```python
   def upgrade():
       # 1. Aggiungi colonna nullable
       op.add_column('asset_contacts', 
           sa.Column('role', sa.String(50), nullable=True))
       
       # 2. Popola dati esistenti
       op.execute("""
           UPDATE asset_contacts 
           SET role = 'other' 
           WHERE role IS NULL
       """)
       
       # 3. Rendi NOT NULL solo dopo aver popolato
       op.alter_column('asset_contacts', 'role', 
                       nullable=False, server_default='other')
   ```

4. **Evitare Breaking Changes**
   ```python
   # ✅ CORRETTO - Aggiungi nuova colonna
   op.add_column('assets', sa.Column('new_field', sa.String(50)))
   
   # ❌ SBAGLIATO - Rimuovi colonna esistente (solo se deprecata)
   # op.drop_column('assets', 'old_field')  # Solo dopo periodo deprecazione
   ```

#### 4.2.3 Rollback Sempre Implementato

**Ogni migrazione DEVE avere `downgrade()` funzionante**:

```python
def upgrade():
    op.add_column('assets', sa.Column('review_status', sa.String(20)))
    op.create_index('idx_assets_review_status', 'assets', ['review_status'])

def downgrade():
    op.drop_index('idx_assets_review_status', 'assets')
    op.drop_column('assets', 'review_status')
```

**Nota**: Se il downgrade comporta perdita di dati, documentarlo chiaramente.

#### 4.2.4 Migrazioni Multi-Step per Grandi Modifiche

**Per modifiche complesse, dividere in più migrazioni**:

```python
# Migrazione 1: Aggiungi colonna nullable
def upgrade():
    op.add_column('assets', sa.Column('security_zone_id', UUID, nullable=True))

# Migrazione 2: Popola dati (background job)
def upgrade():
    # Migrazione dati in batch
    pass

# Migrazione 3: Aggiungi foreign key (dopo che dati sono popolati)
def upgrade():
    op.create_foreign_key('fk_assets_security_zone', 
                         'assets', 'security_zones', 
                         ['security_zone_id'], ['id'])
```

#### 4.2.5 Gestione Indici

**Indici in migrazioni separate se voluminosi**:

```python
# Migrazione 1: Aggiungi colonna
def upgrade():
    op.add_column('assets', sa.Column('next_review_date', sa.DateTime))

# Migrazione 2: Aggiungi indice (può essere lento su tabelle grandi)
def upgrade():
    op.create_index('idx_assets_next_review_date', 
                   'assets', ['next_review_date'],
                   postgresql_where=sa.text('deleted_at IS NULL'))
```

#### 4.2.6 Migrazioni Condizionali

**Verificare stato prima di applicare modifiche**:

```python
def upgrade():
    # Verifica se colonna esiste già (per migrazioni multiple)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('assets')]
    
    if 'review_status' not in columns:
        op.add_column('assets', 
            sa.Column('review_status', sa.String(20), 
                     server_default='pending'))
```

#### 4.2.7 Migrazione Dati di Riferimento

**Per dati seed (es: Security Requirements)**:

```python
def upgrade():
    # Crea tabella
    op.create_table('security_requirements', ...)
    
    # Popola dati standard (idempotente)
    op.execute("""
        INSERT INTO security_requirements (requirement_id, title, description)
        VALUES 
            ('SR 1.1', 'Identification and Authentication', '...'),
            ('SR 1.2', 'Use Control', '...')
        ON CONFLICT (requirement_id) DO NOTHING
    """)
```

#### 4.2.8 Test Migrazioni

**Sempre testare**:
1. Upgrade da versione precedente
2. Downgrade e re-upgrade
3. Upgrade da versione molto vecchia (se possibile)
4. Migrazione con dati reali (backup prima!)

#### 4.2.9 Documentazione Migrazioni

**Ogni migrazione deve documentare**:
- Cosa fa
- Perché è necessaria
- Impatto su dati esistenti
- Tempo stimato (per tabelle grandi)
- Se richiede downtime

```python
"""
Add role column to asset_contacts table

This migration adds a 'role' column to the asset_contacts many-to-many
table to support multiple owners and points-of-contact per asset.

Existing records will be set to role='other' to maintain compatibility.

No downtime required.
Estimated time: < 1 second for typical database sizes.
"""
```

#### 4.2.10 Esempi Pratici

**Esempio 1: Aggiungere colonna con default**
```python
def upgrade():
    op.add_column('assets',
        sa.Column('review_interval_months', sa.Integer(),
                 nullable=False, server_default='6'))
    
    # Per tenant esistenti, usa default
    # (già gestito da server_default)

def downgrade():
    op.drop_column('assets', 'review_interval_months')
```

**Esempio 2: Modificare tabella many-to-many**
```python
def upgrade():
    # Aggiungi colonna role
    op.add_column('asset_contacts',
        sa.Column('role', sa.String(50), nullable=True))
    
    # Popola esistenti
    op.execute("UPDATE asset_contacts SET role = 'other' WHERE role IS NULL")
    
    # Rendi NOT NULL
    op.alter_column('asset_contacts', 'role',
                   nullable=False, server_default='other')
    
    # Aggiungi constraint
    op.create_check_constraint(
        'ck_asset_contacts_role',
        'asset_contacts',
        "role IN ('owner', 'point_of_contact', 'other', 'technical', 'administrative')"
    )

def downgrade():
    op.drop_constraint('ck_asset_contacts_role', 'asset_contacts')
    op.drop_column('asset_contacts', 'role')
```

**Esempio 3: Aggiungere foreign key (dopo dati popolati)**
```python
def upgrade():
    # Verifica che tutti i security_zone_id siano validi
    op.execute("""
        UPDATE assets 
        SET security_zone_id = NULL 
        WHERE security_zone_id NOT IN (SELECT id FROM security_zones)
    """)
    
    # Aggiungi foreign key
    op.create_foreign_key(
        'fk_assets_security_zone',
        'assets', 'security_zones',
        ['security_zone_id'], ['id'],
        ondelete='SET NULL'  # Se zona eliminata, setta NULL
    )

def downgrade():
    op.drop_constraint('fk_assets_security_zone', 'assets', type_='foreignkey')
```

#### 4.2.11 Test Migrazioni in Ambiente di Sviluppo

**Prima di applicare in produzione**:

```bash
# 1. Backup database di sviluppo
pg_dump -U user -d database > backup_before_migration.sql

# 2. Test upgrade
alembic upgrade head

# 3. Verifica che tutto funzioni
# - API endpoints
# - Query database
# - Dati esistenti ancora accessibili

# 4. Test downgrade
alembic downgrade -1

# 5. Verifica che downgrade funzioni
# - Nessun dato perso (se possibile)
# - Sistema ancora funzionante

# 6. Re-upgrade
alembic upgrade head

# 7. Verifica finale
```

#### 4.2.12 Migrazioni in Produzione

**Workflow Sicuro**:

1. **Backup Completo**
   ```bash
   # Backup database
   pg_dump -U user -d production_db > backup_$(date +%Y%m%d_%H%M%S).sql
   
   # Verifica backup
   pg_restore --list backup_*.sql
   ```

2. **Test su Staging First**
   - Applicare migrazione su ambiente staging identico a produzione
   - Testare tutte le funzionalità
   - Verificare performance

3. **Ventana di Manutenzione** (se necessario)
   - Per migrazioni che richiedono lock tabelle
   - Comunicare agli utenti
   - Pianificare in orari di basso traffico

4. **Applicazione Migrazione**
   ```bash
   # In produzione
   alembic upgrade head
   
   # Monitorare output
   # Verificare eventuali errori
   ```

5. **Verifica Post-Migrazione**
   - Test rapido funzionalità critiche
   - Verifica integrità dati
   - Monitoraggio performance

6. **Rollback Plan** (se necessario)
   ```bash
   # Solo se problemi critici
   alembic downgrade -1
   # Oppure restore da backup
   ```

#### 4.2.13 Gestione Versioni Multiple

**Scenario**: Sistema in produzione con versioni multiple

```python
# Migrazione deve funzionare da qualsiasi versione precedente
def upgrade():
    # Verifica versione corrente
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Se colonna non esiste, aggiungila
    columns = [col['name'] for col in inspector.get_columns('assets')]
    if 'review_status' not in columns:
        op.add_column('assets', 
            sa.Column('review_status', sa.String(20), 
                     server_default='pending'))
    
    # Se indice non esiste, crealo
    indexes = [idx['name'] for idx in inspector.get_indexes('assets')]
    if 'idx_assets_review_status' not in indexes:
        op.create_index('idx_assets_review_status', 
                       'assets', ['review_status'])
```

#### 4.2.14 Migrazioni Dati Complesse

**Per migrazioni che richiedono trasformazione dati**:

```python
def upgrade():
    # 1. Aggiungi colonna nullable
    op.add_column('assets', 
        sa.Column('security_zone_id', UUID, nullable=True))
    
    # 2. Migrazione dati in batch (per tabelle grandi)
    conn = op.get_bind()
    
    # Batch processing per evitare lock prolungati
    batch_size = 1000
    offset = 0
    
    while True:
        result = conn.execute(sa.text("""
            SELECT id, site_id 
            FROM assets 
            WHERE security_zone_id IS NULL 
            LIMIT :limit OFFSET :offset
        """), {"limit": batch_size, "offset": offset})
        
        rows = result.fetchall()
        if not rows:
            break
        
        for row in rows:
            # Logica di migrazione dati
            # Es: crea default zone per site se non esiste
            pass
        
        offset += batch_size
    
    # 3. Dopo migrazione dati, aggiungi constraint se necessario
    # op.create_foreign_key(...)
```

#### 4.2.15 Checklist Pre-Migrazione

Prima di creare una migrazione, verificare:

- [ ] Migrazione è incrementale (non rompe versione precedente)
- [ ] Valori default per colonne NOT NULL
- [ ] Dati esistenti vengono migrati correttamente
- [ ] `downgrade()` è implementato e testato
- [ ] Indici aggiunti in modo efficiente
- [ ] Foreign keys con cascade rules appropriate
- [ ] Migrazione testata su database di sviluppo (backup!)
- [ ] Migrazione testata su staging (se disponibile)
- [ ] Documentazione aggiornata
- [ ] Tempo di esecuzione accettabile (per tabelle grandi)
- [ ] Backup pianificato per produzione
- [ ] Rollback plan documentato
- [ ] Test di regressione pianificati

#### 4.2.16 Compatibilità Multi-Versione

**Principio**: Il sistema deve funzionare anche se alcune migrazioni non sono ancora applicate.

```python
# Nel codice applicativo, gestire colonne opzionali
def get_asset_review_status(asset):
    # Se colonna non esiste ancora (versione vecchia), usa default
    if hasattr(asset, 'review_status'):
        return asset.review_status
    return 'pending'  # Default
```

**Nota**: Questo è un fallback temporaneo. L'obiettivo è sempre avere tutte le migrazioni applicate.

### 4.3 Script Seed Data

```
backend/app/init_data/
├── __init__.py
├── init_security_requirements.py ⬅️ NUOVO (ISA/IEC 62443 SR)
├── init_notification_templates.py ⬅️ NUOVO
└── init_bas_behavior_tags.py ⬅️ NUOVO (futuro, BAS/CS)
```

---

## 5. Indici Database - Performance

### 5.1 Indici Critici da Aggiungere

#### Asset
```sql
-- Review queries
CREATE INDEX idx_assets_next_review_date ON assets(next_review_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_assets_review_status ON assets(review_status, next_review_date) WHERE deleted_at IS NULL;

-- Security Zone queries
CREATE INDEX idx_assets_security_zone_id ON assets(security_zone_id) WHERE deleted_at IS NULL;

-- Vulnerability queries (futuro)
CREATE INDEX idx_assets_manufacturer_id ON assets(manufacturer_id) WHERE deleted_at IS NULL;
```

#### SecurityZone
```sql
CREATE INDEX idx_security_zones_tenant_site ON security_zones(tenant_id, site_id) WHERE deleted_at IS NULL;
```

#### AssetDependency
```sql
CREATE INDEX idx_asset_dependencies_dependent ON asset_dependencies(dependent_asset_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_asset_dependencies_dependency ON asset_dependencies(dependency_asset_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_asset_dependencies_tenant_type ON asset_dependencies(tenant_id, dependency_type) WHERE deleted_at IS NULL;
```

#### AssetVulnerability
```sql
CREATE INDEX idx_asset_vulnerabilities_asset_status ON asset_vulnerabilities(asset_id, status);
CREATE INDEX idx_asset_vulnerabilities_tenant_status ON asset_vulnerabilities(tenant_id, status);
```

#### NotificationQueue
```sql
CREATE INDEX idx_notification_queue_scheduled ON notification_queue(status, scheduled_for) WHERE status = 'pending';
```

#### SyslogEntry (futuro, volume alto)
```sql
-- Considerare partizionamento per data
CREATE INDEX idx_syslog_entries_timestamp ON syslog_entries(tenant_id, timestamp DESC);
CREATE INDEX idx_syslog_entries_asset_timestamp ON syslog_entries(asset_id, timestamp DESC) WHERE asset_id IS NOT NULL;
```

### 5.2 JSONB Indici (PostgreSQL)

```sql
-- Vulnerability affected_manufacturers
CREATE INDEX idx_vulnerabilities_manufacturers ON vulnerabilities USING GIN(affected_manufacturers);

-- Asset custom_fields (se usato frequentemente)
CREATE INDEX idx_assets_custom_fields ON assets USING GIN(custom_fields);
```

---

## 6. Relazioni e Dipendenze

### 6.1 Ordine di Creazione Modelli

```python
# backend/app/models/__init__.py

# 1. Core (no dipendenze)
from .tenant import Tenant
from .user import User
from .role import Role

# 2. Physical Organization
from .site import Site
from .area import Area
from .location import Location

# 3. Reference Data
from .manufacturer import Manufacturer
from .contact import Contact
from .supplier import Supplier

# 4. Asset Base
from .asset_type import AssetType
from .asset_status import AssetStatus
from .asset import Asset  # ⭐ Dipende da molti

# 5. Security (ISA/IEC 62443)
from .security_requirement import SecurityRequirement  # No dipendenze
from .security_zone import SecurityZone  # Dipende da Tenant, Site
from .conduit import Conduit  # Dipende da SecurityZone
from .security_requirement_compliance import SecurityRequirementCompliance  # Dipende da SecurityRequirement, SecurityZone, Asset

# 6. Asset Extensions
from .asset_dependency import AssetDependency  # Dipende da Asset
from .asset_vulnerability import AssetVulnerability  # Dipende da Asset, Vulnerability

# 7. Vulnerability
from .vulnerability import Vulnerability  # No dipendenze (system-wide)
from .vulnerability_feed_source import VulnerabilityFeedSource

# 8. Notification
from .notification_template import NotificationTemplate
from .notification_preference import NotificationPreference  # Dipende da User, Tenant
from .notification_queue import NotificationQueue  # Dipende da User, Tenant, NotificationTemplate
from .notification_log import NotificationLog

# 9. System
from .audit_log import AuditLog
from .tenant_smtp_config import TenantSMTPConfig
from .tenant_sso_config import TenantSSOConfig  # Futuro
```

### 6.2 Foreign Key Constraints

**Cascade Rules**:
- `Asset` → `CASCADE` su delete (cascade a dipendenze, vulnerabilità, etc.)
- `SecurityZone` → `SET NULL` su delete (asset mantiene riferimento)
- `Vulnerability` → `RESTRICT` su delete (non eliminare se referenziata)

---

## 7. Estensioni Modelli Esistenti

### 7.1 Asset Model - Modifiche

```python
# backend/app/models/asset.py

class Asset(Base):
    # ... campi esistenti ...
    
    # ISA/IEC 62443
    security_zone_id = Column(UUID, ForeignKey("security_zones.id"), nullable=True, index=True)
    security_level_target = Column(Integer, nullable=True)
    security_level_achieved = Column(Integer, nullable=True)
    isa62443_compliance_status = Column(String(20))
    isa62443_last_assessment = Column(DateTime)
    
    # Review
    last_review_date = Column(DateTime)
    next_review_date = Column(DateTime, index=True)
    review_status = Column(String(20), default="pending", index=True)
    review_notes = Column(Text)
    review_interval_months = Column(Integer, default=6)
    
    # Relationships nuove
    security_zone = relationship("SecurityZone", back_populates="assets")
    dependencies_as_dependent = relationship("AssetDependency", foreign_keys="AssetDependency.dependent_asset_id")
    dependencies_as_dependency = relationship("AssetDependency", foreign_keys="AssetDependency.dependency_asset_id")
    vulnerabilities = relationship("AssetVulnerability", back_populates="asset")
```

### 7.2 Tenant Model - Modifiche

```python
# backend/app/models/tenant.py

class Tenant(Base):
    # ... campi esistenti ...
    
    # Review config
    default_review_interval_months = Column(Integer, default=6)
```

### 7.3 Site Model - Modifiche

```python
# backend/app/models/site.py

class Site(Base):
    # ... campi esistenti ...
    
    # Review config
    review_interval_months = Column(Integer, nullable=True)
```

---

## 8. Servizi - Estensioni

### 8.1 Risk Scoring - Estensioni

```python
# backend/app/services/risk_scoring.py

class CompositeRiskScoringEngine:
    def calculate(self, asset, language="en") -> Dict[str, Any]:
        # ... calcolo esistente ...
        
        # ISA/IEC 62443 factors
        if asset.security_zone_id:
            zone = get_security_zone(asset.security_zone_id)
            sl_gap = zone.security_level_target - zone.security_level_achieved
            if sl_gap > 0:
                vuln_score += sl_gap * 0.5
        
        # Vulnerability factors
        unpatched_vulns = get_unpatched_vulnerabilities(asset.id)
        if unpatched_vulns:
            # ... logica vulnerabilità ...
        
        # Dependency risk propagation
        upstream_risk = self._calculate_upstream_risk(asset)
        if upstream_risk > 7.0:
            final_score = min(10, final_score + 0.5)
        
        return breakdown
```

### 8.2 Email Service - Estensioni

```python
# backend/app/services/email_service.py (esistente)

# Estendere per Notification System
class EmailService:
    def send_notification_email(self, notification: NotificationQueue) -> bool:
        """Invia email da notification queue"""
        pass
    
    def process_notification_queue(self, batch_size: int = 50):
        """Processa coda notifiche"""
        pass
```

---

## 9. Considerazioni Performance

### 9.1 Query Ottimizzate

**Asset Review Queries**:
```python
# Usare indici su next_review_date e review_status
assets_due = db.query(Asset).filter(
    Asset.tenant_id == tenant_id,
    Asset.deleted_at.is_(None),
    Asset.next_review_date <= today,
    Asset.review_status.in_(['pending', 'overdue'])
).all()
```

**Dependency Chain Queries**:
```python
# Usare CTE (Common Table Expression) per catene profonde
# Considerare caching per catene calcolate frequentemente
```

**Vulnerability Matching**:
```python
# Fuzzy matching può essere lento
# Considerare:
# - Background job per matching
# - Caching risultati matching
# - Batch processing
```

### 9.2 Caching Strategy

**Dashboard Cache** (già presente):
- Estendere per includere metriche ISA/IEC 62443
- Cache compliance status per zone

**Risk Score Cache**:
- Cache risk score calcolato (invalidare su cambiamenti asset)
- Cache dependency chains

**Vulnerability Matching Cache**:
- Cache risultati matching manufacturer/product
- TTL: 24 ore (aggiornare quando nuove vulnerabilità)

### 9.3 Background Jobs

**Scheduled Tasks** (usare Celery o APScheduler):
```python
# Asset Review Checks
@schedule.daily(at="09:00")
def check_asset_reviews():
    pass

# Vulnerability Feed Sync
@schedule.daily(at="02:00")
def sync_vulnerability_feeds():
    pass

# Notification Queue Processing
@schedule.every(1).hours
def process_notification_queue():
    pass

# Risk Score Recalculation
@schedule.every(6).hours
def recalculate_risk_scores():
    pass
```

---

## 10. Ordine di Implementazione Consigliato

### Fase 1: Foundation (Priorità Alta)
1. ✅ Asset Ownership (estendere asset_contacts con role)
2. ✅ Asset Review (campi Asset, servizio, API base)
3. ✅ Notification System (SMTP config esiste, estendere)

**Motivazione**: Feature semplici, alta utilità, bassa complessità

### Fase 2: ISA/IEC 62443 Core (Priorità Alta)
1. ✅ SecurityZone model e CRUD
2. ✅ Conduit model e CRUD
3. ✅ Asset assignment a zone
4. ✅ SecurityRequirement seed data
5. ✅ Compliance tracking base

**Motivazione**: Feature core per compliance industriale

### Fase 3: Asset Dependencies (Priorità Media)
1. ✅ AssetDependency model
2. ✅ DependencyChainAnalyzer
3. ✅ RiskPropagationEngine
4. ✅ UI visualization

**Motivazione**: Richiede Fase 1 e 2 per essere utile

### Fase 4: Vulnerability Intelligence (Priorità Media-Bassa)
1. ✅ Vulnerability model
2. ✅ NVD feed parser
3. ✅ VulnerabilityMatcher
4. ✅ Integration con risk scoring

**Motivazione**: Feature complessa, richiede feed esterni

### Fase 5: Advanced (Priorità Bassa)
1. ⏸️ Enterprise Auth (EntraID)
2. ⏸️ Remote Syslog
3. ⏸️ BAS/CS (on hold)

**Motivazione**: Feature avanzate, dipendono da maturità sistema

---

## 11. Checklist Implementazione

### Per Ogni Nuovo Modello

- [ ] Creare file modello in `backend/app/models/`
- [ ] Aggiungere import in `backend/app/models/__init__.py`
- [ ] Creare schema Pydantic in `backend/app/schemas/`
- [ ] Creare CRUD operations in `backend/app/crud/`
- [ ] Creare router in `backend/app/routers/`
- [ ] Creare servizio (se necessario) in `backend/app/services/`
- [ ] Creare migrazione Alembic
- [ ] Aggiungere indici per performance
- [ ] Test unitari
- [ ] Documentazione API

### Per Modifiche Modelli Esistenti

- [ ] Modificare modello
- [ ] Creare migrazione Alembic
- [ ] Aggiornare schema Pydantic
- [ ] Aggiornare CRUD (se necessario)
- [ ] Aggiornare router (se necessario)
- [ ] Test regressione

---

## 12. Note Finali

### 12.1 Compatibilità Retroattiva e Aggiornabilità

**Principio Fondamentale**: Il sistema deve essere sempre aggiornabile da qualsiasi versione precedente senza perdita di dati o funzionalità.

**Regole Critiche**:

1. **Migrazioni Sempre Incrementali**
   - Ogni migrazione deve funzionare indipendentemente dalla versione di partenza
   - Non assumere mai che una migrazione precedente sia stata applicata
   - Usare verifiche condizionali quando necessario

2. **Compatibilità Dati Esistenti**
   - Tutte le modifiche devono mantenere compatibilità con dati esistenti
   - Valori default appropriati per nuovi campi
   - Migrazione dati esistenti quando necessario

3. **Reversibilità**
   - Migrazioni devono essere reversibili (downgrade sempre implementato)
   - Documentare se downgrade comporta perdita di dati
   - Testare sempre upgrade → downgrade → re-upgrade

4. **Zero Downtime (quando possibile)**
   - Preferire migrazioni che non richiedono downtime
   - Aggiungere colonne nullable prima, poi popolare, poi rendere NOT NULL
   - Usare migrazioni multi-step per modifiche complesse

5. **Test Completo**
   - Test su database di sviluppo con dati reali
   - Test su staging prima di produzione
   - Test di rollback
   - Backup sempre prima di migrazioni in produzione

### 12.2 Testing

- Test unitari per ogni nuovo servizio
- Test integrazione per API endpoints
- Test performance per query complesse
- Test migrazioni (upgrade/downgrade)

### 12.3 Documentazione

- Aggiornare API documentation (OpenAPI/Swagger)
- Documentare nuovi modelli e relazioni
- Documentare nuovi servizi e algoritmi

---

**Status**: Draft - Analisi Completa  
**Last Updated**: 2025-12-04  
**Author**: AI Assistant per Maurizio Bertaboni

