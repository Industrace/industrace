# Asset Detail - Nuovo Layout

## Come Testare

È stata creata una versione alternativa del layout della pagina Asset Detail con un design più accessibile.

### Accesso

Per testare il nuovo layout, accedi a:
```
/assets-new/:id
```

Dove `:id` è l'ID dell'asset che vuoi visualizzare.

Esempio:
- Vecchio layout: `/assets/8bd77b01-783e-4b70-aa5e-f47d0bbd0329`
- Nuovo layout: `/assets-new/8bd77b01-783e-4b70-aa5e-f47d0bbd0329`

### Caratteristiche del Nuovo Layout

1. **Sidebar Navigation**: Navigazione sempre visibile con link diretti alle sezioni
2. **Sezioni Collassabili**: Le sezioni secondarie possono essere espanse/collassate
3. **Overview e Rischio Sempre Visibili**: Le informazioni principali sono sempre accessibili
4. **Accessibilità Migliorata**:
   - Skip link per saltare al contenuto principale
   - Navigazione da tastiera completa
   - ARIA labels appropriati
   - Screen reader friendly

### Struttura Sezioni

- **Panoramica** (sempre visibile): Info principali + Info tecniche
- **Rischio** (sempre visibile): Rischio totale + breakdown
- **Rete e Connessioni** (collassabile): Connessioni + Comunicazioni
- **Relazioni** (collassabile): Dipendenze + Vulnerabilità
- **Documentazione** (collassabile): Documenti + Note + Campi Personalizzati
- **Gestione** (collassabile): Contatti + Fornitori + Review
- **Cronologia** (collassabile): Timeline

### Componenti Creati

- `AssetDetailSidebar.vue`: Sidebar navigation
- `AssetDetailSection.vue`: Wrapper per sezioni collassabili
- `AssetDetailNew.vue`: Pagina principale con nuovo layout

### Note

Il vecchio layout (`AssetDetail.vue`) rimane invariato e funzionante. Il nuovo layout è disponibile solo tramite la route `/assets-new/:id`.

