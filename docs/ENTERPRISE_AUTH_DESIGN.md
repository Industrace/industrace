# Enterprise Authentication - Design Document

## Overview

Implementazione di Enterprise Authentication (OAuth2/OIDC) per supportare SSO con EntraID/Azure AD, Google Workspace, Okta, e altri identity provider, mantenendo compatibilità completa con il sistema di autenticazione esistente (email/password).

## Obiettivi

1. **Coesistenza**: Supportare sia autenticazione locale (email/password) che SSO enterprise
2. **Auto-provisioning**: Creazione automatica utenti da identity provider
3. **"Connect" Workflow**: Setup semplificato per configurare SSO
4. **Multi-provider**: Supporto per più identity provider (Azure AD, Google, Okta, etc.)
5. **Backward Compatibility**: Utenti esistenti continuano a funzionare senza modifiche

---

## Architettura

### Modello Utente Esteso

```python
class User(Base):
    # Campi esistenti (mantenuti)
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"))
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # ⬅️ Diventa nullable
    name = Column(String(255), nullable=False)
    role_id = Column(UUID, ForeignKey("roles.id"))
    is_active = Column(Boolean, default=True)
    
    # Nuovi campi per SSO
    auth_provider = Column(String(50), nullable=True)  # 'local', 'azure_ad', 'google', 'okta'
    external_id = Column(String(255), nullable=True)  # ID utente nel provider esterno
    sso_email = Column(String(255), nullable=True)  # Email dal provider (può differire)
    last_sso_login = Column(DateTime, nullable=True)
    sso_metadata = Column(JSONB, nullable=True)  # Dati aggiuntivi dal provider
```

**Considerazioni**:
- `password_hash` diventa nullable: utenti SSO-only non hanno password
- `auth_provider` indica il metodo di autenticazione
- `external_id` per matching con identity provider
- `sso_email` può differire da `email` (es: UPN in Azure AD)

### Configurazione SSO per Tenant

```python
class TenantSSOConfig(Base):
    __tablename__ = "tenant_sso_config"
    
    tenant_id = Column(UUID, ForeignKey("tenants.id"), primary_key=True)
    
    # Provider Info
    provider_type = Column(String(50), nullable=False)  # 'azure_ad', 'google', 'okta'
    enabled = Column(Boolean, default=False)
    
    # OAuth2/OIDC Configuration
    client_id = Column(String(255), nullable=False)
    client_secret_encrypted = Column(String(500), nullable=False)  # Encrypted
    tenant_domain = Column(String(255), nullable=True)  # Per Azure AD
    authority_url = Column(String(500), nullable=True)  # OIDC discovery URL
    authorization_endpoint = Column(String(500), nullable=True)
    token_endpoint = Column(String(500), nullable=True)
    userinfo_endpoint = Column(String(500), nullable=True)
    
    # Scopes
    scopes = Column(JSONB, default=["openid", "profile", "email"])
    
    # Auto-provisioning
    auto_provision_enabled = Column(Boolean, default=True)
    default_role_id = Column(UUID, ForeignKey("roles.id"), nullable=True)  # Role per nuovi utenti
    domain_restriction = Column(String(255), nullable=True)  # Solo utenti da questo dominio
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(UUID, ForeignKey("users.id"), nullable=True)
```

---

## Workflow di Autenticazione

### 1. Login Locale (Esistente - Mantenuto)

```
POST /login
Body: { email, password }

1. Verifica email/password
2. Genera JWT token
3. Return token
```

**Nessuna modifica necessaria** - continua a funzionare come prima.

### 2. Login SSO (Nuovo)

```
GET /auth/sso/{provider}/authorize
→ Redirect a identity provider

GET /auth/sso/{provider}/callback
→ Identity provider redirect con code
→ Exchange code per token
→ Get user info
→ Create/update user
→ Generate JWT token
→ Redirect a frontend con token
```

### 3. Coesistenza

**Scenario 1: Utente solo locale**
- `auth_provider = 'local'`
- `password_hash != NULL`
- Login solo via `/login`

**Scenario 2: Utente solo SSO**
- `auth_provider = 'azure_ad'` (o altro)
- `password_hash = NULL`
- Login solo via SSO flow

**Scenario 3: Utente ibrido** (migrazione graduale)
- `auth_provider = 'local'` (o può essere cambiato)
- `password_hash != NULL`
- `external_id != NULL`
- Può usare entrambi i metodi

---

## Auto-Provisioning

### Logica di Matching

Quando un utente fa login SSO per la prima volta:

1. **Cerca utente esistente**:
   - Per `external_id` (se già collegato)
   - Per `email` (se email match)
   - Per `sso_email` (se sso_email match)

2. **Se trovato**:
   - Aggiorna `external_id`, `sso_email`, `last_sso_login`
   - Aggiorna `auth_provider` se era 'local'
   - Login completato

