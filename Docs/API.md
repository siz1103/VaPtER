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
- `search`: Ricerca full-text
- `name`: Filtro per nome
- `company_name`: Filtro per azienda
- `email`: Filtro per email
- `ordering`: Ordinamento (es: `-created_at`)

**Risposta:**
```json
{
  "count": 1,
  "results": [
    {
      "id": "uuid-string",
      "name": "Test Company",
      "company_name": "Test Corp",
      "email": "test@testcorp.com",
      "phone": "+1234567890",
      "contact_person": "John Doe",
      "address": "123 Test St",
      "notes": "Important client",
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

#### GET /api/orchestrator/customers/{id}/
Ottenere dettagli di un cliente specifico.

#### PATCH /api/orchestrator/customers/{id}/
Aggiornare un cliente esistente.

#### DELETE /api/orchestrator/customers/{id}/
Eliminare un cliente (soft delete).

#### GET /api/orchestrator/customers/{id}/targets/
Ottenere tutti i target di un cliente.

#### GET /api/orchestrator/customers/{id}/scans/
Ottenere tutte le scansioni di un cliente.

### 2. Port Lists

#### GET /api/orchestrator/port-lists/
Ottenere lista delle configurazioni porte.

**Risposta:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "name": "Web Ports",
      "tcp_ports": "80,443,8080,8443",
      "udp_ports": "53,161",
      "description": "Common web and DNS ports",
      "total_tcp_ports": 4,
      "total_udp_ports": 2,
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### POST /api/orchestrator/port-lists/
Creare una nuova lista di porte.

#### GET /api/orchestrator/port-lists/{id}/
Ottenere dettagli di una lista porte.

#### PATCH /api/orchestrator/port-lists/{id}/
Aggiornare una lista porte.

#### DELETE /api/orchestrator/port-lists/{id}/
Eliminare una lista porte.

### 3. Scan Types

#### GET /api/orchestrator/scan-types/
Ottenere lista dei tipi di scansione.

**Parametri Query:**
- `with_finger`: Solo scan types con fingerprinting
- `with_enum`: Solo scan types con enumeration  
- `with_web`: Solo scan types con web scanning
- `with_vuln`: Solo scan types con vulnerability lookup

**Risposta:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "name": "Full Scan",
      "only_discovery": false,
      "consider_alive": true,
      "be_quiet": false,
      "port_list": 1,
      "port_list_name": "Web Ports",
      "plugin_finger": true,
      "plugin_enum": true,
      "plugin_web": true,
      "plugin_vuln_lookup": true,
      "description": "Complete vulnerability assessment",
      "enabled_plugins": ["finger", "enum", "web", "vuln_lookup"],
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### POST /api/orchestrator/scan-types/
Creare un nuovo tipo di scansione.

#### GET /api/orchestrator/scan-types/{id}/
Ottenere dettagli di un tipo di scansione.

#### PATCH /api/orchestrator/scan-types/{id}/
Aggiornare un tipo di scansione.

#### DELETE /api/orchestrator/scan-types/{id}/
Eliminare un tipo di scansione.

### 4. Targets

#### GET /api/orchestrator/targets/
Ottenere lista dei target.

**Parametri Query:**
- `customer`: Filtro per customer ID
- `customer_name`: Filtro per nome customer
- `search`: Ricerca in nome, indirizzo, descrizione
- `has_recent_scans`: Target con scansioni recenti

**Risposta:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "customer": "customer-uuid",
      "customer_name": "Test Company",
      "name": "Web Server",
      "address": "192.168.1.100",
      "description": "Main web server",
      "scans_count": 3,
      "last_scan": {
        "id": 5,
        "status": "Completed",
        "initiated_at": "2025-01-01T10:00:00Z",
        "completed_at": "2025-01-01T10:30:00Z"
      },
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### POST /api/orchestrator/targets/
Creare un nuovo target.

#### GET /api/orchestrator/targets/{id}/
Ottenere dettagli di un target.

#### PATCH /api/orchestrator/targets/{id}/
Aggiornare un target.

#### DELETE /api/orchestrator/targets/{id}/
Eliminare un target.

#### GET /api/orchestrator/targets/{id}/scans/
Ottenere tutte le scansioni per un target.

#### POST /api/orchestrator/targets/{id}/scan/
Avviare una nuova scansione per un target.

**Body:**
```json
{
  "scan_type_id": 1
}
```

### 5. Scans ✅ AGGIORNATO

#### GET /api/orchestrator/scans/
Ottenere lista delle scansioni.

**Parametri Query:**
- `target__customer`: Filtro per customer ID (utilizzato dal frontend)
- `status`: Filtro per status scansione
- `target`: Filtro per target ID
- `scan_type`: Filtro per tipo scansione
- `search`: Ricerca in target name, address, customer name
- `initiated_after`: Scansioni dopo una data
- `initiated_before`: Scansioni prima di una data

**Risposta:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "target": 1,
      "target_name": "Web Server",
      "target_address": "192.168.1.100",
      "customer_name": "Test Company",
      "scan_type": 1,
      "scan_type_name": "Full Scan",
      "status": "Completed",
      "initiated_at": "2025-01-01T10:00:00Z",
      "started_at": "2025-01-01T10:05:00Z",
      "completed_at": "2025-01-01T10:30:00Z",
      "duration_seconds": 1500,
      "parsed_nmap_results": {
        "ports": [
          {
            "port": 80,
            "state": "open",
            "service": "http"
          },
          {
            "port": 443,
            "state": "open", 
            "service": "https"
          }
        ],
        "os_detection": "Linux 3.2 - 4.9"
      },
      "parsed_finger_results": null,
      "parsed_enum_results": null,
      "parsed_web_results": null,
      "parsed_vuln_results": null,
      "error_message": null,
      "report_path": "/reports/scan_1_report.pdf",
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-01T10:30:00Z"
    }
  ]
}
```

