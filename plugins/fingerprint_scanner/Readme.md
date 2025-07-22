# plugins/fingerprint_scanner/README.md

# Fingerprint Scanner Plugin

Il plugin Fingerprint Scanner per VaPtER fornisce capacità avanzate di identificazione dei servizi utilizzando FingerprintX e altri strumenti.

## Funzionalità

1. Estrazione corretta dell'host

Ora estrae correttamente l'IP dall'array addresses
Preferisce l'hostname quando disponibile (come hai richiesto)
Log più dettagliati per il debugging

2. Mapping corretto dei campi del database

port: intero (es. 22)
protocol: transport protocol (tcp/udp)
service_name: application protocol (ssh, http, smtp, etc.)
service_product: software name (OpenSSH, Exim, nginx, etc.)
service_version: versione (9.6p1, 4.92, etc.)
service_info: informazioni aggiuntive estratte dal banner

3. Parser del banner migliorato
La funzione parse_banner ora gestisce correttamente:

SSH: estrae OpenSSH e versione 9.6p1 da "SSH-2.0-OpenSSH_9.6p1 Ubuntu-3ubuntu13.12"
SMTP: estrae Exim e 4.92 da "220 hostname ESMTP Exim 4.92"
HTTP: estrae prodotto e versione dal formato "nginx/1.18.0"
Altri protocolli: parsing generico per pattern comuni

4. Gestione metadata migliorata

I metadata vengono salvati in modo strutturato in additional_info
Campi speciali come ssh_algorithms e password_auth_enabled vengono estratti
Il banner originale viene preservato

5. Logging e debugging

Rispetta la variabile d'ambiente LOG_LEVEL
Log dettagliati del JSON raw di FingerprintX per debugging
Log informativi del processo di parsing

6. Gestione dei risultati

Salva anche risultati "no_match" se contengono dati utili
Confidence score adattivo (95% per success, 50% per no_match)
Summary migliorato per il report finale

Il plugin ora dovrebbe:

Estrarre correttamente gli host dai risultati nmap
Eseguire FingerprintX su ogni porta aperta
Parsare intelligentemente i banner per estrarre product e version
Salvare i dati nel formato corretto nel database
Fornire log dettagliati per il debugging

## Requisiti

- Docker con immagine Kali Linux
- FingerprintX (installato automaticamente)
- Python 3.x
- RabbitMQ per la comunicazione
- API Gateway per il salvataggio dei risultati

## Configurazione

Il plugin utilizza le seguenti variabili d'ambiente:

```bash
FINGERPRINT_TIMEOUT_PER_PORT=60      # Timeout per porta in secondi
MAX_CONCURRENT_FINGERPRINTS=10       # Numero massimo di scan paralleli
FINGERPRINT_MAX_RETRIES=3            # Tentativi per porta
FINGERPRINT_RETRY_DELAY=5            # Delay tra tentativi
```

## Utilizzo

Il plugin viene attivato automaticamente quando:

1. Un scan ha completato la fase nmap
2. Il scan type ha `plugin_finger=True`
3. Ci sono porte aperte da analizzare

### Flusso di lavoro

1. **Ricezione messaggio**: Il plugin riceve un messaggio dalla coda `fingerprint_scan_requests`
2. **Recupero dati nmap**: Ottiene i risultati nmap dal backend
3. **Estrazione porte**: Identifica tutte le porte aperte
4. **Fingerprinting**: Esegue FingerprintX su ogni porta
5. **Salvataggio risultati**: Salva i dettagli nel database
6. **Aggiornamento stato**: Notifica il completamento

## Test

Per testare il plugin:

```bash
# Eseguire il test di verifica installazione
docker-compose exec fingerprint_scanner python test_fingerprint.py

# Verificare i log
docker-compose logs -f fingerprint_scanner

# Test manuale dal backend
docker-compose exec backend python test_fingerprint_plugin.py
```

## Struttura dati

### Input (da RabbitMQ)
```json
{
    "scan_id": 123,
    "target_id": 456,
    "target_host": "192.168.1.100",
    "plugin": "fingerprint"
}
```

### Output (FingerprintDetail)
```json
{
    "scan": 123,
    "target": 456,
    "port": 22,
    "protocol": "tcp",
    "service_name": "ssh",
    "service_version": "OpenSSH 8.2p1",
    "service_product": "OpenSSH",
    "fingerprint_method": "fingerprintx",
    "confidence_score": 95,
    "raw_response": "...",
    "additional_info": {
        "host": "192.168.1.100",
        "scan_timestamp": "2025-01-20T10:00:00Z"
    }
}
```

## Troubleshooting

### Il plugin non si avvia
- Verificare la connessione a RabbitMQ
- Controllare che FingerprintX sia installato: `docker-compose exec fingerprint_scanner which fingerprintx`

### Nessun risultato salvato
- Verificare la connessione all'API Gateway
- Controllare i permessi di rete del container
- Verificare che ci siano porte aperte nei risultati nmap

### Timeout frequenti
- Aumentare `FINGERPRINT_TIMEOUT_PER_PORT`
- Ridurre `MAX_CONCURRENT_FINGERPRINTS`
- Verificare la connettività verso i target

## Estensioni future

- Supporto per altri tool di fingerprinting (banner grabbing, etc.)
- Integrazione con database di signature personalizzate
- Machine learning per migliorare l'accuratezza
- Caching dei risultati per ottimizzare le performance