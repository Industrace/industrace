# Security Review Report - Industrace
**Data Review**: Gennaio 2025  
**Ultimo Aggiornamento**: Gennaio 2025 (Verifica stato implementazione)  
**Versione Sistema**: 1.0.0  
**Reviewer**: Security Audit

---

## 📊 Riepilogo Stato Implementazione

| Vulnerabilità | Severità | Stato | Priorità |
|--------------|----------|-------|----------|
| 1. CORS Handler Eccezioni | 🔴 Critica | ✅ Risolto | - |
| 2. Rate Limiting | 🔴 Critica | ✅ Risolto | - |
| 3. File Upload Validation | 🟠 Media | ❌ Non Risolto | Alta |
| 4. Query ILIKE Sanitization | 🟠 Media | ❌ Non Risolto | Media |
| 5. Security Headers | 🟠 Media | ❌ Non Risolto | Alta |
| 6. Gestione Errori | 🟠 Media | ✅ Risolto | - |
| 7. Password Policy | 🟠 Media | ⚠️ Parzialmente Risolto | Media |
| 8. Cookie SameSite | 🟠 Media | ⚠️ Parzialmente Risolto | Bassa |

**Legenda**: ✅ Risolto | ⚠️ Parzialmente Risolto | ❌ Non Risolto

---

## Executive Summary

Questa review ha identificato **8 vulnerabilità critiche/medie** e **5 raccomandazioni** per migliorare la sicurezza complessiva del sistema. Il codice mostra una buona base di sicurezza con autenticazione JWT, RBAC, e validazione input, ma presenta alcune aree che richiedono attenzione immediata.

**Ultimo aggiornamento**: Gennaio 2025 - Verifica stato implementazione

### Riepilogo Rischi
- 🔴 **Critico**: 2 vulnerabilità (1 parzialmente risolta, 1 non risolta)
- 🟠 **Medio**: 6 vulnerabilità (1 parzialmente risolta, 5 non risolte)  
- 🟡 **Basso**: 5 raccomandazioni (non implementate)

---

## 🔴 Vulnerabilità Critiche

### 1. CORS Configurazione Permissiva
**Severità**: CRITICA  
**File**: `backend/app/main.py`  
**Stato**: ✅ **RISOLTO** (Gennaio 2025)

**Problema**:
```python
headers={
    "Access-Control-Allow-Origin": "*",
    ...
}
```

L'header CORS era impostato su `*` negli handler di eccezioni, permettendo richieste da qualsiasi origine. Questo può esporre l'API a attacchi CSRF e permettere accesso non autorizzato.

**Soluzione Implementata**:
- ✅ Creata funzione helper `get_cors_origin()` che determina l'origine corretta basandosi sulla richiesta
- ✅ Creata funzione `get_cors_headers()` che genera header CORS sicuri usando le origini configurate
- ✅ Sostituito `"*"` con origine configurata in tutti gli handler di eccezioni:
  - `RequestValidationError` handler
  - `ValidationError` handler  
  - `ErrorCodeException` handler
  - `Exception` handler (generico)
- ✅ La funzione verifica se l'origine della richiesta è nella lista permessa e la usa, altrimenti usa la prima origine configurata come fallback sicuro

**Nota**: Il CORS principale era già configurato correttamente con `CORSMiddleware` alle linee 123-129 usando `settings.CORS_ORIGINS.split(",")`. Ora anche gli handler di eccezioni usano le stesse origini configurate.

**Impatto**: 
- Attacchi CSRF
- Accesso non autorizzato da domini esterni
- Violazione Same-Origin Policy

**Raccomandazione**:
```python
# Usa le origini configurate invece di "*"
allowed_origins = settings.CORS_ORIGINS.split(",")
origin = request.headers.get("origin")
if origin in allowed_origins:
    headers["Access-Control-Allow-Origin"] = origin
else:
    headers["Access-Control-Allow-Origin"] = allowed_origins[0] if allowed_origins else ""
```

---

### 2. Rate Limiting Non Funzionante
**Severità**: CRITICA  
**File**: `backend/app/services/rate_limiter.py`  
**Stato**: ✅ **RISOLTO** (Gennaio 2025)

**Problema**:
```python
def check_rate_limit(request: Request, api_key=None) -> bool:
    # Implementazione semplificata del rate limiting
    # In produzione, usa Redis o un database per il tracking
    return True  # Per ora, sempre permesso
```

Il rate limiting è dichiarato ma non implementato. La funzione ritorna sempre `True`, permettendo attacchi brute force e DoS.

