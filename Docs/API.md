# VaPtER API Documentation

Questo documento descrive le API REST implementate nella piattaforma VaPtER.

## Architettura API

La piattaforma utilizza un **API Gateway Pattern** con FastAPI come gateway principale che fa da reverse proxy verso il backend Django.

```
Frontend → API Gateway (FastAPI) → Backend Orchestrator (Django)
```

## Base URL

### Produzione (Accesso Principale)
- **API Gateway**: `http://vapter.szini.it:8080/api/orchestrator/`
- **Documentazione API**: `http://vapter.szini.it:8080/docs`

### Development (Accesso Diretto)
- **Backend Django**: `http://vapter.szini.it:8000/api/orchestrator/`
- **Django Admin**: `http://vapter.szini.it:8000/admin/`
- **API Schema Django**: `http://vapter.szini.it:8000/api/schema/swagger-ui/`

### Monitoring & Health
- **Gateway Health**: `http://vapter.szini.it:8080/health/`
- **Gateway Detailed Health**: `http://vapter.szini.it:8080/health/detailed`
- **RabbitMQ Management**: `http://vapter.szini.it:15672/`

## Autenticazione

Al momento non è implementata l'autenticazione. Tutte le API sono accessibili senza autenticazione.
L'API Gateway è predisposto per l'implementazione futura di autenticazione JWT.

## Formato Risposta

Tutte le API restituiscono JSON con il seguente formato standard:

### Successo (200, 201, ecc.)
```json
{
  "data": "...",
  "status": "success"
}
```

### Errore (400, 404, 500, ecc.)
```json
{
  "error": "Error message",
  "status": "error"
}
```

### Paginazione
```json
{
  "count": 100,
  "next": "http://example.com/api/endpoint/?page=3",
  "previous": "http://example.com/api/endpoint/?page=1",
  "results": [...]
}
```

## API Gateway Endpoints

### Health Check Endpoints

#### GET /health/
Health check base dell'API Gateway.

**Risposta:**
```json
{
  "status": "healthy",
  "service": "api_gateway",
  "version": "1.0.0",
  "timestamp": 1641024000.123
}
```

#### GET /health/detailed
Health check dettagliato con verifica backend.

**Risposta:**
```json
{
  "status": "healthy",
  "service": "api_gateway",
  "version": "1.0.0",
  "timestamp": 1641024000.123,
  "checks": {
    "backend": {
      "status": "healthy",
      "url": "http://backend:8000",
      "response_time_ms": 45.67
    }
  }
}
```

#### GET /health/readiness
Kubernetes readiness probe endpoint.

#### GET /health/liveness
Kubernetes liveness probe endpoint.

## Orchestrator API Endpoints

Tutti gli endpoint dell'orchestrator sono accessibili tramite l'API Gateway con il prefisso `/api/orchestrator/`.

### 1. Customers

#### GET /api/orchestrator/customers/
Ottenere lista di tutti i clienti.

**Parametri Query:**
- `search`: Ricerca per nome, company_name, email, contact_person
- `name`: Filtra per nome (contiene)
- `email`: Filtra per email (contiene)
- `created_after`: Filtra per data creazione (YYYY-MM-DD)
- `page`: Numero di pagina
- `page_size`: Elementi per pagina (default: 20)

**Risposta:**
```json
{
  "count": 1,
  "results": [
    {
      "id": "uuid",
      "name": "Customer Name",
      "company_name": "Company Inc.",
      "email": "customer@example.com",
      "phone": "+1234567890",
      "contact_person": "John Doe",
      "address": "123 Main St",
      "notes": "Note aggiuntive",
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-01T10:00:00Z",
      "targets_count": 5,
      "scans_count": 12
    }
  ]
}
```

#### POST /api/orchestrator/customers/
Creare un nuovo cliente.

**Body:**
```json
{
  "name": "Customer Name",
  "company_name": "Company Inc.",
  "email": "customer@example.com",
  "phone": "+1234567890",
  "contact_person": "John Doe",
  "address": "123 Main St",
  "notes": "Note aggiuntive"
}
```

#### GET /api/orchestrator/customers/{id}/
Ottenere dettagli di un cliente specifico.

