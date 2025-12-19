# Asset Detail - Nuovo Design con 4 Macro-Sezioni

## Struttura Generale

Il layout è organizzato in **4 macro-sezioni principali** (schede di primo livello), ognuna con contenuti specifici e layout ottimizzato.

---

## 1. 📊 PANORAMICA

### Obiettivo
Rispondere alla domanda: **"Questa risorsa rappresenta un problema in questo momento?"**

### Contenuti
- **Status Dashboard** (sempre visibile)
  - Badge stato asset (Attivo/Inattivo/Manutenzione)
  - Badge criticità aziendale (Alta/Media/Bassa)
  - **Alert Banner** (se ci sono problemi critici)
    - Rischio totale > 7.0 → Banner rosso
    - Vulnerabilità critiche → Banner arancione
    - Dipendenze con problemi → Banner giallo
    - Nessun problema → Banner verde "Tutto OK"

- **Riepilogo Rischio** (sempre visibile)
  - Card con punteggio rischio totale (grande, colorato)
  - Breakdown rapido: Base + Dipendenze
  - Trend indicator (↑/↓/→) se disponibile storico

- **Info Principali** (sempre visibile)
  - Nome, Tipo, Sito, Area, Posizione
  - Produttore, Modello, Serial Number
  - Data installazione, Ultima manutenzione

- **Info Tecniche** (collassabile, default espanso)
  - Interfacce di rete (IP, MAC, VLAN)
  - Protocolli supportati
  - Livello Purdue
  - Accesso remoto/fisico

- **Quick Actions** (sempre visibile)
  - Pulsanti: Modifica, Stampa, Aggiungi Nota
  - Link rapidi: Vedi Dipendenze, Vedi Vulnerabilità

### Layout
```
┌─────────────────────────────────────────────────┐
│ [ALERT BANNER - se problemi critici]          │
├─────────────────────────────────────────────────┤
│ STATUS: [Badge] | CRITICITÀ: [Badge]          │
├─────────────────────────────────────────────────┤
│ RISCHIO TOTALE: [8.5] [Badge Rosso]           │
│ Base: 6.2 | Dipendenze: +2.3                   │
├─────────────────────────────────────────────────┤
│ INFO PRINCIPALI                                 │
│ Nome, Tipo, Sito, Area...                      │
├─────────────────────────────────────────────────┤
│ ▼ INFO TECNICHE (espanso)                      │
│ IP, MAC, Protocolli, Purdue...                 │
├─────────────────────────────────────────────────┤
│ [Modifica] [Stampa] [Aggiungi Nota]            │
└─────────────────────────────────────────────────┘
```

### Indicatori Visivi
- **Alert Banner**: Rosso (critico), Arancione (warning), Giallo (attenzione), Verde (OK)
- **Badge Rischio**: Colore in base al punteggio (0-3 verde, 3-6 giallo, 6-8 arancione, 8-10 rosso)
- **Badge Stato**: Verde (attivo), Grigio (inattivo), Giallo (manutenzione)
- **Contatori**: Numero vulnerabilità critiche, dipendenze problematiche

---

## 2. 🔗 RELAZIONI

### Obiettivo
Visualizzare connessioni e dipendenze in modo intuitivo, **prima il grafico, poi i dettagli**.

### Contenuti
- **Grafico Relazioni** (sempre visibile, grande)
  - Visualizzazione grafica delle dipendenze
  - Nodi: Asset corrente (centro) + Asset dipendenti/dipendenze
  - Collegamenti colorati per tipo dipendenza
  - Interattivo: click su nodo per vedere dettagli
  - Legenda tipi dipendenza

- **Riepilogo Relazioni** (sempre visibile, sotto grafico)
  - Card: "Dipende da X asset"
  - Card: "X asset dipendono da questo"
  - Card: "X connessioni di rete"
  - Card: "X comunicazioni attive"

- **Dipendenze** (tab/collassabile, default espanso)
  - Tabella asset da cui dipende
  - Tabella asset che dipendono da questo
  - Filtri per tipo dipendenza
  - Badge per dipendenze critiche

- **Connessioni di Rete** (tab/collassabile)
  - Tabella interfacce di rete
  - Collegamenti fisici
  - Topologia di rete semplificata

- **Comunicazioni** (tab/collassabile)
  - Tabella comunicazioni attive
  - Protocolli utilizzati
  - Porte e servizi