**Soluzione Implementata**:
- ✅ Implementato rate limiting reale usando Redis con sliding window
- ✅ Fallback in-memory quando Redis non è disponibile
- ✅ Aggiunto rate limiting strict (10/minute) all'endpoint `/login` per prevenire brute force
- ✅ Configurazione Redis aggiunta in `config.py` (REDIS_URL, REDIS_ENABLED)
- ✅ Headers di rate limiting aggiunti alle risposte (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- ✅ Rate limiting già integrato negli endpoint external API

**Impatto**:
- Attacchi brute force su login
- DoS (Denial of Service)
- Abuso API senza limiti

**Raccomandazione**:
Implementare rate limiting reale usando Redis o database:
```python
from redis import Redis
import time

redis_client = Redis(host='localhost', port=6379, db=0)

def check_rate_limit(request: Request, api_key=None) -> bool:
    identifier = get_client_identifier(request, api_key)
    rate_limit = get_rate_limit_for_api_key(api_key)
    
    limit_str, period = rate_limit.split("/")
    limit = int(limit_str)
    
    # Usa sliding window o token bucket
    key = f"rate_limit:{identifier}"
    current = redis_client.incr(key)
    
    if current == 1:
        if period == "minute":
            redis_client.expire(key, 60)
        elif period == "hour":
            redis_client.expire(key, 3600)
    
    return current <= limit
```

---

## 🟠 Vulnerabilità Medie

### 3. Validazione File Upload Insufficiente
**Severità**: MEDIA  
**File**: `backend/app/routers/asset_photos.py:31`, `asset_documents.py:44`  
**Stato**: ❌ **NON RISOLTO**

**Problema**:
La validazione si basa solo su `content_type` che può essere facilmente falsificato. Non c'è validazione del contenuto reale del file.

**Esempio**:
```python
if file.content_type not in ["image/jpeg", "image/png"]:
    raise ErrorCodeException(...)
```

**Nota**: La validazione attuale controlla solo il `content_type` fornito dal client, che può essere facilmente manipolato. Non c'è verifica del magic number o del contenuto reale del file.

**Impatto**:
- Upload di file malevoli mascherati come immagini
- Possibile esecuzione di codice se i file vengono processati
- Storage di file non validi

**Raccomandazione**:
```python
import magic  # python-magic
from PIL import Image

def validate_image_file(file: UploadFile) -> bool:
    # Verifica MIME type reale
    file_content = file.file.read(1024)
    file.file.seek(0)
    
    mime_type = magic.from_buffer(file_content, mime=True)
    if mime_type not in ["image/jpeg", "image/png"]:
        return False
    
    # Verifica che sia un'immagine valida
    try:
        img = Image.open(file.file)
        img.verify()
        file.file.seek(0)
        return True
    except Exception:
        return False
```

---

### 4. Query ILIKE con Input Utente
**Severità**: MEDIA  
**File**: `backend/app/routers/search.py:47-51`  
**Stato**: ❌ **NON RISOLTO**

**Problema**:
Le query usano `ilike(f"%{query}%")` con input utente. Anche se SQLAlchemy protegge da SQL injection, pattern complessi possono causare performance issues o ReDoS.

**Esempio**:
```python
Asset.name.ilike(f"%{query}%")
```

**Nota**: Il codice attuale usa direttamente l'input utente senza sanitizzazione. Le query sono limitate a 5-20 risultati, ma non c'è limitazione sulla lunghezza della query stessa.

**Impatto**:
- ReDoS (Regular Expression Denial of Service) se usati pattern complessi
- Performance degradation con query molto lunghe

**Raccomandazione**:
```python
# Limita lunghezza query
if len(query) > 100:
    query = query[:100]

# Escape caratteri speciali per LIKE
query = query.replace("%", "\\%").replace("_", "\\_")

# Usa full-text search invece di ILIKE per performance migliori
from sqlalchemy import func
Asset.name.ilike(func.escape(query))
```

---

### 5. Mancanza di Security Headers nell'Applicazione
**Severità**: MEDIA  
**File**: `backend/app/main.py`  
**Stato**: ❌ **NON RISOLTO**

**Problema**:
I security headers sono configurati solo in nginx, non nell'applicazione FastAPI. Se nginx viene bypassato o non è presente, l'applicazione non ha protezioni.

**Nota**: Non è stato trovato alcun middleware per security headers nell'applicazione FastAPI. I headers sono gestiti solo a livello nginx.

**Impatto**:
- XSS attacks
- Clickjacking
- MIME type sniffing

**Raccomandazione**:
Aggiungere middleware per security headers:
```python
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

---

### 6. Gestione Errori che Espone Informazioni
**Severità**: MEDIA  
**File**: `backend/app/main.py:687-704`  
**Stato**: ✅ **RISOLTO**

**Problema**:
Anche se c'è un handler generico, in modalità DEBUG potrebbero essere esposte informazioni sensibili negli stack trace.

**Nota**: L'handler generico alle linee 687-704 ritorna sempre un messaggio generico "Errore interno del server" senza esporre dettagli, anche se non controlla esplicitamente `settings.DEBUG`. Il logging completo avviene solo lato server.

**Impatto**:
- Esposizione di percorsi file system
- Informazioni su struttura database
- Dettagli implementazione

**Raccomandazione**:
```python
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log completo per debugging interno
    logger.error(f"Error 500 on {request.url}: {exc}", exc_info=True)
    
    # Risposta generica per utente
    if settings.DEBUG:
        # In sviluppo, mostra dettagli
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "detail": str(exc)}
        )
    else:
        # In produzione, solo messaggio generico
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "detail": "Errore interno del server"}
        )
