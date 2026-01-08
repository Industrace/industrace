# Guida alla Configurazione SSO con Azure AD (Microsoft 365)

Questa guida ti aiuterà a configurare l'autenticazione Single Sign-On (SSO) tra Industrace e Azure AD (Microsoft 365 / Entra ID).

## Prerequisiti

- Accesso amministratore a Microsoft Azure Portal
- Accesso amministratore a Industrace
- Tenant Microsoft 365 / Azure AD attivo

## Passo 1: Registrare l'Applicazione in Azure AD

### 1.1 Accedi al Azure Portal

1. Vai su [https://portal.azure.com](https://portal.azure.com)
2. Accedi con un account amministratore del tenant
3. Naviga su **Azure Active Directory** (o **Microsoft Entra ID**)

### 1.2 Registra una Nuova Applicazione

1. Nel menu laterale, seleziona **App registrations** (Registrazioni app)
2. Clicca su **+ New registration** (+ Nuova registrazione)
3. Compila il form:
   - **Name**: `Industrace SSO` (o un nome a tua scelta)
   - **Supported account types**: 
     - Seleziona **Accounts in this organizational directory only** (Solo account in questa directory organizzativa) per massima sicurezza
     - Oppure **Accounts in any organizational directory** se devi supportare più tenant
   - **Redirect URI**: 
     - Platform: **Web**
     - URI: `https://tuodominio.com/api/auth/sso/azure_ad/callback`
     - ⚠️ **IMPORTANTE**: Sostituisci `tuodominio.com` con il tuo dominio effettivo
     - Esempio: `https://industrace.local/api/auth/sso/azure_ad/callback` (per sviluppo locale)
     - Esempio: `https://app.industrace.com/api/auth/sso/azure_ad/callback` (per produzione)
4. Clicca su **Register** (Registra)

### 1.3 Annota le Informazioni dell'Applicazione

Dopo la registrazione, annota queste informazioni:

- **Application (client) ID**: Questo è il tuo `Client ID`
- **Directory (tenant) ID**: Questo è il tuo `Tenant Domain` (puoi usare anche il nome del tenant, es: `contoso.onmicrosoft.com`)

## Passo 2: Configurare l'Autenticazione

### 2.1 Configurare i Redirect URI

1. Nella pagina dell'applicazione, vai su **Authentication** (Autenticazione)
2. In **Redirect URIs**, aggiungi:
   - `https://tuodominio.com/api/auth/sso/azure_ad/callback`
   - `https://tuodominio.com/api/auth/sso/azure_ad/authorize` (opzionale, per redirect diretto)
3. In **Implicit grant and hybrid flows**, assicurati che:
   - ✅ **ID tokens** sia selezionato (necessario per OIDC)
   - ❌ **Access tokens** può essere deselezionato (non necessario per il flusso base)
4. Clicca su **Save** (Salva)

### 2.2 Configurare le API Permissions

1. Vai su **API permissions** (Autorizzazioni API)
2. Verifica che siano presenti:
   - **Microsoft Graph** > **openid** (Delegated) - ✅ Già presente
   - **Microsoft Graph** > **profile** (Delegated) - ✅ Già presente
   - **Microsoft Graph** > **email** (Delegated) - ✅ Già presente
   - **Microsoft Graph** > **User.Read** (Delegated) - Aggiungi se non presente
3. **IMPORTANTE**: Se devi importare utenti, aggiungi anche:
   - **Microsoft Graph** > **User.Read.All** (Application) - ⚠️ **OBBLIGATORIO** per importare utenti
   - Questo permesso deve essere di tipo **Application** (non Delegated) per funzionare con il client credentials flow
   - ⚠️ **Richiede il consenso dell'amministratore**
4. Clicca su **Grant admin consent** (Concedi consenso amministratore) - **OBBLIGATORIO** per i permessi Application
5. ⚠️ **Nota**: Senza il permesso **User.Read.All (Application)** e il consenso amministratore, l'importazione utenti non funzionerà

## Passo 3: Creare un Client Secret

### 3.1 Generare il Secret

1. Vai su **Certificates & secrets** (Certificati e segreti)
2. Nella sezione **Client secrets**, clicca su **+ New client secret**
3. Compila:
   - **Description**: `Industrace SSO Secret` (o un nome descrittivo)
   - **Expires**: Scegli una scadenza (consigliato: 24 mesi per produzione)
4. Clicca su **Add** (Aggiungi)
5. ⚠️ **IMPORTANTE**: Copia immediatamente il **Value** del secret (lo vedrai solo una volta!)
   - Questo è il tuo `Client Secret`

## Passo 4: Configurare Industrace

### 4.1 Accedi alla Configurazione SSO

1. Accedi a Industrace come amministratore
2. Vai su **SSO Config** (o **Configurazione SSO**)
3. Se non esiste ancora una configurazione, clicca su **Start Setup** (Inizia Configurazione)

### 4.2 Compilare il Form di Configurazione

Compila i seguenti campi:

- **Provider Type**: Seleziona `Azure AD (EntraID)`
- **Enabled**: Attiva quando sei pronto a testare
- **Client ID**: Incolla l'**Application (client) ID** dal Passo 1.3
- **Client Secret**: Incolla il **Value** del secret dal Passo 3.1
- **Tenant Domain**: 
  - Puoi usare il **Directory (tenant) ID** (UUID)
  - Oppure il nome del tenant (es: `contoso.onmicrosoft.com`)
  - Oppure `common` per supportare account Microsoft personali (non consigliato per enterprise)
- **Redirect URI**: 
  - Deve corrispondere esattamente a quello configurato in Azure AD
  - Esempio: `https://tuodominio.com/api/auth/sso/azure_ad/callback`
- **Auto-Provisioning**: 
  - ⚠️ **Consigliato: DISABILITATO** per massima sicurezza
  - Se disabilitato, solo gli utenti già esistenti in Industrace possono accedere
  - Gli utenti esistenti vengono collegati automaticamente se l'email corrisponde
- **Domain Restriction** (opzionale):
  - Esempio: `contoso.com` per permettere solo utenti da questo dominio

### 4.3 Testare la Connessione

1. Clicca su **Test Connection** (Test Connessione)
2. Se il test ha successo, procedi al passo successivo
3. Se fallisce, verifica:
   - Client ID e Client Secret corretti
   - Redirect URI corrisponde esattamente
   - Le API permissions sono configurate correttamente

### 4.4 Salvare la Configurazione

1. Clicca su **Save** (Salva)
2. Attiva **Enabled** se non l'hai già fatto
3. La configurazione è ora attiva!

## Passo 5: Importare Utenti (Opzionale)

### 5.1 Importare Utenti da Azure AD

1. Nella pagina SSO Config, vai sul tab **Import Users**
2. Cerca gli utenti che vuoi importare (puoi filtrare per nome o email)
3. Seleziona gli utenti che vuoi importare
4. Scegli il **Ruolo** da assegnare agli utenti importati
5. Clicca su **Import Selected** (Importa Selezionati)

### 5.2 Verificare gli Utenti Importati

1. Vai su **Users** (Utenti) in Industrace
2. Verifica che gli utenti siano stati creati correttamente
3. Gli utenti importati avranno:
   - Email corrispondente a quella in Azure AD
   - Ruolo assegnato durante l'importazione
   - `auth_provider` impostato su `azure_ad`

## Passo 6: Testare il Login SSO

### 6.1 Testare il Login

1. Esci da Industrace (logout)
2. Vai alla pagina di login
3. Dovresti vedere un pulsante **"Accedi con Microsoft"** (o simile)
4. Clicca sul pulsante
5. Verrai reindirizzato a Microsoft per l'autenticazione
6. Dopo l'autenticazione, verrai reindirizzato automaticamente a Industrace

### 6.2 Verificare il Collegamento Utente

1. Dopo il login SSO, vai su **Profile** (Profilo)
2. Verifica che l'utente sia stato collegato correttamente:
   - L'utente dovrebbe avere `auth_provider` = `azure_ad`
   - L'utente dovrebbe avere `external_id` popolato

## Troubleshooting

### Problema: "Invalid redirect URI"

**Causa**: Il Redirect URI in Industrace non corrisponde a quello configurato in Azure AD.

**Soluzione**: 
- Verifica che il Redirect URI in Industrace corrisponda esattamente a quello in Azure AD
- Controlla che non ci siano spazi o caratteri speciali
- Assicurati che il protocollo sia corretto (http vs https)

### Problema: "Invalid client secret"

**Causa**: Il Client Secret è scaduto o errato.

**Soluzione**:
- Genera un nuovo Client Secret in Azure AD
- Aggiorna la configurazione in Industrace con il nuovo secret

### Problema: "User not found" durante il login

**Causa**: L'utente non esiste in Industrace e l'auto-provisioning è disabilitato.

**Soluzione**:
- Importa l'utente manualmente tramite la funzionalità "Import Users"
- Oppure abilita l'auto-provisioning (non consigliato per sicurezza)

### Problema: "Domain restriction violation"

**Causa**: L'email dell'utente non corrisponde al dominio configurato in Domain Restriction.

**Soluzione**:
- Verifica il dominio dell'utente in Azure AD
- Aggiorna Domain Restriction per includere il dominio corretto
- Oppure rimuovi Domain Restriction se non necessario

### Problema: Il pulsante SSO non appare nella pagina di login

**Causa**: La configurazione SSO non è abilitata o non è configurata correttamente.

**Soluzione**:
- Verifica che `Enabled` sia attivo nella configurazione SSO
- Verifica che la configurazione sia stata salvata correttamente
- Controlla i log del backend per eventuali errori

### Problema: Errore 500 quando si cerca di elencare/importare utenti Azure AD

**Causa**: L'applicazione Azure AD non ha i permessi corretti o il consenso amministratore non è stato concesso.

**Soluzione**:
1. Verifica che il permesso **User.Read.All (Application)** sia stato aggiunto (non Delegated!)
2. Verifica che il **consenso amministratore** sia stato concesso (Grant admin consent)
3. Controlla i log del backend per vedere l'errore specifico:
   - Se vedi "Failed to authenticate" → problema con Client ID/Secret o tenant
   - Se vedi "Insufficient privileges" → manca il permesso User.Read.All (Application)
   - Se vedi "consent required" → manca il consenso amministratore
4. Dopo aver aggiunto i permessi, attendi qualche minuto prima di riprovare (Azure AD può richiedere tempo per propagare i permessi)

## Note Importanti

### Sicurezza

- ⚠️ **Mai condividere il Client Secret**: È un segreto sensibile
- ⚠️ **Usa HTTPS in produzione**: Il Redirect URI deve usare HTTPS
- ⚠️ **Auto-provisioning disabilitato**: Consigliato per massima sicurezza
- ⚠️ **Domain Restriction**: Usa per limitare l'accesso a domini specifici

### Best Practices

1. **Test in ambiente di sviluppo prima di produzione**
2. **Usa segreti con scadenza lunga** (24 mesi) per evitare interruzioni
3. **Documenta la configurazione** per il team
4. **Monitora i log** per eventuali problemi
5. **Mantieni aggiornati i segreti** prima della scadenza

## Supporto

Per problemi o domande:
- Consulta la documentazione di Azure AD: [https://docs.microsoft.com/azure/active-directory/](https://docs.microsoft.com/azure/active-directory/)
- Contatta il supporto Industrace