### Layout
```
┌─────────────────────────────────────────────────┐
│ GRAFICO RELAZIONI (grande, interattivo)        │
│                                                 │
│        [Asset A]                                │
│           |                                     │
│    [Asset Corrente] ← [Asset B]                │
│           |                                     │
│        [Asset C]                                │
│                                                 │
│ [Legenda: Critica | Alta | Media | Bassa]     │
├─────────────────────────────────────────────────┤
│ [4 Dipende da] [2 Dipendono] [3 Connessioni]   │
├─────────────────────────────────────────────────┤
│ ▼ DIPENDENZE (espanso)                         │
│ Tabella asset dipendenti...                     │
├─────────────────────────────────────────────────┤
│ ▶ CONNESSIONI DI RETE                          │
│ ▶ COMUNICAZIONI                                 │
└─────────────────────────────────────────────────┘
```

### Indicatori Visivi
- **Colori grafico**: Rosso (critica), Arancione (alta), Giallo (media), Verde (bassa)
- **Badge contatori**: Numero relazioni per tipo
- **Icone**: ⚠️ per dipendenze problematiche, ✓ per OK
- **Tooltip**: Hover su nodi per info rapide

---

## 3. 🛡️ SICUREZZA E RISCHI

### Obiettivo
Dettagli tecnici approfonditi su rischio, vulnerabilità e conformità IEC 62443.

### Contenuti
- **Dashboard Rischio** (sempre visibile)
  - Card grande: Rischio Totale con breakdown
  - Grafico a torta: Vulnerabilità / Impatto / Operativo
  - Indicatori: Trend, Confronto con media settore
  - Badge: Livello rischio (Basso/Medio/Alto/Critico)

- **Calcolo Rischio Base** (collassabile, default espanso)
  - Breakdown dettagliato vulnerabilità
  - Breakdown impatto
  - Breakdown operativo
  - Formula e spiegazione

- **Rischio da Dipendenze** (collassabile, default espanso)
  - Tabella asset da cui riceve rischio
  - Calcolo per ogni dipendenza
  - Totale rischio aggiunto

- **Propagazione Rischio** (collassabile)
  - Numero asset affetti
  - Selezione profondità propagazione
  - Tabella asset che ricevono rischio da questo
  - Calcolo rischio propagato

- **Vulnerabilità** (collassabile, default espanso)
  - Tabella vulnerabilità con severità
  - Filtri: Critiche, Alte, Medie, Basse
  - Badge: Numero vulnerabilità critiche
  - Link a dettagli CVE

- **Conformità IEC 62443** (collassabile)
  - Status conformità per zona
  - Requisiti soddisfatti / totali
  - Gap analysis
  - Roadmap conformità

### Layout
```
┌─────────────────────────────────────────────────┐
│ DASHBOARD RISCHIO                              │
│ [Rischio Totale: 8.5] [Grafico Torta]         │
│ Base: 6.2 | Dipendenze: +2.3                   │
├─────────────────────────────────────────────────┤
│ ▼ CALCOLO RISCHIO BASE (espanso)                │
│ Vulnerabilità: 4.5 | Impatto: 1.2 | Op: 0.5   │
├─────────────────────────────────────────────────┤
│ ▼ RISCHIO DA DIPENDENZE (espanso)              │
│ Tabella asset + calcolo...                     │
├─────────────────────────────────────────────────┤
│ ▶ PROPAGAZIONE RISCHIO                         │
│ ▶ VULNERABILITÀ (espanso)                      │
│ [3 Critiche] Tabella vulnerabilità...          │
├─────────────────────────────────────────────────┤
│ ▶ CONFORMITÀ IEC 62443                         │
└─────────────────────────────────────────────────┘
```

### Indicatori Visivi
- **Badge Rischio**: Colore in base al punteggio
- **Badge Vulnerabilità**: Rosso (critiche), Arancione (alte), Giallo (medie)
- **Progress Bar**: Conformità IEC 62443 (% requisiti soddisfatti)
- **Icone**: ⚠️ per problemi, ✓ per OK, 📊 per grafici

---

## 4. 📋 GESTIONE

### Obiettivo
Raggruppare contenuti relativi a governance, documentazione e audit.

### Contenuti
- **Riepilogo Gestione** (sempre visibile)
  - Card: "X documenti associati"
  - Card: "X contatti responsabili"
  - Card: "X fornitori"
  - Card: "Prossima review: [data]"
  - Badge: Status review (In scadenza / Scaduta / OK)