```

---

### 7. Validazione Password Potenzialmente Debole
**Severità**: MEDIA  
**File**: `backend/app/schemas/validators.py:212-218`  
**Stato**: ⚠️ **PARZIALMENTE RISOLTO**

**Problema**:
La validazione password esiste ma è debole. Richiede solo minimo 8 caratteri, senza requisiti per maiuscole, numeri o caratteri speciali.

**Nota**: La funzione `validate_password` in `backend/app/schemas/validators.py` controlla solo la lunghezza minima (8 caratteri). Non richiede maiuscole, minuscole, numeri o caratteri speciali, rendendo le password vulnerabili a brute force.

**Impatto**:
- Password deboli vulnerabili a brute force
- Possibile compromissione account

**Raccomandazione**:
Implementare validazione password forte:
```python
import re

def validate_password_strength(password: str) -> bool:
    """
    Valida che la password rispetti:
    - Minimo 12 caratteri
    - Almeno una maiuscola
    - Almeno una minuscola
    - Almeno un numero
    - Almeno un carattere speciale
    """
    if len(password) < 12:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True
```

---

### 8. Cookie SameSite Potenzialmente Permissivo
**Severità**: MEDIA  
**File**: `backend/app/config.py:49`  
**Stato**: ⚠️ **PARZIALMENTE RISOLTO**

**Problema**:
Il default per `SAME_SITE_COOKIES` è "lax", che può essere bypassato in alcuni scenari. In produzione dovrebbe essere "strict".

**Nota**: Il default è "lax" (linea 49). La funzione `_validate_security_settings` (linee 85-95) valida `SECURE_COOKIES` in produzione ma non verifica che `SAME_SITE_COOKIES` sia "strict".

**Impatto**:
- CSRF attacks in alcuni scenari
- Cross-site cookie access

**Raccomandazione**:
```python
# In config.py, validare che in produzione sia "strict"
def _validate_security_settings(self):
    if self.ENVIRONMENT == "production":
        if self.SAME_SITE_COOKIES != "strict":
            raise ValueError("SAME_SITE_COOKIES must be 'strict' in production")
```

---

## 🟡 Raccomandazioni di Miglioramento

### 9. Implementare Content Security Policy (CSP)
**Priorità**: ALTA

Aggiungere CSP headers per prevenire XSS:
```python
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none';"
)
```

---

### 10. Implementare Logging di Sicurezza
**Priorità**: MEDIA

Aggiungere logging specifico per eventi di sicurezza:
- Tentativi di login falliti
- Accessi non autorizzati
- Modifiche a permessi
- Uso di API keys

---

### 11. Implementare Account Lockout
**Priorità**: MEDIA

Dopo N tentativi di login falliti, bloccare temporaneamente l'account:
```python
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Nel login endpoint
if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise ErrorCodeException(
            status_code=403,
            error_code="ACCOUNT_LOCKED",
            detail=f"Account locked until {user.locked_until}"
        )
```

---

### 12. Validazione Dimensione File Upload
**Priorità**: MEDIA

Verificare che la validazione della dimensione sia applicata prima di salvare il file:
```python
# Verifica dimensione PRIMA di processare
if file.size > settings.MAX_FILE_SIZE:
    raise ErrorCodeException(...)

# Per file stream, verifica durante il caricamento
total_size = 0
chunk_size = 8192
while True:
    chunk = await file.read(chunk_size)
    if not chunk:
        break
    total_size += len(chunk)
    if total_size > settings.MAX_FILE_SIZE:
        raise ErrorCodeException(...)
