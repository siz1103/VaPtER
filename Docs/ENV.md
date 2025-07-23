## Variabili d'ambiente necessarie (.env)

Il sistema VaPtER utilizza diverse variabili d'ambiente per la configurazione. Di seguito la documentazione completa:

### Configurazione Generale

| Variabile | Descrizione | Valore di Default | Obbligatoria |
|-----------|-------------|------------------|--------------|
| `ENVIRONMENT` | Ambiente di esecuzione | `development` | No |
| `PROJECT_NAME` | Nome del progetto | `VaPtER` | No |
| `PROJECT_VERSION` | Versione del progetto | `1.0.0` | No |
| `DEBUG` | Modalità debug Django | `True` | No |
| `DOMAIN` | Dominio principale | `vapter.szini.it` | Sì |
| `PROTOCOL` | Protocollo (http/https) | `http` | No |

### URL Esterni (Accesso Client)

| Variabile | Descrizione | Valore di Default |
|-----------|-------------|------------------|
| `EXTERNAL_GATEWAY_URL` | URL pubblico API Gateway | `http://vapter.szini.it:8080` |
| `EXTERNAL_BACKEND_URL` | URL pubblico Backend | `http://vapter.szini.it:8000` |
| `EXTERNAL_FRONTEND_URL` | URL pubblico Frontend | `http://vapter.szini.it:3000` |
| `EXTERNAL_RABBITMQ_URL` | URL RabbitMQ Management | `http://vapter.szini.it:15672` |

### Configurazione Django

| Variabile | Descrizione | Valore di Default | Obbligatoria |
|-----------|-------------|------------------|--------------|
| `SECRET_KEY` | Chiave segreta Django | - | Sì |
| `ALLOWED_HOSTS` | Host permessi | `*` | No |
| `CORS_ALLOWED_ORIGINS` | Domini CORS permessi | `http://vapter.szini.it:3000,http://localhost:3000` | No |

### Configurazione Database

| Variabile | Descrizione | Valore di Default | Obbligatoria |
|-----------|-------------|------------------|--------------|
| `POSTGRES_DB` | Nome database | `vapter` | Sì |
| `POSTGRES_USER` | Username database | `vapter` | Sì |
| `POSTGRES_PASSWORD` | Password database | `vapter123` | Sì |
| `DATABASE_URL` | URL completo database | `postgresql://vapter:vapter123@db:5432/vapter` | Sì |

### Configurazione RabbitMQ

| Variabile | Descrizione | Valore di Default | Obbligatoria |
|-----------|-------------|------------------|--------------|
| `RABBITMQ_USER` | Username RabbitMQ | `vapter` | Sì |
| `RABBITMQ_PASSWORD` | Password RabbitMQ | `vapter123` | Sì |
| `RABBITMQ_URL` | URL completo RabbitMQ | `amqp://vapter:vapter123@rabbitmq:5672/` | Sì |

### Code RabbitMQ (Opzionali - Override dei Default)

| Variabile | Descrizione | Valore di Default |
|-----------|-------------|------------------|
| `RABBITMQ_NMAP_SCAN_REQUEST_QUEUE` | Coda richieste scan Nmap | `nmap_scan_requests` |
| `RABBITMQ_GCE_SCAN_REQUEST_QUEUE` | Coda richieste scan Gce | `gce_scan_requests` |
| `RABBITMQ_FINGERPRINT_SCAN_REQUEST_QUEUE` | Coda richieste scan Fingerprint | `fingerprint_scan_requests` |
| `RABBITMQ_WEB_SCAN_REQUEST_QUEUE` | Coda richieste scan Web | `web_scan_requests` |
| `RABBITMQ_VULN_LOOKUP_REQUEST_QUEUE` | Coda richieste lookup vulnerabilità | `vuln_lookup_requests` |
| `RABBITMQ_REPORT_REQUEST_QUEUE` | Coda richieste generazione report | `report_requests` |
| `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE` | Coda aggiornamenti stato scan | `scan_status_updates` |

### Configurazione Frontend