#### POST /api/orchestrator/scans/
Creare una nuova scansione (generalmente si usa l'endpoint target/scan).

#### GET /api/orchestrator/scans/{id}/
Ottenere dettagli di una scansione specifica.

#### PATCH /api/orchestrator/scans/{id}/
Aggiornare una scansione (usato per change scan type).

**Body per cambio scan type:**
```json
{
  "scan_type": 2
}
```

#### DELETE /api/orchestrator/scans/{id}/ ✅ NUOVO
Eliminare una scansione (solo se non attiva).

#### POST /api/orchestrator/scans/{id}/restart/ ✅ AGGIORNATO
Riavviare una scansione fallita o completata.

**Risposta:**
```json
{
  "id": 1,
  "status": "Pending",
  "initiated_at": "2025-01-01T11:00:00Z",
  "started_at": null,
  "completed_at": null,
  "error_message": null
}
```

#### POST /api/orchestrator/scans/{id}/cancel/ ✅ AGGIORNATO
Cancellare una scansione in corso.

**Risposta:**
```json
{
  "id": 1,
  "status": "Failed",
  "error_message": "Scan cancelled by user",
  "completed_at": "2025-01-01T10:15:00Z"
}
```

#### GET /api/orchestrator/scans/statistics/
Ottenere statistiche generali delle scansioni.

**Risposta:**
```json
{
  "total_scans": 150,
  "active_scans": 3,
  "completed_scans": 120,
  "failed_scans": 27,
  "scans_by_status": {
    "Pending": 1,
    "Queued": 1,
    "Nmap Scan Running": 1,
    "Completed": 120,
    "Failed": 27
  },
  "scans_last_24h": 12,
  "average_scan_duration_minutes": 25.5
}
```

### 6. Scan Details

#### GET /api/orchestrator/scan-details/
Ottenere dettagli aggiuntivi delle scansioni.

**Parametri Query:**
- `scan_id`: ID della scansione

**Risposta:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "scan": 1,
      "open_ports": {
        "tcp": [80, 443, 22],
        "udp": [53, 161]
      },
      "os_guess": {
        "name": "Linux 3.2 - 4.9",
        "accuracy": "95%"
      },
      "nmap_started_at": "2025-01-01T10:05:00Z",
      "nmap_completed_at": "2025-01-01T10:15:00Z",
      "finger_started_at": "2025-01-01T10:15:00Z",
      "finger_completed_at": "2025-01-01T10:20:00Z",
      "enum_started_at": "2025-01-01T10:20:00Z",
      "enum_completed_at": "2025-01-01T10:25:00Z",
      "web_started_at": "2025-01-01T10:25:00Z",
      "web_completed_at": "2025-01-01T10:28:00Z",
      "vuln_started_at": "2025-01-01T10:28:00Z",
      "vuln_completed_at": "2025-01-01T10:30:00Z",
      "created_at": "2025-01-01T10:05:00Z",
      "updated_at": "2025-01-01T10:30:00Z"
    }
  ]
}
```

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

## Scan Status Workflow ✅ AGGIORNATO

Le scansioni seguono questo workflow di stati:

```
Pending → Queued → Nmap Scan Running → Nmap Scan Completed
                                    ↓
                             Finger Scan Running → Finger Scan Completed
                                    ↓
                             Enum Scan Running → Enum Scan Completed
                                    ↓
                             Web Scan Running → Web Scan Completed
                                    ↓
                             Vuln Lookup Running → Vuln Lookup Completed
                                    ↓
                             Report Generation Running → Completed
