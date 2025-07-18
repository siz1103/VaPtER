# Docs/ScanResultsProcessing.md

# Processamento Risultati Scansione

## Panoramica

Questo documento descrive come i risultati delle scansioni nmap vengono processati e salvati nel sistema.

## Flusso di Processamento

### 1. Ricezione Risultati dal Plugin Nmap

Il plugin nmap invia i risultati parsati tramite una chiamata PATCH all'endpoint:
```
PATCH /api/orchestrator/scans/{scan_id}/
```

Con il seguente payload:
```json
{
  "parsed_nmap_results": {
    "scan_info": {...},
    "hosts": [...],
    "stats": {...}
  },
  "status": "Nmap Scan Completed",
  "completed_at": "2025-01-18T10:30:00Z"
}
```

### 2. Salvataggio e Processamento

Quando il backend riceve i risultati:

1. **Salvataggio Raw**: I risultati completi vengono salvati nel campo `parsed_nmap_results` del modello Scan
2. **Estrazione Dettagli**: Il metodo `perform_update` nel ScanViewSet chiama `ScanStatusService._extract_scan_details()`
3. **Processamento Automatico**: I dettagli vengono estratti e salvati in ScanDetail

### 3. Dati Estratti

#### Open Ports
Le porte aperte vengono estratte e salvate in `scan_detail.open_ports`:
```json
[
  {
    "port": "22",
    "protocol": "tcp",
    "state": "open",
    "service": {
      "name": "ssh",
      "product": "OpenSSH",
      "version": "8.2p1",
      "extrainfo": "Ubuntu"
    }
  }
]
```

#### OS Guess
Le informazioni del sistema operativo vengono estratte e salvate in `scan_detail.os_guess`:
```json
{
  "name": "Linux 4.15 - 5.6",
  "accuracy": "96",
  "type": "general purpose",
  "vendor": "Linux",
  "osfamily": "Linux",
  "osgen": "4.X"
}
```

## Utilizzo dei Dati

### API Response
I dati estratti sono automaticamente inclusi nella risposta API quando si richiede una scansione:
```bash
GET /api/orchestrator/scans/{scan_id}/
```

### Frontend Display
Il frontend può mostrare:
- Lista delle porte aperte con servizi e versioni
- Sistema operativo rilevato con accuratezza
- Informazioni dettagliate sui servizi

### Plugin Futuri
I plugin non ancora implementati potranno utilizzare questi dati:
- **Fingerprint**: Approfondire l'identificazione dei servizi
- **Enum**: Enumerare basandosi sulle porte e servizi trovati
- **Web**: Analizzare solo le porte web (80, 443, 8080, etc.)
- **Vuln Lookup**: Cercare CVE per le versioni software identificate

## Note Implementative

### Gestione Errori
- Se il parsing fallisce, i campi rimangono vuoti ma non bloccano il processo
- Gli errori vengono loggati per debug

### Performance
- L'estrazione avviene solo quando `parsed_nmap_results` viene aggiornato
- I dati vengono salvati una sola volta per evitare duplicazioni

### Estensibilità
- La struttura supporta l'aggiunta di nuovi campi
- I plugin futuri possono arricchire i dati esistenti