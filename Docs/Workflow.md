# Docs/Workflow.md

# Workflow di Scansione

## Panoramica del Flusso

Il sistema utilizza un'architettura basata su microservizi con RabbitMQ per orchestrare le scansioni di vulnerabilità. Ogni componente opera in modo indipendente e comunica attraverso code di messaggi.

## Stati della Scansione

Una scansione può trovarsi in uno dei seguenti stati:

1. **Pending** - Scansione creata ma non ancora in coda
2. **Queued** - Scansione in coda per l'elaborazione
3. **Nmap Scan Running** - Scansione delle porte in corso
4. **Nmap Scan Completed** - Scansione delle porte completata
5. **Finger Scan Running** - Fingerprinting in corso *(Non implementato)*
6. **Finger Scan Completed** - Fingerprinting completato *(Non implementato)*
7. **Enum Scan Running** - Enumerazione in corso *(Non implementato)*
8. **Enum Scan Completed** - Enumerazione completata *(Non implementato)*
9. **Web Scan Running** - Scansione web in corso *(Non implementato)*
10. **Web Scan Completed** - Scansione web completata *(Non implementato)*
11. **Vuln Lookup Running** - Ricerca vulnerabilità in corso *(Non implementato)*
12. **Vuln Lookup Completed** - Ricerca vulnerabilità completata *(Non implementato)*
13. **Report Generation Running** - Generazione report in corso *(Non implementato)*
14. **Completed** - Scansione completata con successo
15. **Failed** - Scansione fallita

## Flusso di Esecuzione

### 1. Creazione Scansione
- L'utente crea una nuova scansione tramite API
- Il sistema valida i parametri (target, scan_type)
- **NOTA**: È possibile creare più scansioni sullo stesso target, anche con scan_type diversi
- La scansione viene salvata con stato `Pending`

### 2. Accodamento
- Il servizio `ScanOrchestratorService` pubblica un messaggio nella coda `nmap_scan_requests`
- Lo stato passa a `Queued`

### 3. Esecuzione Nmap
- Il plugin Nmap preleva il messaggio dalla coda
- Esegue la scansione delle porte in base alla configurazione
- Aggiorna lo stato a `Nmap Scan Running`
- Al termine, salva i risultati e aggiorna lo stato a `Nmap Scan Completed`

### 4. Plugin Successivi (Non Implementati)

**IMPORTANTE**: I seguenti plugin sono previsti nell'architettura ma non ancora implementati. Attualmente, dopo il completamento di Nmap, la scansione viene marcata come `Completed` anche se sono abilitati altri plugin.

#### Fingerprinting
- Se abilitato in scan_type, dovrebbe identificare servizi e versioni
- Utilizzerebbe i risultati di Nmap come input

#### Enumeration
- Se abilitato, dovrebbe enumerare informazioni aggiuntive
- Potrebbe includere: utenti, share, DNS, etc.

#### Web Scanning
- Se abilitato e vengono trovate porte web (80, 443, 8080, etc.)
- Dovrebbe eseguire scansioni specifiche per applicazioni web

#### Vulnerability Lookup
- Se abilitato, dovrebbe cercare CVE note
- Baserebbe la ricerca su servizi e versioni identificate

### 5. Generazione Report (Non Implementato)
- Dovrebbe aggregare tutti i risultati
- Generare report in vari formati (PDF, HTML, JSON)

## Code RabbitMQ

Il sistema utilizza le seguenti code:

- `nmap_scan_requests` - Richieste di scansione Nmap
- `fingerprint_scan_requests` - Richieste fingerprinting *(Non utilizzata)*
- `enum_scan_requests` - Richieste enumerazione *(Non utilizzata)*
- `web_scan_requests` - Richieste scansione web *(Non utilizzata)*
- `vuln_lookup_requests` - Richieste lookup vulnerabilità *(Non utilizzata)*
- `report_requests` - Richieste generazione report *(Non utilizzata)*
- `scan_status_updates` - Aggiornamenti stato da tutti i plugin

## Formato Messaggi

### Messaggio di Richiesta Scansione
```json
{
    "scan_id": 123,
    "scan_type_id": 1,
    "target_host": "192.168.1.100",
    "target_name": "Web Server",
    "customer_id": "abc-123",
    "timestamp": "2025-01-18T10:00:00Z"
}
```

### Messaggio di Aggiornamento Stato
```json
{
    "scan_id": 123,
    "module": "nmap",
    "status": "completed",
    "message": "Scan completed successfully",
    "error_details": null
}
```

## Gestione Errori

- Ogni plugin deve gestire i propri errori
- In caso di errore, lo stato passa a `Failed`
- I dettagli dell'errore vengono salvati nel campo `error_message`
- Il workflow si interrompe in caso di errore

## Considerazioni per lo Sviluppo Futuro

1. **Implementazione Plugin**: Quando si implementeranno i plugin mancanti, sarà necessario riattivare la logica di orchestrazione in `services.py`

2. **Parallelizzazione**: Valutare se alcuni plugin possono essere eseguiti in parallelo invece che sequenzialmente

3. **Timeout**: Implementare timeout per ogni fase per evitare scansioni bloccate

4. **Retry Logic**: Aggiungere logica di retry per errori temporanei

5. **Priorità**: Implementare sistema di priorità per le scansioni

## Note Temporanee

- **Plugin Non Implementati**: Al momento solo Nmap è funzionante. Gli altri plugin sono previsti ma non implementati.
- **Completamento Automatico**: Le scansioni vengono marcate come `Completed` dopo Nmap, indipendentemente dai plugin abilitati.
- **Scansioni Multiple**: È possibile lanciare più scansioni sullo stesso target senza restrizioni.