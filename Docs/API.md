# VaPtER API Documentation

Questo documento descrive le API REST implementate nel backend Django orchestrator.

## Base URL

- **Development**: `http://vapter.szini.it:8000/api/orchestrator/`
- **API Schema**: `http://vapter.szini.it:8000/api/schema/swagger-ui/`

## Autenticazione

Al momento non è implementata l'autenticazione. Tutte le API sono accessibili senza autenticazione.

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

## Endpoints

### 1. Customers

#### GET /customers/
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

#### POST /customers/
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

#### GET /customers/{id}/
Ottenere dettagli di un cliente specifico.

#### PUT/PATCH /customers/{id}/
Aggiornare un cliente.

#### DELETE /customers/{id}/
Eliminare un cliente (soft delete).

#### GET /customers/{id}/targets/
Ottenere tutti i target di un cliente.

#### GET /customers/{id}/scans/
Ottenere tutte le scansioni di un cliente.

#### GET /customers/{id}/statistics/
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

#### GET /port-lists/
Ottenere lista delle configurazioni di porte.

**Risposta:**
```json
{
  "results": [
    {
      "id": 1,
      "name": "Common TCP Ports",
      "tcp_ports": "21,22,23,25,53,80,443",
      "udp_ports": null,
      "description": "Porte TCP più comuni",
      "total_tcp_ports": 7,
      "total_udp_ports": 0,
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### POST /port-lists/
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

### 3. Scan Types

#### GET /scan-types/
Ottenere lista dei tipi di scansione.

**Parametri Query:**
- `with_finger`: Filtra per scan types con fingerprinting
- `with_enum`: Filtra per scan types con enumerazione
- `with_web`: Filtra per scan types con web scanning
- `with_vuln`: Filtra per scan types con vulnerability lookup

**Risposta:**
```json
{
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
      "enabled_plugins": []
    }
  ]
}
```

#### POST /scan-types/
Creare un nuovo tipo di scansione.

### 4. Targets

#### GET /targets/
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

#### POST /targets/
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

#### POST /targets/{id}/scan/
Avviare una nuova scansione per un target.

**Body:**
```json
{
  "scan_type_id": 2
}
```

### 5. Scans

#### GET /scans/
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

#### POST /scans/
Creare e avviare una nuova scansione.

**Body:**
```json
{
  "target": 1,
  "scan_type": 2
}
```

#### GET /scans/{id}/
Ottenere dettagli di una scansione.

#### PATCH /scans/{id}/
Aggiornare una scansione (usato principalmente dai moduli scanner).

**Body:**
```json
{
  "status": "Completed",
  "parsed_nmap_results": {...},
  "completed_at": "2025-01-01T10:30:00Z"
}
```

#### POST /scans/{id}/restart/
Riavviare una scansione fallita o completata.

#### POST /scans/{id}/cancel/
Cancellare una scansione in corso.

#### GET /scans/statistics/
Ottenere statistiche generali delle scansioni.

### 6. Scan Details

#### GET /scan-details/
Ottenere dettagli aggiuntivi delle scansioni.

**Parametri Query:**
- `scan_id`: ID della scansione

## Status Codes

- **200**: OK - Richiesta completata con successo
- **201**: Created - Risorsa creata con successo
- **400**: Bad Request - Errore nei dati inviati
- **404**: Not Found - Risorsa non trovata
- **500**: Internal Server Error - Errore interno del server

## Filtri e Ricerca

Tutte le API supportano:
- **Ricerca**: Parametro `search` per ricerca full-text
- **Filtri**: Parametri specifici per ogni campo
- **Ordinamento**: Parametro `ordering` (es: `-created_at`)
- **Paginazione**: Parametri `page` e `page_size`

## Esempi di Utilizzo

### Creare un cliente e avviare una scansione

```bash
# 1. Creare un cliente
curl -X POST http://vapter.szini.it:8000/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Corp", "email": "test@testcorp.com"}'

# 2. Creare un target
curl -X POST http://vapter.szini.it:8000/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{"customer": "customer-uuid", "name": "Web Server", "address": "192.168.1.100"}'

# 3. Avviare una scansione
curl -X POST http://vapter.szini.it:8000/api/orchestrator/targets/1/scan/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type_id": 2}'

# 4. Monitorare la scansione
curl http://vapter.szini.it:8000/api/orchestrator/scans/1/
```

## Workflow Tipico

1. **Setup iniziale**: Creare cliente e target
2. **Configurazione**: Scegliere tipo di scansione appropriato
3. **Esecuzione**: Avviare scansione tramite API
4. **Monitoraggio**: Controllare stato via polling o webhook (futuro)
5. **Risultati**: Recuperare risultati e report generati