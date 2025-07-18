# Docs/API.md

# Documentazione API Orchestrator

## Panoramica

L'API Orchestrator gestisce tutte le operazioni relative a clienti, target, scansioni e configurazioni. Tutte le API sono esposte tramite l'API Gateway sulla porta 8080.

**Base URL**: `http://vapter.szini.it:8080/api/orchestrator/`

## Autenticazione

**NOTA**: L'autenticazione non è ancora implementata nella fase di sviluppo corrente.

## Endpoints

### 1. Customers

#### GET /api/orchestrator/customers/
Ottenere la lista dei clienti con paginazione e filtri.

**Parametri Query:**
- `page`: Numero pagina (default: 1)
- `page_size`: Elementi per pagina (default: 10)
- `search`: Ricerca per nome, email, azienda
- `ordering`: Campo ordinamento (`name`, `-created_at`, etc.)

**Risposta:**
```json
{
  "count": 25,
  "next": "http://vapter.szini.it:8080/api/orchestrator/customers/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid-string",
      "name": "Customer Name",
      "company_name": "Company Inc",
      "email": "customer@example.com",
      "phone": "+1234567890",
      "contact_person": "John Doe",
      "address": "123 Main St",
      "notes": "Important customer",
      "targets_count": 5,
      "scans_count": 12,
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-01T10:00:00Z"
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
  "company_name": "Company Inc",
  "email": "customer@example.com",
  "phone": "+1234567890",
  "contact_person": "John Doe",
  "address": "123 Main St",
  "notes": "Important customer"
}
```