#### PUT/PATCH /api/orchestrator/customers/{id}/
Aggiornare un cliente.

#### DELETE /api/orchestrator/customers/{id}/
Eliminare un cliente (soft delete).

#### GET /api/orchestrator/customers/{id}/targets/
Ottenere tutti i target di un cliente.

#### GET /api/orchestrator/customers/{id}/scans/
Ottenere tutte le scansioni di un cliente.

#### GET /api/orchestrator/customers/{id}/statistics/
Ottenere statistiche del cliente.

**Risposta:**
```json
{
  "targets_count": 5,
  "scans_count": 12,
  "status_distribution": {
    "Completed": 8,
    "Failed": 2,
    "Running": 2
  },
  "recent_scans": [...]
}
```

### 2. Port Lists

#### GET /api/orchestrator/port-lists/
Ottenere lista delle configurazioni di porte.

**Parametri Query:**
- `search`: Ricerca per nome, descrizione, tcp_ports, udp_ports
- `name`: Filtra per nome (contiene)
- `page`: Numero di pagina
- `page_size`: Elementi per pagina (default: 20)

**Risposta:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "name": "Common TCP Ports",
      "tcp_ports": "21,22,23,25,53,80,443",
      "udp_ports": null,
      "description": "Porte TCP più comuni",
      "total_tcp_ports": 7,
      "total_udp_ports": 0,
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### POST /api/orchestrator/port-lists/
Creare una nuova lista di porte.

**Body:**
```json
{
  "name": "Custom Port List",
  "tcp_ports": "80,443,8080,8443",
  "udp_ports": "53,123,161",
  "description": "Lista personalizzata"
}
```

**Validazione:**
- `name`: Obbligatorio, max 50 caratteri
- `tcp_ports`: Opzionale, formato: "22,80,443" o "1-1000" o combinazioni
- `udp_ports`: Opzionale, stesso formato di tcp_ports
- Almeno uno tra `tcp_ports` e `udp_ports` deve essere specificato
- Le porte devono essere nel range 1-65535

#### GET /api/orchestrator/port-lists/{id}/
Ottenere dettagli di una lista di porte specifica.

#### PUT/PATCH /api/orchestrator/port-lists/{id}/
Aggiornare una lista di porte.

#### DELETE /api/orchestrator/port-lists/{id}/
Eliminare una lista di porte (soft delete).

**Note:** La cancellazione fallirà se la lista è utilizzata da scan types esistenti.

### 3. Scan Types

#### GET /api/orchestrator/scan-types/
Ottenere lista dei tipi di scansione.

**Parametri Query:**
- `search`: Ricerca per nome, descrizione, configurazione
- `with_finger`: Filtra per scan types con fingerprinting
- `with_enum`: Filtra per scan types con enumerazione
- `with_web`: Filtra per scan types con web scanning
- `with_vuln`: Filtra per scan types con vulnerability lookup
- `page`: Numero di pagina
- `page_size`: Elementi per pagina (default: 20)

