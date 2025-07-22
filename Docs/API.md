# API Documentation - VaPtER

## Base URL
- **API Gateway**: `http://vapter.szini.it:8080/api/orchestrator/`
- **Backend Direct**: `http://vapter.szini.it:8000/api/orchestrator/` (solo development)

## Autenticazione
**NOTA**: L'autenticazione non è ancora implementata. Sarà aggiunta prima del deploy in produzione.

## Endpoints

### 5. Scans ✅ AGGIORNATO

#### PATCH /api/orchestrator/scans/{id}/ ✅ ENHANCED
Aggiornare una scansione esistente.

**Comportamento speciale per parsed_nmap_results**:
Quando viene aggiornato il campo `parsed_nmap_results`, il sistema automaticamente:
1. Estrae le porte aperte dai risultati nmap
2. Estrae l'OS detection più probabile
3. Salva questi dati nella tabella `ScanDetail` associata

**Body Esempio con risultati Nmap:**
```json
{
  "parsed_nmap_results": {
    "hosts": [{
      "os": {
        "name": "Linux 4.19 - 5.15",
        "accuracy": "98",
        "vendor": "Linux",
        "type": "general purpose",
        "osfamily": "Linux",
        "osgen": "4.X"
      },
      "ports": [
        {
          "state": "open",
          "portid": "22",
          "protocol": "tcp",
          "service": {
            "name": "ssh",
            "product": "OpenSSH",
            "version": "6.6.1p1"
          }
        }
      ],
      "state": "up"
    }]
  },
  "status": "Nmap Scan Completed"
}
```

**Dati automaticamente estratti in ScanDetail:**
- `open_ports`: Contiene liste separate per TCP e UDP con dettagli dei servizi
- `os_guess`: Contiene le informazioni dell'OS più probabile

### 6. Scan Details ✅ AGGIORNATO

#### GET /api/orchestrator/scan-details/
Ottenere dettagli aggiuntivi delle scansioni.

**Risposta con dati processati:**
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "scan": 1,
      "open_ports": {
        "tcp": [
          {
            "port": 22,
            "state": "open",
            "service": "ssh",
            "product": "OpenSSH",
            "version": "6.6.1p1",
            "extrainfo": "Ubuntu Linux; protocol 2.0"
          },
          {
            "port": 80,
            "state": "open",
            "service": "http",
            "product": "Apache httpd",
            "version": "2.4.7"
          }
        ],
        "udp": []
      },
      "os_guess": {
        "name": "Linux 4.19 - 5.15",
        "accuracy": "98",
        "vendor": "Linux",
        "type": "general purpose",
        "osfamily": "Linux",
        "osgen": "4.X"
      },
      "nmap_started_at": "2025-01-01T10:05:00Z",
      "nmap_completed_at": "2025-01-01T10:15:00Z",
      "created_at": "2025-01-01T10:05:00Z",
      "updated_at": "2025-01-01T10:30:00Z"
    }
  ]
}
```

GCE Results
List GCE Results
httpGET /api/orchestrator/gce-results/
Query parameters:

scan - Filter by scan ID
target - Filter by target ID
gce_scan_status - Filter by status (Done, Running, Stopped)
report_format - Filter by format (XML, JSON)

Response:
json{
  "count": 10,
  "results": [
    {
      "id": 1,
      "scan": 123,
      "target": 456,
      "gce_task_id": "550e8400-e29b-41d4-a716-446655440000",
      "gce_report_id": "660e8400-e29b-41d4-a716-446655440000",
      "gce_target_id": "770e8400-e29b-41d4-a716-446655440000",
      "gce_scan_status": "Done",
      "gce_scan_progress": 100,
      "report_format": "XML",
      "vulnerability_count": {
        "critical": 2,
        "high": 5,
        "medium": 10,
        "low": 15,
        "log": 20
      },
      "gce_scan_started_at": "2025-01-22T10:00:00Z",
      "gce_scan_completed_at": "2025-01-22T11:30:00Z",
      "created_at": "2025-01-22T10:00:00Z"
    }
  ]
}
Get GCE Result Detail
httpGET /api/orchestrator/gce-results/{id}/
Response includes the full report in full_report field.
Update GCE Scan Progress
httpPATCH /api/orchestrator/scans/{scan_id}/gce-progress/
Request body:
json{
  "gce_task_id": "550e8400-e29b-41d4-a716-446655440000",
  "gce_scan_progress": 45,
  "gce_scan_status": "Running"
}
Response:
json{
  "status": "progress updated"
}
Create GCE Results
httpPOST /api/orchestrator/scans/{scan_id}/gce-results/
Request body:
json{
  "gce_task_id": "550e8400-e29b-41d4-a716-446655440000",
  "gce_report_id": "660e8400-e29b-41d4-a716-446655440000",
  "gce_target_id": "770e8400-e29b-41d4-a716-446655440000",
  "report_format": "XML",
  "full_report": "<xml>...</xml>",
  "gce_scan_started_at": "2025-01-22T10:00:00Z",
  "gce_scan_completed_at": "2025-01-22T11:30:00Z",
  "vulnerability_count": {
    "critical": 2,
    "high": 5,
    "medium": 10,
    "low": 15,
    "log": 20
  }
}
Response: Returns the created/updated GceResult object.

## Processing automatico dei risultati Nmap

### Formato open_ports
Il sistema estrae automaticamente le porte aperte e le organizza per protocollo:
- Solo le porte con stato "open" vengono incluse
- Le porte sono ordinate per numero
- Include informazioni su servizio, prodotto, versione quando disponibili

### Formato os_guess
Il sistema estrae solo l'OS più probabile (quello con accuracy più alta):
- Se non viene rilevato nessun OS, viene salvato un oggetto vuoto `{}`
- Include tutte le informazioni disponibili (vendor, type, osfamily, etc.)

### Note importanti
- Il processing avviene automaticamente quando `parsed_nmap_results` viene aggiornato
- Se la scansione non ha risultati o non rileva porte/OS, vengono salvati oggetti vuoti `{}`
- Il sistema assume sempre un singolo host (il primo nell'array hosts)