3. **Se non trovato** (auto-provisioning):
   - Verifica `auto_provision_enabled` in TenantSSOConfig
   - Verifica `domain_restriction` (se configurato)
   - Crea nuovo utente:
     - `email` = email dal provider
     - `name` = name dal provider
     - `auth_provider` = provider_type
     - `external_id` = sub/id dal provider
     - `password_hash` = NULL
     - `role_id` = default_role_id (o 'viewer' se non configurato)
     - `tenant_id` = tenant corrente
   - Login completato

### Domain Restriction

```python
# Esempio: Solo utenti da dominio aziendale
domain_restriction = "company.com"
# Permette solo email@company.com
```

---

## "Connect" Workflow Semplificato

### Step 1: Inizio Setup

```
POST /auth/sso/connect/start
Body: { provider_type: 'azure_ad' }

→ Genera state, code_verifier (PKCE)
→ Return:
  {
    "authorization_url": "https://login.microsoftonline.com/...",
    "state": "...",
    "code_verifier": "..."
  }
```

### Step 2: Redirect Utente

Frontend redirecta utente a `authorization_url`.

### Step 3: Callback e Setup

```
GET /auth/sso/connect/callback
Query: { code, state, ... }

→ Verifica state
→ Exchange code per token
→ Get tenant info (per Azure AD: tenant ID)
→ Get user info
→ Salva configurazione in TenantSSOConfig
→ Return success
```

### Step 4: Test Connection

```
POST /auth/sso/{tenant_id}/test
→ Testa connessione con identity provider
→ Return status
```

---

## Implementazione Tecnica

### Librerie Python

```python
# OAuth2/OIDC
from authlib.integrations.starlette_client import OAuth
# o
from fastapi_users import FastAPIUsers
# o
import httpx  # Per chiamate manuali
```

### Service: SSOAuthService

```python
class SSOAuthService:
    @staticmethod
    def get_authorization_url(
        tenant_id: UUID,
        provider_type: str,
        redirect_uri: str
    ) -> str:
        """Genera URL di autorizzazione"""
        pass
    
    @staticmethod
    def handle_callback(
        code: str,
        state: str,
        tenant_id: UUID,
        provider_type: str
    ) -> Dict:
        """Gestisce callback OAuth"""
        pass
    
    @staticmethod
    def get_user_info(
        access_token: str,
        provider_type: str,
        config: TenantSSOConfig
    ) -> Dict:
        """Ottiene info utente da identity provider"""
        pass
    
    @staticmethod
    def find_or_create_user(
        db: Session,
        user_info: Dict,
        tenant_id: UUID,
        config: TenantSSOConfig
    ) -> User:
        """Trova o crea utente"""
        pass
```

### Provider-Specific Implementation

#### Azure AD / EntraID

```python
# Discovery URL
authority = f"https://login.microsoftonline.com/{tenant_domain}/v2.0"
discovery_url = f"{authority}/.well-known/openid-configuration"

# Scopes
scopes = ["openid", "profile", "email", "User.Read"]

# User Info
# Claims: sub, email, name, preferred_username, etc.
```

#### Google Workspace

```python
# Discovery URL
discovery_url = "https://accounts.google.com/.well-known/openid-configuration"

# Scopes
scopes = ["openid", "profile", "email"]

# User Info
# Claims: sub, email, name, picture, etc.
```

#### Okta

```python
# Discovery URL
discovery_url = f"https://{okta_domain}/.well-known/openid-configuration"

# Scopes
scopes = ["openid", "profile", "email"]

# User Info
# Claims: sub, email, name, etc.
```

---

## Migrazione Utenti Esistenti

### Strategia 1: Coesistenza (Raccomandato)

- Utenti esistenti continuano con password
- Nuovi utenti possono essere creati via SSO
- Utenti esistenti possono collegare account SSO (opzionale)

**Vantaggi**:
- Zero downtime
- Nessuna interruzione per utenti esistenti
- Migrazione graduale

### Strategia 2: Linking Manuale

Admin può collegare utente esistente a account SSO:

```
POST /users/{user_id}/link-sso
Body: { external_id, provider_type }

→ Aggiorna user.auth_provider, user.external_id
→ Utente può ora usare SSO
→ Password rimane (per fallback)
```

### Strategia 3: Migrazione Bulk

Script per migrare tutti gli utenti di un tenant:

```python
# Per ogni utente:
# 1. Cerca utente in Azure AD per email
# 2. Se trovato, aggiorna user con external_id
# 3. Opzionale: disabilita password (force SSO)
```

---

## API Endpoints

### SSO Authentication

```python
# Authorization
GET /auth/sso/{provider}/authorize
→ Redirect a identity provider

# Callback
GET /auth/sso/{provider}/callback
→ Gestisce OAuth callback
→ Crea/aggiorna utente
→ Genera JWT
→ Redirect a frontend

# Connect/Setup
POST /auth/sso/connect/start
POST /auth/sso/connect/callback
GET /auth/sso/{tenant_id}/config
PUT /auth/sso/{tenant_id}/config
POST /auth/sso/{tenant_id}/test
DELETE /auth/sso/{tenant_id}/config
```