```

Stati di errore:
- **Failed**: La scansione è fallita in qualsiasi fase
- Ogni fase può andare direttamente a **Failed** in caso di errore

### Stati Attivi (Con Polling)
I seguenti stati sono considerati "attivi" e vengono monitorati dal frontend con polling:
- `Pending`
- `Queued`
- `Nmap Scan Running`
- `Finger Scan Running`
- `Enum Scan Running`
- `Web Scan Running`
- `Vuln Lookup Running`
- `Report Generation Running`

### Azioni Disponibili per Status
- **Restart**: Disponibile per scansioni `Failed` o `Completed`
- **Cancel**: Disponibile per tutti gli stati attivi
- **Delete**: Disponibile solo per scansioni non attive
- **Change Scan Type**: Disponibile solo per scansioni non attive

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
  -d '{"scan_type_id": 1}'

# 7. Ottenere scansioni per customer ✅ NUOVO
curl "http://vapter.szini.it:8080/api/orchestrator/scans/?target__customer=customer-uuid"

# 8. Riavviare una scansione ✅ NUOVO
curl -X POST http://vapter.szini.it:8080/api/orchestrator/scans/1/restart/

# 9. Cancellare una scansione ✅ NUOVO
curl -X POST http://vapter.szini.it:8080/api/orchestrator/scans/1/cancel/

# 10. Cambiare tipo di scansione ✅ NUOVO
curl -X PATCH http://vapter.szini.it:8080/api/orchestrator/scans/1/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type": 2}'

# 11. Eliminare una scansione ✅ NUOVO
curl -X DELETE http://vapter.szini.it:8080/api/orchestrator/scans/1/

# 12. Ottenere statistiche scansioni
curl http://vapter.szini.it:8080/api/orchestrator/scans/statistics/
```

### Frontend Integration ✅ AGGIORNATO

Il frontend utilizza le seguenti API per la pagina Scans:

```typescript
// Ottenere scansioni per customer selezionato
GET /api/orchestrator/scans/?target__customer={customerId}

// Polling ogni 3 secondi per scansioni attive
// Gestito automaticamente da TanStack Query

// Azioni disponibili:
POST /api/orchestrator/scans/{id}/restart/
POST /api/orchestrator/scans/{id}/cancel/  
DELETE /api/orchestrator/scans/{id}/
PATCH /api/orchestrator/scans/{id}/ (per change scan type)
```

## Rate Limiting e Performance

### Polling Considerations
- Il frontend effettua polling ogni 3 secondi solo per scansioni attive
- Il polling si ferma automaticamente quando non ci sono scansioni attive
- Implementazione intelligente per ridurre carico server

### Caching Strategy
- TanStack Query gestisce il caching automatico
- Invalidazione cache dopo mutazioni (restart, cancel, delete)
- Stale time configurato per bilanciare freschezza e performance

### Error Handling
- Retry automatico per errori temporanei di rete
- Fallback graceful per timeout
- User feedback mediante toast notifications