**Risposta:**
```json
{
  "count": 6,
  "results": [
    {
      "id": 1,
      "name": "Discovery",
      "only_discovery": true,
      "consider_alive": false,
      "be_quiet": true,
      "port_list": null,
      "port_list_name": null,
      "plugin_finger": false,
      "plugin_enum": false,
      "plugin_web": false,
      "plugin_vuln_lookup": false,
      "description": "Scansione di discovery",
      "enabled_plugins": [],
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### POST /api/orchestrator/scan-types/
Creare un nuovo tipo di scansione.

**Body:**
```json
{
  "name": "Custom Scan Type",
  "only_discovery": false,
  "consider_alive": false,
  "be_quiet": false,
  "port_list": 2,
  "plugin_finger": true,
  "plugin_enum": false,
  "plugin_web": false,
  "plugin_vuln_lookup": true,
  "description": "Tipo di scansione personalizzato"
}
```

**Validazione:**
- `name`: Obbligatorio, max 50 caratteri, univoco
- Se `only_discovery` è true, `port_list` deve essere null e tutti i plugin devono essere false
- `port_list`: Deve esistere se specificato

#### GET /api/orchestrator/scan-types/{id}/
Ottenere dettagli di un tipo di scansione specifico.

#### PUT/PATCH /api/orchestrator/scan-types/{id}/
Aggiornare un tipo di scansione.

#### DELETE /api/orchestrator/scan-types/{id}/
Eliminare un tipo di scansione (soft delete).

**Note:** La cancellazione fallirà se il tipo è utilizzato da scansioni esistenti.

### 4. Targets

#### GET /api/orchestrator/targets/
Ottenere lista dei target.

**Parametri Query:**
- `customer`: ID del cliente
- `customer_name`: Nome del cliente (contiene)
- `name`: Nome target (contiene)
- `address`: Indirizzo target (contiene)
- `has_recent_scans`: true/false

**Risposta:**
```json
{
  "results": [
    {
      "id": 1,
      "customer": "uuid",
      "customer_name": "Customer Name",
      "name": "Web Server",
      "address": "192.168.1.100",
      "description": "Server web principale",
      "scans_count": 3,
      "last_scan": {
        "id": 5,
        "status": "Completed",
        "initiated_at": "2025-01-01T10:00:00Z",
        "completed_at": "2025-01-01T10:30:00Z"
      },
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### POST /api/orchestrator/targets/
Creare un nuovo target.

**Body:**
```json
{
  "customer": "customer-uuid",
  "name": "Web Server",
  "address": "192.168.1.100",
  "description": "Server web principale"
}
```

#### POST /api/orchestrator/targets/{id}/scan/
Avviare una nuova scansione per un target.

**Body:**
```json
{
  "scan_type_id": 2
}
```

### 5. Scans

#### GET /api/orchestrator/scans/
Ottenere lista delle scansioni.

**Parametri Query:**
- `target`: ID del target
- `customer`: ID del cliente
- `status`: Stato della scansione
- `status_in`: Lista di stati (es: "Completed,Failed")
- `is_running`: true/false
- `is_completed`: true/false
- `has_errors`: true/false
- `initiated_after`: Data inizio (YYYY-MM-DD)
- `initiated_before`: Data fine (YYYY-MM-DD)

**Risposta:**
```json
{
  "results": [
    {
      "id": 1,
      "target": 1,
      "target_name": "Web Server",
      "target_address": "192.168.1.100",
      "customer_name": "Customer Name",
      "scan_type": 2,
      "scan_type_name": "Scan Base",
      "status": "Completed",
      "initiated_at": "2025-01-01T10:00:00Z",
      "started_at": "2025-01-01T10:01:00Z",
      "completed_at": "2025-01-01T10:30:00Z",
      "duration_seconds": 1740,
      "parsed_nmap_results": {...},
      "error_message": null,
      "report_path": null,
      "details": {
        "open_ports": [...],
        "os_guess": {...}
      }
    }
  ]
}
```

#### POST /api/orchestrator/scans/
Creare e avviare una nuova scansione.

**Body:**
```json
{
  "target": 1,
  "scan_type": 2
}
```

#### GET /api/orchestrator/scans/{id}/
Ottenere dettagli di una scansione.

#### PATCH /api/orchestrator/scans/{id}/
Aggiornare una scansione (usato principalmente dai moduli scanner).

**Body:**
```json
{
  "status": "Completed",
  "parsed_nmap_results": {...},
  "completed_at": "2025-01-01T10:30:00Z"
}
```

#### POST /api/orchestrator/scans/{id}/restart/
Riavviare una scansione fallita o completata.

#### POST /api/orchestrator/scans/{id}/cancel/
Cancellare una scansione in corso.

#### GET /api/orchestrator/scans/statistics/
Ottenere statistiche generali delle scansioni.

### 6. Scan Details

#### GET /api/orchestrator/scan-details/
Ottenere dettagli aggiuntivi delle scansioni.

**Parametri Query:**
- `scan_id`: ID della scansione

## Status Codes

- **200**: OK - Richiesta completata con successo
- **201**: Created - Risorsa creata con successo
- **400**: Bad Request - Errore nei dati inviati
- **404**: Not Found - Risorsa non trovata
- **502**: Bad Gateway - Errore di comunicazione con backend
- **503**: Service Unavailable - Backend non disponibile
- **504**: Gateway Timeout - Timeout comunicazione backend
- **500**: Internal Server Error - Errore interno del server

## API Gateway Features

### Request Logging
Tutte le richieste vengono loggiate con:
- Request ID univoco
- Metodo HTTP e URL
- IP client e User-Agent
- Durata della richiesta
- Status code di risposta

### Error Handling
- Timeout configurabile per richieste backend
- Retry logic automatico per errori temporanei
- Propagazione appropriata degli errori
- Logging dettagliato degli errori

### Headers Personalizzati
- `X-Request-ID`: ID univoco della richiesta
- `X-Process-Time`: Tempo di elaborazione in secondi

## Filtri e Ricerca

Tutte le API supportano:
- **Ricerca**: Parametro `search` per ricerca full-text
- **Filtri**: Parametri specifici per ogni campo
- **Ordinamento**: Parametro `ordering` (es: `-created_at`)
- **Paginazione**: Parametri `page` e `page_size`

## Esempi di Utilizzo

### Tramite API Gateway (Raccomandato)

```bash
# 1. Verificare stato del gateway
curl http://vapter.szini.it:8080/health/detailed

# 2. Creare un cliente
curl -X POST http://vapter.szini.it:8080/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Corp", "email": "test@testcorp.com"}'

# 3. Creare una lista di porte
curl -X POST http://vapter.szini.it:8080/api/orchestrator/port-lists/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Web Ports", "tcp_ports": "80,443,8080,8443", "description": "Common web ports"}'

# 4. Creare un tipo di scansione
curl -X POST http://vapter.szini.it:8080/api/orchestrator/scan-types/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Web Scan", "port_list": 1, "plugin_web": true, "description": "Web application scan"}'

# 5. Creare un target
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{"customer": "customer-uuid", "name": "Web Server", "address": "192.168.1.100"}'

# 6. Avviare una scansione
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/1/scan/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type_id": 2}'

# 7. Monitorare la scansione
curl http://vapter.szini.it:8080/api/orchestrator/scans/1/

# 8. Filtrare port lists
curl "http://vapter.szini.it:8080/api/orchestrator/port-lists/?search=web"

# 9. Filtrare scan types con plugin web
curl "http://vapter.szini.it:8080/api/orchestrator/scan-types/?with_web=true"
```

### Accesso Diretto Backend (Solo Development)

```bash
# Accesso diretto al backend Django (bypass gateway)
curl http://vapter.szini.it:8000/api/orchestrator/customers/
```

## Nuove Funzionalità Settings

### Port Lists
- CRUD completo per gestione liste di porte
- Validazione formato porte (singole, range, combinazioni)
- Conteggio automatico numero porte
- Controllo dipendenze con Scan Types

### Scan Types
- CRUD completo per gestione tipi di scansione
- Logica `only_discovery` che disabilita configurazioni avanzate
- Gestione plugin opzionali
- Integrazione con Port Lists
- Configurazioni per timing e comportamento scan

## Workflow Tipico

1. **Setup iniziale**: Creare cliente e configurazioni
2. **Configurazione Port Lists**: Definire gruppi di porte standard
3. **Configurazione Scan Types**: Creare template di scansione
4. **Gestione Target**: Aggiungere target da scansionare
5. **Esecuzione**: Avviare scansione tramite API Gateway
6. **Monitoraggio**: Controllare stato via polling
7. **Risultati**: Recuperare risultati e report generati

## Monitoring e Debugging

### Health Checks
- `/health/`: Base health check
- `/health/detailed`: Health con verifica backend
- `/health/readiness`: Per Kubernetes readiness probe
- `/health/liveness`: Per Kubernetes liveness probe

### Logs
- I log dell'API Gateway contengono tutte le richieste con timing e dettagli
- Ogni richiesta ha un ID univoco per tracciamento
- Errori di comunicazione backend sono loggati separatamente

### Troubleshooting
1. Verificare stato gateway: `GET /health/detailed`
2. Controllare logs del container: `docker-compose logs api_gateway`
3. Verificare connettività backend: `GET /health/readiness`