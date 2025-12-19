# Sistema di Evidenze per Security Capabilities

## Panoramica

Il sistema di evidenze mostra quali asset nella zona supportano le capability richieste da un Security Requirement (SR). Le evidenze possono essere di tre tipi:

## Tipi di Evidenze

### 1. **Evidenze Esplicite (Verified/Declared)**

Queste sono evidenze **dichiarate manualmente** dall'utente tramite la tabella `asset_capabilities`.

**Come funzionano:**
- Un utente crea un record `AssetCapability` per un asset specifico
- Specifica il `support_level`: `'supported'`, `'not_supported'`, o `'unknown'`
- Può aggiungere `notes` e `evidence_ref` (riferimento a documenti, configurazioni, ecc.)

**Status nell'UI:**
- `status: 'verified'` → se `support_level == 'supported'` (✅ verde)
- `status: 'declared'` → se `support_level == 'not_supported'` o altri valori non-unknown (⚠️ arancione)
- `status: 'unknown'` → se `support_level == 'unknown'` (non viene mostrato)

**Esempio:**
```python
# Asset "PLC Controller B1" ha esplicitamente la capability "Session Locking"
AssetCapability(
    asset_id="...",
    capability_id="session_locking_timeout",
    support_level="supported",  # → status: 'verified'
    notes="PLC supports session timeout after 15 minutes",
    evidence_ref="config/plc_b1_security.json"
)
```

### 2. **Evidenze Inferite (Inferred)**

Queste sono evidenze **inferite automaticamente** dal sistema basandosi sul tipo di asset (`asset_type`).

**Come funzionano:**
- Il sistema controlla se il nome dell'`asset_type` corrisponde a uno dei `typical_roles` della capability
- Se c'è corrispondenza, crea un'evidenza inferita con `status: 'inferred'`
- Non c'è bisogno di creare manualmente un record `AssetCapability`

**Status nell'UI:**
- `status: 'inferred'` → evidenza inferita automaticamente (ℹ️ blu/grigio)

**Esempio:**
```python
# Capability "Session Locking" ha typical_roles: ['hmi']
# Asset "HMI Operator Station" ha asset_type.name = "HMI"
# → Il sistema inferisce che l'asset supporta la capability
# → Status: 'inferred'
```

**Mapping automatico:**
- `'plc'` → match con "PLC Controller", "Programmable Controller", ecc.
- `'hmi'` → match con "HMI", "Human Machine Interface", ecc.
- `'server'` → match con "Server", "SCADA Server", "Historian", ecc.
- `'firewall'` → match con "Firewall", "FW", ecc.
- `'rtu'` → match con "RTU", "Remote Terminal Unit", ecc.

### 3. **Evidenze da Conduit**

Le evidenze possono anche provenire da asset associati ai conduits (conduit assets).

**Come funzionano:**
- Un conduit può avere asset associati (tramite `ConduitAsset`)
- Questi asset vengono controllati per le capability che `applies_to_conduit == True`
- Le evidenze seguono le stesse regole (esplicite o inferite)

## Come Vengono Mostrate

Nell'endpoint `/compliance/zone/{zone_id}/sr/{sr_id}/assessment-assist`, le evidenze vengono restituite così:

```json
{
  "available_evidence": {
    "assets": [
      {
        "asset_id": "...",
        "asset_name": "PLC Controller B1",
        "asset_type": "PLC Controller",
        "capabilities": [
          {
            "capability": { "name": "Session Locking", ... },
            "asset_capability": { "support_level": "supported", ... },
            "status": "verified",  // o "declared" o "inferred"
            "source": "explicit"   // o "asset_type"
          }
        ],
        "status": "verified"  // o "declared" o "inferred"
      }
    ],
    "conduits": [...]
  }
}
```

## Come Creare Evidenze Esplicite

**Attualmente non c'è un endpoint API dedicato**, ma puoi creare `AssetCapability` direttamente nel database o tramite script.

**Struttura:**
```python
from app.models.asset_capability import AssetCapability
from app.crud import asset_capabilities as crud_asset_capabilities

# Creare un'evidenza esplicita
asset_capability = AssetCapability(
    tenant_id=tenant_id,
    asset_id=asset_id,
    capability_id=capability_id,
    support_level="supported",  # o "not_supported" o "unknown"
    notes="PLC supports session timeout",
    evidence_ref="config/plc_security.json"
)
db.add(asset_capability)
db.commit()
```

## Priorità delle Evidenze

1. **Evidenze Esplicite** hanno sempre priorità su quelle inferite
2. Se un asset ha sia evidenza esplicita che inferita per la stessa capability, viene mostrata solo quella esplicita
3. Le evidenze inferite vengono mostrate solo se non esiste un'evidenza esplicita

## Esempio Pratico

**Scenario:** Valutare SR 2.5 (Session Lock) per una zona con:
- Asset "PLC Controller B1" (tipo: "PLC Controller")
- Asset "HMI Station" (tipo: "HMI")

**Capability richiesta:** `session_locking_timeout` con `typical_roles: ['hmi']`

**Risultato:**
- **HMI Station**: Evidenza **inferita** (tipo "HMI" match con `typical_roles: ['hmi']`)
- **PLC Controller B1**: Nessuna evidenza (tipo "PLC" non match con `typical_roles: ['hmi']`)

**Se aggiungiamo un'evidenza esplicita per PLC:**
- **PLC Controller B1**: Evidenza **esplicita** (se `support_level == 'supported'` → `status: 'verified'`)

## Note Importanti

- Le evidenze **inferite** sono solo suggerimenti basati sul tipo di asset
- Le evidenze **esplicite** sono dichiarazioni verificate dall'utente
- Il sistema non crea automaticamente record `AssetCapability` per le evidenze inferite
- Le evidenze inferite sono solo per visualizzazione nella valutazione SR

