# Test Evidence API

## Prerequisiti

1. Backend in esecuzione: `docker-compose -f docker-compose.dev.yml up backend`
2. Database migrato: `docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head`
3. Utente admin creato (default: admin@example.com / admin123)

## Test Manuali con cURL

### 1. Login e ottenere token

```bash
TOKEN=$(curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123" \
  | jq -r '.access_token')

echo "Token: $TOKEN"
```

### 2. Creare Evidence (libera, senza relazioni)

```bash
curl -X POST http://localhost:8000/api/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "manual",
    "type": "document",
    "description": "Firewall configuration screenshot",
    "confidence": 0.8
  }' | jq
```

**Risposta attesa**: 201 Created con Evidence object

### 3. Listare tutte le Evidence

```bash
curl -X GET http://localhost:8000/api/evidence \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Risposta attesa**: Array di Evidence objects

### 4. Filtrare Evidence per source

```bash
curl -X GET "http://localhost:8000/api/evidence?source=manual" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Risposta attesa**: Array di Evidence con source=manual

### 5. Filtrare Evidence per zone_id

```bash
# Prima ottenere un zone_id
ZONE_ID=$(curl -X GET http://localhost:8000/api/security-zones \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')

# Poi filtrare
curl -X GET "http://localhost:8000/api/evidence?zone_id=$ZONE_ID" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 6. Ottenere Evidence per ID

```bash
EVIDENCE_ID=$(curl -X GET http://localhost:8000/api/evidence \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')

curl -X GET "http://localhost:8000/api/evidence/$EVIDENCE_ID" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Risposta attesa**: 200 OK con Evidence object

### 7. Aggiornare Evidence

```bash
curl -X PUT "http://localhost:8000/api/evidence/$EVIDENCE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated: Firewall configuration screenshot",
    "confidence": 0.9
  }' | jq
```

**Risposta attesa**: 200 OK con Evidence aggiornato

### 8. Creare Evidence con relazione (zone_id)

```bash
curl -X POST http://localhost:8000/api/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"source\": \"document\",
    \"description\": \"Zone boundary protection evidence\",
    \"zone_id\": \"$ZONE_ID\"
  }" | jq
```

**Risposta attesa**: 201 Created con Evidence collegata a zone

### 9. Test Validazione (source invalido)

```bash
curl -X POST http://localhost:8000/api/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "invalid_source",
    "description": "This should fail"
  }' | jq
```

**Risposta attesa**: 422 Unprocessable Entity (validazione fallita)

### 10. Test Validazione (confidence > 1)

```bash
curl -X POST http://localhost:8000/api/evidence \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "manual",
    "description": "Test",
    "confidence": 1.5
  }' | jq
```

**Risposta attesa**: 422 Unprocessable Entity (confidence deve essere 0-1)

### 11. Eliminare Evidence

```bash
curl -X DELETE "http://localhost:8000/api/evidence/$EVIDENCE_ID" \
  -H "Authorization: Bearer $TOKEN" -v
```

**Risposta attesa**: 204 No Content

### 12. Verificare eliminazione (404)

```bash
curl -X GET "http://localhost:8000/api/evidence/$EVIDENCE_ID" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Risposta attesa**: 404 Not Found

## Test con Python Script

Eseguire lo script di test:

```bash
docker-compose -f docker-compose.dev.yml exec backend python test_evidence_api.py
```

## Test con Swagger UI

1. Aprire http://localhost:8000/docs
2. Cliccare "Authorize" e inserire credenziali
3. Cercare sezione "evidence"
4. Testare gli endpoint direttamente dall'interfaccia

## Checklist Test

- [ ] Login funziona
- [ ] CREATE Evidence (libera) funziona
- [ ] CREATE Evidence (con zone_id) funziona
- [ ] LIST Evidence funziona
- [ ] LIST Evidence con filtri funziona
- [ ] GET Evidence by ID funziona
- [ ] UPDATE Evidence funziona
- [ ] DELETE Evidence funziona
- [ ] Validazione source enum funziona
- [ ] Validazione confidence range funziona
- [ ] Multi-tenancy: Evidence isolata per tenant
- [ ] Relazioni opzionali funzionano (asset_id, zone_id, etc.)

## Note

- Tutte le relazioni sono opzionali (nullable)
- Evidence può essere creata "libera" senza relazioni
- Le relazioni possono essere aggiunte/modificate dopo la creazione
- Evidence NON calcola automaticamente compliance o SL