| Variabile | Descrizione | Valore di Default |
|-----------|-------------|------------------|
| `VITE_API_URL` | URL base per le chiamate API | `/api` |

### Comunicazione Interna

| Variabile | Descrizione | Valore di Default | Obbligatoria |
|-----------|-------------|------------------|--------------|
| `INTERNAL_API_GATEWAY_URL` | URL interno API Gateway | `http://api_gateway:8080` | Sì |

### Configurazione Logging

| Variabile | Descrizione | Valore di Default |
|-----------|-------------|------------------|
| `LOG_LEVEL` | Livello di logging | `INFO` |

## File di Configurazione

### .env (Produzione)
Creare questo file nella root del progetto con i valori specifici per l'ambiente di produzione.

### .env.example
File template con tutti i valori di esempio per lo sviluppo.

## Note di Sicurezza

### Variabili Critiche da Cambiare in Produzione:
- `SECRET_KEY`: Deve essere una stringa lunga e random
- `POSTGRES_PASSWORD`: Password sicura per il database
- `RABBITMQ_PASSWORD`: Password sicura per RabbitMQ
- `DEBUG`: Deve essere `False` in produzione
- `ALLOWED_HOSTS`: Specificare domini specifici invece di `*`

### Esempio Produzione:
```bash
DEBUG=False
SECRET_KEY=your-very-long-random-secret-key-here-minimum-50-characters
POSTGRES_PASSWORD=very-secure-database-password-here
RABBITMQ_PASSWORD=very-secure-rabbitmq-password-here
ALLOWED_HOSTS=vapter.yourdomain.com
PROTOCOL=https
```

## Greenbone Community Edition (GCE) Configuration

### GCE Authentication
- `GCE_USERNAME` - Username per l'autenticazione con GCE (default: `vapter_api`)
- `GCE_PASSWORD` - Password per l'autenticazione con GCE (richiesto, no default)
- `GCE_SOCKET_PATH` - Percorso del socket Unix di GVMD (default: `/mnt/gce_sockets/gvmd.sock`)

### GCE Scanner Settings
- `GCE_SCAN_CONFIG_ID` - UUID della configurazione di scansione da usare (default: `daba56c8-73ec-11df-a475-002264764cea` - Full and fast)
- `GCE_SCANNER_ID` - UUID dello scanner da utilizzare (default: `08b69003-5fc2-4037-a479-93b440211c73` - OpenVAS Default)
- `GCE_PORT_LIST_ID` - UUID della port list da utilizzare (default: `730ef368-57e2-11e1-a90f-406186ea4fc5` - All TCP and Nmap top 100 UDP)

### GCE Plugin Configuration
- `GCE_POLLING_INTERVAL` - Intervallo di polling in secondi per verificare lo stato della scansione (default: `60`)
- `GCE_MAX_SCAN_TIME` - Timeout massimo per una scansione in secondi (default: `14400` - 4 ore)
- `GCE_REPORT_FORMAT` - Formato del report da salvare: XML o JSON (default: `XML`)

### GCE Docker Configuration (.env.gce)
File separato per la configurazione di GCE stesso:

- `GCE_ADMIN_USER` - Username amministratore di GCE (default: `admin`)
- `GCE_ADMIN_PASSWORD` - Password amministratore di GCE (richiesto)
- `GCE_VAPTER_USER` - Username per l'utente API dedicato a VaPtER (default: `vapter_api`)
- `GCE_VAPTER_PASSWORD` - Password per l'utente API di VaPtER (richiesto)
- `GCE_WEB_PORT` - Porta per l'interfaccia web di GCE (default: `8443`)
- `GCE_API_PORT` - Porta per l'API OpenVASD (default: `9390`)
- `FEED_RELEASE` - Versione dei feed di vulnerabilità (default: `24.10`)

### Volume Configuration
Il plugin GCE richiede accesso al socket Unix di GVMD. Nel docker-compose.yml:

```yaml
volumes:
  # Opzione 1: Docker volume
  - gvmd_socket_vol:/mnt/gce_sockets:ro
  
  # Opzione 2: Directory host
  - /opt/gce/sockets:/mnt/gce_sockets:ro
```