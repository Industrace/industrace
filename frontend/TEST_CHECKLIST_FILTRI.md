# Checklist Test Filtri Assets

## Test Funzionalità Base

### 1. Filtri Base Sempre Visibili
- [ ] Verificare che i filtri Status, Site, Area siano sempre visibili
- [ ] Verificare che ogni dropdown funzioni correttamente
- [ ] Verificare che il pulsante "Filtri avanzati" sia visibile

### 2. Filtri Avanzati Espandibili
- [ ] Cliccare sul pulsante "Filtri avanzati"
- [ ] Verificare che la sezione si espanda mostrando:
  - [ ] Filtro Location
  - [ ] Filtro Business Criticality
  - [ ] Filtri Risk Score (min e max)
- [ ] Cliccare di nuovo per collassare la sezione
- [ ] Verificare che i filtri avanzati si nascondano correttamente

### 3. Applicazione Filtri
- [ ] Selezionare un filtro Status
- [ ] Verificare che gli asset vengano filtrati correttamente
- [ ] Verificare che il tag del filtro attivo appaia sopra la tabella
- [ ] Selezionare un filtro Site
- [ ] Verificare che i filtri si combinino correttamente (AND)
- [ ] Selezionare un filtro Area
- [ ] Verificare che tutti i filtri attivi siano mostrati come tag

### 4. Filtri Avanzati
- [ ] Espandere i filtri avanzati
- [ ] Selezionare una Business Criticality (es. "Critical")
- [ ] Verificare che gli asset vengano filtrati
- [ ] Impostare un Risk Score Min (es. 5)
- [ ] Verificare che solo gli asset con risk_score >= 5 siano mostrati
- [ ] Impostare un Risk Score Max (es. 8)
- [ ] Verificare che solo gli asset con risk_score tra 5 e 8 siano mostrati
- [ ] Selezionare una Location
- [ ] Verificare che il filtro funzioni correttamente

### 5. Rimozione Filtri
- [ ] Cliccare sulla X su un tag filtro attivo
- [ ] Verificare che il filtro venga rimosso
- [ ] Verificare che gli asset vengano aggiornati
- [ ] Cliccare su "Clear All"
- [ ] Verificare che tutti i filtri vengano rimossi
- [ ] Verificare che tutti gli asset vengano mostrati

## Test Sincronizzazione URL

### 6. Sincronizzazione Filtri → URL
- [ ] Applicare un filtro Status
- [ ] Verificare che l'URL contenga `?status_id=...`
- [ ] Applicare un filtro Site
- [ ] Verificare che l'URL contenga entrambi i parametri
- [ ] Applicare un filtro Business Criticality
- [ ] Verificare che l'URL contenga `?business_criticality=critical`
- [ ] Applicare un filtro Risk Score Min
- [ ] Verificare che l'URL contenga `?risk_score_min=5`
- [ ] Rimuovere tutti i filtri
- [ ] Verificare che l'URL non contenga più i parametri

### 7. Sincronizzazione URL → Filtri (Navigazione Dashboard)
- [ ] Navigare alla dashboard
- [ ] Cliccare su "Assets at Risk" (link con `?risk_score_min=5`)
- [ ] Verificare che la pagina Assets si apra con il filtro Risk Score Min già applicato
- [ ] Verificare che gli asset siano già filtrati
- [ ] Tornare alla dashboard
- [ ] Cliccare su "Critical Assets" (link con `?business_criticality=critical`)
- [ ] Verificare che la pagina Assets si apra con il filtro Business Criticality già applicato
- [ ] Verificare che gli asset siano già filtrati
- [ ] Tornare alla dashboard
- [ ] Cliccare su "Newly Added Assets" (link con `?sort=created_at&order=desc`)
- [ ] Verificare che la pagina Assets si apra con l'ordinamento già applicato

### 8. Condivisione URL
- [ ] Applicare alcuni filtri
- [ ] Copiare l'URL dalla barra degli indirizzi
- [ ] Aprire una nuova scheda del browser
- [ ] Incollare l'URL
- [ ] Verificare che i filtri siano già applicati
- [ ] Verificare che gli asset siano già filtrati

## Test Performance e Reattività

### 9. Debounce e Performance
- [ ] Cambiare rapidamente più filtri in sequenza
- [ ] Verificare che non vengano fatte troppe chiamate API
- [ ] Verificare che ci sia un leggero delay (debounce) prima della chiamata
- [ ] Verificare che dopo il debounce, la chiamata venga eseguita

### 10. Reattività
- [ ] Cambiare un filtro
- [ ] Verificare che gli asset vengano aggiornati automaticamente
- [ ] Verificare che non sia necessario cliccare un pulsante "Applica"
- [ ] Cambiare più filtri in sequenza
- [ ] Verificare che ogni cambio triggeri un aggiornamento

## Test Edge Cases

### 11. Filtri Vuoti
- [ ] Verificare che con nessun filtro applicato, tutti gli asset siano mostrati
- [ ] Verificare che il conteggio totale sia corretto
- [ ] Applicare un filtro che non corrisponde a nessun asset
- [ ] Verificare che venga mostrato "0 risultati" o messaggio appropriato

### 12. Combinazioni Complesse
- [ ] Applicare Status + Site + Area + Business Criticality + Risk Score
- [ ] Verificare che tutti i filtri funzionino insieme
- [ ] Verificare che l'URL contenga tutti i parametri
- [ ] Rimuovere un filtro alla volta
- [ ] Verificare che ogni rimozione aggiorni correttamente i risultati

### 13. Trash Mode
- [ ] Attivare la modalità Trash
- [ ] Verificare che i filtri funzionino anche in modalità Trash
- [ ] Applicare un filtro in modalità Trash
- [ ] Verificare che solo gli asset eliminati vengano filtrati

## Test UI/UX

### 14. Visualizzazione Filtri Attivi
- [ ] Applicare diversi filtri
- [ ] Verificare che tutti i tag dei filtri attivi siano visibili
- [ ] Verificare che i tag siano cliccabili per rimuovere il filtro
- [ ] Verificare che il conteggio dei filtri attivi sia corretto
- [ ] Verificare che il pulsante "Clear All" sia visibile quando ci sono filtri attivi

### 15. Responsive Design
- [ ] Testare su schermo grande (desktop)
- [ ] Verificare che i filtri siano disposti orizzontalmente
- [ ] Testare su schermo piccolo (mobile)
- [ ] Verificare che i filtri si adattino correttamente
- [ ] Verificare che la sezione avanzata sia leggibile su mobile

## Test Integrazione

### 16. Integrazione con BaseDataTable
- [ ] Verificare che la tabella mostri gli asset filtrati
- [ ] Verificare che il global search della tabella funzioni insieme ai filtri
- [ ] Verificare che l'ordinamento della tabella funzioni con i filtri applicati

### 17. Integrazione con altre pagine
- [ ] Dalla pagina Asset Detail, tornare alla lista Assets
- [ ] Verificare che i filtri precedenti siano mantenuti (se salvati in localStorage)
- [ ] Navigare da altre pagine alla lista Assets
- [ ] Verificare che i filtri vengano inizializzati correttamente

## Note
- Tutti i test devono essere eseguiti con dati reali nel database
- Verificare che non ci siano errori nella console del browser
- Verificare che non ci siano loop infiniti di chiamate API
- Verificare che l'URL non cambi continuamente senza intervento dell'utente