### User Management

```python
# Link SSO to existing user
POST /users/{user_id}/link-sso
Body: { external_id, provider_type }

# Unlink SSO
DELETE /users/{user_id}/unlink-sso

# Get user auth methods
GET /users/{user_id}/auth-methods
→ Return: { "local": true, "sso": ["azure_ad"] }
```

---

## Frontend Integration

### Login Page

```vue
<template>
  <div>
    <!-- Login locale (esistente) -->
    <form @submit="loginLocal">
      <input v-model="email" />
      <input v-model="password" type="password" />
      <button>Login</button>
    </form>
    
    <!-- SSO Login -->
    <div v-if="ssoEnabled">
      <button @click="loginSSO('azure_ad')">
        Login with Microsoft
      </button>
      <button @click="loginSSO('google')">
        Login with Google
      </button>
    </div>
  </div>
</template>
```

### SSO Flow

```javascript
async function loginSSO(provider) {
  // Redirect a backend
  window.location.href = `/api/auth/sso/${provider}/authorize?tenant_id=${tenantId}`
}

// Callback gestito automaticamente da backend
// Redirect a frontend con token in query param o cookie
```

---

## Sicurezza

### Client Secret Encryption

```python
from cryptography.fernet import Fernet

def encrypt_secret(secret: str) -> str:
    key = settings.ENCRYPTION_KEY  # Da env
    f = Fernet(key)
    return f.encrypt(secret.encode()).decode()

def decrypt_secret(encrypted: str) -> str:
    key = settings.ENCRYPTION_KEY
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()
```

### PKCE (per public clients)

```python
import secrets
import base64
import hashlib

def generate_pkce():
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode().rstrip('=')
    
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    return code_verifier, code_challenge
```

### State Validation

```python
# Genera state random per ogni request
state = secrets.token_urlsafe(32)
# Salva in session/redis con expiry
# Verifica al callback
```

---

## Testing

### Test Scenarios

1. **Login locale** (utente esistente)
2. **Login SSO** (utente nuovo - auto-provisioning)
3. **Login SSO** (utente esistente - linking)
4. **Coesistenza** (utente può usare entrambi)
5. **Domain restriction** (solo domini autorizzati)
6. **Auto-provisioning disabled** (blocca nuovi utenti)

---

## Deployment Considerations

### Environment Variables

```bash
# Encryption key per client secrets
ENCRYPTION_KEY=...

# Redirect URIs
SSO_REDIRECT_URI=https://app.example.com/auth/sso/callback

# Provider-specific (opzionale, può essere per-tenant)
AZURE_AD_CLIENT_ID=...
AZURE_AD_CLIENT_SECRET=...
```

### Database Migration

```python
# 1. Aggiungi campi SSO a User
# 2. Rendi password_hash nullable
# 3. Crea TenantSSOConfig table
# 4. Popola auth_provider='local' per utenti esistenti
```

---

## Roadmap Implementazione

### Fase 1: Foundation
- Modelli database (User esteso, TenantSSOConfig)
- Migrazione database
- Base SSOAuthService

### Fase 2: Azure AD Integration
- Implementazione Azure AD specifica
- OAuth2/OIDC flow
- Auto-provisioning

### Fase 3: Connect Workflow
- Setup semplificato
- Test connection
- UI per configurazione

### Fase 4: Multi-Provider
- Google Workspace
- Okta
- Generic OIDC

### Fase 5: Advanced Features
- User linking/unlinking
- Migration tools
- Audit logging per SSO

---

## Esempio Pratico

### Scenario: Tenant vuole abilitare Azure AD

1. **Admin va su Settings → SSO**
2. **Clicca "Connect Azure AD"**
3. **Redirect a Microsoft** (consenso app)
4. **Callback → Config salvata**
5. **Test connection** → OK
6. **Enable SSO** → Attivo

### Scenario: Utente fa login

1. **Utente va su login page**
2. **Vede "Login with Microsoft"**
3. **Clicca → Redirect a Microsoft**
4. **Login Microsoft**
5. **Callback → Utente creato/aggiornato**
6. **JWT generato → Login completato**

### Scenario: Utente esistente

1. **Utente esistente (email/password)**
2. **Admin collega account** (o utente stesso)
3. **Utente può ora usare SSO**
4. **Password rimane** (per fallback)

---

## Note Importanti

1. **Backward Compatibility**: Tutti gli utenti esistenti continuano a funzionare
2. **Password Opzionale**: Utenti SSO-only non hanno password
3. **Email Matching**: Matching per email permette linking automatico
4. **Domain Restriction**: Importante per sicurezza (solo domini autorizzati)
5. **Auto-provisioning**: Può essere disabilitato per controllo manuale
6. **Multi-tenant**: Ogni tenant può avere configurazione SSO diversa

