# plugins/gce_scanner/README.md

# GCE Scanner Plugin

Il plugin GCE Scanner per VaPtER fornisce integrazione con Greenbone Community Edition per scansioni di vulnerabilità avanzate.

## ⚠️ Nota Importante sulla Compatibilità

Il plugin potrebbe riscontrare problemi di compatibilità con diverse versioni di GMP (Greenbone Management Protocol). 

### Fix Rapido per Errori di Versione

Se riscontri l'errore `Remote manager daemon uses an unsupported version of GMP`:

```bash
# Opzione 1: Script di fix automatico
chmod +x fix-gmp-version.sh
./fix-gmp-version.sh

# Opzione 2: Fix manuale
docker-compose exec gce_scanner pip uninstall -y python-gvm
docker-compose exec gce_scanner pip install git+https://github.com/greenbone/python-gvm.git@main
docker-compose restart gce_scanner

# Opzione 3: Debug per capire il problema
docker-compose exec gce_scanner python debug_gmp.py
```

## Funzionalità

- Creazione automatica di target in GCE basati sui risultati Nmap
- Avvio e monitoraggio di scansioni di vulnerabilità
- Recupero dei report completi (XML o JSON)
- Aggiornamento progressivo dello stato delle scansioni
- Gestione errori e retry automatici

## Requisiti

- Docker
- Accesso al socket Unix di GCE (`/run/gvmd/gvmd.sock`)
- Python 3.12+
- Credenziali valide per GCE

## Configurazione

Il plugin utilizza le seguenti variabili d'ambiente:

```bash
# Autenticazione GCE
GCE_USERNAME=vapter_api
GCE_PASSWORD=your_secure_password
GCE_SOCKET_PATH=/mnt/gce_sockets/gvmd.sock

# Configurazione scansioni
GCE_SCAN_CONFIG_ID=daba56c8-73ec-11df-a475-002264764cea  # Full and fast
GCE_SCANNER_ID=08b69003-5fc2-4037-a479-93b440211c73      # OpenVAS Default
GCE_PORT_LIST_ID=730ef368-57e2-11e1-a90f-406186ea4fc5    # All TCP and Nmap top 100 UDP

# Timing
GCE_POLLING_INTERVAL=60   # Intervallo di polling in secondi
GCE_MAX_SCAN_TIME=14400   # Timeout massimo scansione (4 ore)
```

## Setup

### 1. Configurare GCE

Assicurarsi che GCE sia in esecuzione e creare l'utente API:

```bash
# Accedere a GCE web UI
# http://vapter.szini.it:8443

# Creare utente 'vapter_api' con ruolo Admin
# O via CLI:
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd \
  gvmd --create-user=vapter_api --password=your_secure_password
```

### 2. Configurare i volumi

Il socket di GCE deve essere accessibile al container VaPtER:

```bash
# Verificare che il volume esista
docker volume ls | grep gvmd_socket_vol

# O creare manualmente una directory condivisa
sudo mkdir -p /opt/gce/sockets
sudo chown 1001:1001 /opt/gce/sockets
```

### 3. Aggiornare docker-compose.yml

Assicurarsi che il volume sia montato correttamente:

```yaml
volumes:
  # Per volume Docker
  - gvmd_socket_vol:/mnt/gce_sockets:ro
  
  # O per directory manuale
  - /opt/gce/sockets:/mnt/gce_sockets:ro
```

## Utilizzo

Il plugin viene attivato automaticamente quando:

1. Un scan ha completato la fase nmap (e fingerprint se abilitata)
2. Il scan type ha `plugin_gce=True`
3. Il target è raggiungibile

### Flusso di lavoro

1. **Ricezione messaggio**: Riceve richiesta dalla coda `gce_scan_requests`
2. **Creazione target**: Crea il target in GCE
3. **Creazione task**: Crea il task di scansione
4. **Avvio scansione**: Avvia la scansione in GCE
5. **Monitoraggio**: Polling dello stato ogni 60 secondi
6. **Recupero report**: Scarica il report completo
7. **Salvataggio**: Salva i risultati nel database VaPtER

## Test

### Test connessione

```bash
# Eseguire il test di connessione
docker-compose exec gce_scanner python test_gce.py

# Verificare i log
docker-compose logs -f gce_scanner
```

### Test manuale

```bash
# Inviare una richiesta di test
docker-compose exec backend python -c "
from orchestrator_api.services import RabbitMQService
rabbitmq = RabbitMQService()
rabbitmq.publish_message('gce_scan_requests', {
    'scan_id': 1,
    'target_id': 1,
    'target_host': '192.168.1.100',
    'plugin': 'gce'
})
"
```

## Troubleshooting

### Socket non trovato

```bash
# Verificare che GCE sia in esecuzione
docker compose -f docker-compose-gce.yml ps

# Verificare il percorso del socket
docker compose -f docker-compose-gce.yml exec gvmd ls -la /run/gvmd/

# Verificare i permessi
ls -la /var/lib/docker/volumes/gvmd_socket_vol/_data/
```

### Autenticazione fallita

```bash
# Verificare le credenziali
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd \
  gvmd --get-users

# Reset password
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd \
  gvmd --user=vapter_api --new-password=new_password
```

### Scansioni lente

- Verificare le risorse del sistema (CPU, RAM)
- Controllare il numero di host/porte da scansionare
- Considerare l'uso di profili di scansione più leggeri

## Struttura dati

### Input (da RabbitMQ)
```json
{
    "scan_id": 123,
    "target_id": 456,
    "target_host": "192.168.1.100",
    "plugin": "gce"
}
```

### Output (GceResult)
```json
{
    "scan": 123,
    "target": 456,
    "gce_task_id": "uuid",
    "gce_report_id": "uuid",
    "gce_target_id": "uuid",
    "report_format": "XML",
    "full_report": "<xml>...</xml>",
    "vulnerability_count": {
        "critical": 2,
        "high": 5,
        "medium": 10,
        "low": 15,
        "log": 20
    },
    "gce_scan_started_at": "2025-01-20T10:00:00Z",
    "gce_scan_completed_at": "2025-01-20T11:30:00Z"
}
```

## Estensioni future

- Parsing dettagliato dei report XML per estrarre vulnerabilità
- Supporto per scansioni autenticate con credenziali
- Selezione dinamica del profilo di scansione
- Integrazione con feed di vulnerabilità personalizzati
- Report differenziali tra scansioni successive