```

---

### 13. Implementare Secret Rotation
**Priorità**: BASSA

Implementare rotazione automatica per:
- API Keys
- JWT secret keys (con supporto per multiple keys)
- Encryption keys

---

## ✅ Punti di Forza

Il sistema mostra diverse buone pratiche di sicurezza:

1. **Autenticazione JWT**: Implementazione corretta con validazione audience/issuer
2. **Password Hashing**: Uso di bcrypt con CryptContext
3. **RBAC**: Sistema di permessi granulare implementato
4. **Input Validation**: Uso di Pydantic per validazione schema
5. **SQL Injection Protection**: Uso di SQLAlchemy ORM
6. **Audit Logging**: Tracciamento delle operazioni critiche
7. **Sanitizzazione**: Uso di bleach per sanitizzazione input
8. **Tenant Isolation**: Separazione dati per tenant
9. **HTTPS Enforcement**: Configurato in nginx per produzione
10. **Secure Cookies**: Configurazione corretta per produzione

---

## Piano di Azione Prioritario

### Fase 1 - Critico (Immediato)
1. ✅ Fix CORS configuration nell'handler eccezioni (1-2 ore) - **RISOLTO** (Gennaio 2025)
2. ✅ Implementare rate limiting reale (4-8 ore) - **RISOLTO** (Gennaio 2025)
3. ❌ Aggiungere security headers middleware (2-4 ore) - **NON RISOLTO**

### Fase 2 - Medio (1 settimana)
4. ❌ Migliorare validazione file upload (4-6 ore) - **NON RISOLTO**
5. ❌ Sanitizzare query ILIKE (2-3 ore) - **NON RISOLTO**
6. ✅ Migliorare gestione errori (2-3 ore) - **RISOLTO**
7. ⚠️ Implementare password policy forte (2-4 ore) - **PARZIALMENTE RISOLTO** (solo lunghezza minima)

### Fase 3 - Miglioramenti (2 settimane)
8. ❌ Implementare CSP (2-3 ore) - **NON RISOLTO**
9. ❌ Aggiungere security logging (4-6 ore) - **NON RISOLTO**
10. ❌ Implementare account lockout (3-4 ore) - **NON RISOLTO**

### Stato Implementazione
- ✅ **Risolto**: 3 vulnerabilità (Gestione Errori, Rate Limiting, CORS)
- ⚠️ **Parzialmente Risolto**: 2 vulnerabilità (Password Policy, SameSite)
- ❌ **Non Risolto**: 3 vulnerabilità medie + 5 raccomandazioni

---

## Testing di Sicurezza Consigliato

1. **Penetration Testing**: Test manuali su endpoint critici
2. **Dependency Scanning**: `pip-audit` o `safety check`
3. **SAST**: Static Application Security Testing
4. **DAST**: Dynamic Application Security Testing
5. **OWASP ZAP**: Automated security scanning

---

## Conclusioni

Il sistema Industrace ha una base di sicurezza solida, ma presenta alcune vulnerabilità critiche che devono essere risolte prima della produzione. 

### Stato Attuale (Gennaio 2025)
- **3 vulnerabilità risolte**: Gestione errori, Rate limiting (con Redis + fallback in-memory), CORS (handler eccezioni)
- **2 vulnerabilità parzialmente risolte**: Password policy (solo lunghezza), SameSite cookies (validazione mancante)
- **3 vulnerabilità medie non risolte**: File upload validation, Query ILIKE sanitization, Security headers
- **5 raccomandazioni non implementate**: CSP, Security logging, Account lockout, File size validation, Secret rotation

### Priorità Immediate
Le principali aree di miglioramento sono:

1. **Security Headers**: Implementare middleware a livello applicazione (MEDIO)
3. **Security Headers**: Implementazione middleware a livello applicazione (MEDIO)
4. **File Upload**: Validazione più robusta con magic number verification (MEDIO)
5. **Query ILIKE**: Sanitizzazione input per prevenire ReDoS (MEDIO)
6. **Password Policy**: Requisiti più forti (maiuscole, numeri, caratteri speciali) (MEDIO)

Con le correzioni proposte, il sistema raggiungerà un livello di sicurezza adeguato per un ambiente di produzione enterprise.

---

**Prossimi Passi**:
1. Review e approvazione di questo report
2. Priorizzazione delle vulnerabilità
3. Implementazione delle fix critiche
4. Re-test dopo le correzioni
5. Documentazione delle modifiche