- **Documenti** (collassabile, default espanso)
  - Tabella documenti con tipo, data, versione
  - Upload/download documenti
  - Categorie: Manuali, Certificati, Schemi, Altro

- **Contatti e Responsabili** (collassabile, default espanso)
  - Tabella contatti con ruolo
  - Badge: Proprietario, Punto di contatto, Tecnico
  - Info contatto (email, telefono)

- **Fornitori** (collassabile)
  - Tabella fornitori associati
  - Contratti e garanzie
  - Info supporto

- **Review e Audit** (collassabile, default espanso)
  - Calendario review
  - Storico review passate
  - Prossima review programmata
  - Badge: In scadenza / Scaduta

- **Note e Campi Personalizzati** (collassabile)
  - Editor note (rich text)
  - Campi personalizzati definiti
  - Storico modifiche

- **Timeline** (collassabile)
  - Timeline eventi asset
  - Modifiche, review, manutenzioni
  - Filtri per tipo evento

### Layout
```
┌─────────────────────────────────────────────────┐
│ RIEPILOGO GESTIONE                             │
│ [5 Documenti] [3 Contatti] [2 Fornitori]      │
│ [Review: 15/02/2025] [Badge: OK]              │
├─────────────────────────────────────────────────┤
│ ▼ DOCUMENTI (espanso)                          │
│ Tabella documenti + upload...                  │
├─────────────────────────────────────────────────┤
│ ▼ CONTATTI E RESPONSABILI (espanso)           │
│ Tabella contatti...                            │
├─────────────────────────────────────────────────┤
│ ▼ REVIEW E AUDIT (espanso)                    │
│ Calendario + storico...                        │
├─────────────────────────────────────────────────┤
│ ▶ FORNITORI                                    │
│ ▶ NOTE E CAMPI PERSONALIZZATI                  │
│ ▶ TIMELINE                                    │
└─────────────────────────────────────────────────┘
```

### Indicatori Visivi
- **Badge Review**: Rosso (scaduta), Arancione (in scadenza), Verde (OK)
- **Contatori**: Numero documenti, contatti, fornitori
- **Icone**: 📄 documenti, 👤 contatti, 🏢 fornitori, 📅 review
- **Status**: Colori per stato review

---

## Navigazione tra Macro-Sezioni

### Layout Generale
```
┌─────────────────────────────────────────────────┐
│ ASSET HEADER (sempre visibile)                 │
│ Nome, Status, Criticità, Rischio               │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ [Panoramica] [Relazioni] [Sicurezza] [Gestione]│
│ ─────────────────────────────────────────────── │
│                                                 │
│ CONTENUTO MACRO-SEZIONE                        │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Comportamento
- **Tab di primo livello**: 4 tab principali (Panoramica, Relazioni, Sicurezza, Gestione)
- **Default**: Aprire sempre su "Panoramica"
- **Persistenza**: Ricordare ultima tab visitata (localStorage)
- **Breadcrumb**: Mostrare macro-sezione corrente

### Responsive
- Su mobile: Tab diventano menu dropdown
- Sezioni collassabili sempre collassabili
- Grafico relazioni: Scroll orizzontale se necessario

---

## Accessibilità

- **Skip Links**: Saltare al contenuto principale
- **ARIA Labels**: Ogni sezione con label appropriato
- **Navigazione Tastiera**: Tab order logico
- **Screen Reader**: Annunciare cambi sezione
- **High Contrast**: Supporto per tema ad alto contrasto

---

## Implementazione

### Componenti da Creare
1. `AssetDetailOverview.vue` - Macro-sezione Panoramica
2. `AssetDetailRelations.vue` - Macro-sezione Relazioni
3. `AssetDetailSecurity.vue` - Macro-sezione Sicurezza e Rischi
4. `AssetDetailManagement.vue` - Macro-sezione Gestione
5. `AssetRelationsGraph.vue` - Grafico relazioni
6. `AssetRiskDashboard.vue` - Dashboard rischio
7. `AssetAlertBanner.vue` - Banner alert problemi

### Componenti da Riutilizzare
- `AssetDetailHeader.vue` - Header asset
- `AssetDetailRiskTab.vue` - Componenti rischio (adattare)
- `AssetDetailDependenciesTab.vue` - Dipendenze (adattare)
- Altri componenti esistenti