**Validazioni:**
- `name`: Obbligatorio, max 255 caratteri
- `email`: Obbligatorio, deve essere unico, formato email valido
- Altri campi sono opzionali

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
    "Nmap Scan Running": 2
  },
  "recent_scans": [...]
}
```

### 2. Port Lists

#### GET /api/orchestrator/port-lists/
Ottenere lista delle port list.

**Risposta:**
```json
{
  "results": [
    {
      "id": 1,
      "name": "Standard TCP Scan",
      "tcp_ports": "21,22,23,25,80,443,3306,3389,8080",
      "udp_ports": "53,123,161",
      "description": "Common ports for standard scanning",
      "total_tcp_ports": 9,
      "total_udp_ports": 3,
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### POST /api/orchestrator/port-lists/
Creare una nuova port list.

**Body:**
```json
{
  "name": "Custom Port List",
  "tcp_ports": "80,443,8080-8090",
  "udp_ports": "53,123",
  "description": "Custom ports for web services"
}
```

**Formato Porte:**
- Singole: `80,443,3306`
- Range: `8080-8090`
- Misto: `80,443,8080-8090,9000`

### 3. Scan Types

#### GET /api/orchestrator/scan-types/
Ottenere lista dei tipi di scansione.

**Risposta:**
```json
{
  "results": [
    {
      "id": 1,
      "name": "Basic Scan",
      "port_list": 1,
      "port_list_name": "Standard TCP Scan",
      "plugin_finger": false,
      "plugin_enum": false,
      "plugin_web": false,
      "plugin_vuln_lookup": false,
      "enabled_plugins": [],
      "description": "Basic port scanning only",
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### POST /api/orchestrator/scan-types/
Creare un nuovo tipo di scansione.

**Body:**
```json
{
  "name": "Full Scan",
  "port_list": 1,
  "plugin_finger": true,
  "plugin_enum": true,
  "plugin_web": true,
  "plugin_vuln_lookup": true,
  "description": "Complete scan with all plugins"
}
```

**Note sui Plugin:**
- I plugin sono previsti nell'architettura ma non ancora implementati
- Attualmente solo la scansione Nmap è funzionante
- I flag dei plugin possono essere impostati ma non avranno effetto

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

**Comportamento Scansioni Multiple:**
- È possibile avviare più scansioni sullo stesso target
- Non ci sono restrizioni sul numero di scansioni contemporanee
- Ogni scansione è indipendente e può utilizzare scan_type diversi
- Utile per:
  - Eseguire scansioni con diversi livelli di approfondimento
  - Monitorare cambiamenti nel tempo
  - Testare diverse configurazioni di scansione

**Risposta:**
```json
{
  "id": 10,
  "target": 1,
  "target_name": "Web Server",
  "target_address": "192.168.1.100",
  "scan_type": 2,
  "scan_type_name": "Full Scan",
  "status": "Queued",
  "initiated_at": "2025-01-18T10:00:00Z"
}
```

### 5. Scans

#### GET /api/orchestrator/scans/
Ottenere lista delle scansioni.

**Parametri Query:**
- `target`: ID del target
- `target__customer`: ID del cliente
- `status`: Stato della scansione
- `scan_type`: ID del tipo di scansione
- `initiated_after`: Data minima di avvio
- `initiated_before`: Data massima di avvio

**Stati Possibili:**
- `Pending`: Creata ma non in coda
- `Queued`: In coda per elaborazione
- `Nmap Scan Running`: Scansione porte in corso
- `Nmap Scan Completed`: Scansione porte completata
- `Completed`: Scansione completata
- `Failed`: Scansione fallita

**Note:** Gli stati relativi ai plugin (Finger, Enum, Web, Vuln) sono previsti ma non utilizzati attualmente.

#### POST /api/orchestrator/scans/
Creare una nuova scansione.

**Body:**
```json
{
  "target": 1,
  "scan_type": 2
}
```

#### GET /api/orchestrator/scans/{id}/
Ottenere dettagli di una scansione.

**Risposta Dettagliata:**
```json
{
  "id": 10,
  "target": 1,
  "target_name": "Web Server",
  "target_address": "192.168.1.100",
  "customer_name": "Customer Name",
  "scan_type": 2,
  "scan_type_name": "Full Scan",
  "status": "Completed",
  "initiated_at": "2025-01-18T10:00:00Z",
  "started_at": "2025-01-18T10:00:05Z",
  "completed_at": "2025-01-18T10:30:00Z",
  "duration_seconds": 1795,
  "parsed_nmap_results": {...},
  "error_message": null,
  "details": {
    "id": 1,
    "open_ports": [...],
    "os_guess": {...},
    "nmap_started_at": "2025-01-18T10:00:05Z",
    "nmap_completed_at": "2025-01-18T10:30:00Z"
  }
}
```

#### POST /api/orchestrator/scans/{id}/restart/
Riavviare una scansione fallita o completata.

**Prerequisiti:**
- La scansione deve essere in stato `Failed` o `Completed`
- Resetta tutti i risultati precedenti

#### POST /api/orchestrator/scans/{id}/cancel/
Annullare una scansione in corso.

**Note:** Non ancora implementato completamente.

#### GET /api/orchestrator/scans/statistics/
Ottenere statistiche globali delle scansioni.

### 6. Scan Details

#### GET /api/orchestrator/scan-details/
Ottenere lista dei dettagli di scansione.

#### GET /api/orchestrator/scan-details/{id}/
Ottenere dettagli specifici di una scansione.

## Gestione Errori

L'API utilizza codici di stato HTTP standard:

- `200 OK`: Richiesta completata con successo
- `201 Created`: Risorsa creata con successo
- `400 Bad Request`: Dati invalidi o mancanti
- `404 Not Found`: Risorsa non trovata
- `500 Internal Server Error`: Errore del server

**Formato Errori:**
```json
{
  "error": "Messaggio di errore principale",
  "details": {
    "field_name": ["Errore specifico del campo"]
  }
}
```

## Rate Limiting

Non implementato nella fase corrente.

## Webhook

Non implementati nella fase corrente.

## Note sullo Sviluppo

1. **Autenticazione**: Da implementare prima del deployment in produzione
2. **CORS**: Attualmente permissivo, da configurare per produzione
3. **Plugin**: Solo Nmap è funzionante, altri plugin sono placeholder
4. **Scansioni Multiple**: Supportate senza restrizioni per flessibilità in sviluppo