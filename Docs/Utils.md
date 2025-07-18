## Comandi Utili (Sviluppo Locale)

### Comandi per setup iniziale

**Assumendo che si sia nella root del progetto.**

#### Setup Docker Environment

```bash
# Copiare e configurare le variabili d'ambiente
cp .env.example .env
# Editare il file .env con i valori desiderati

# Costruire tutti i container (incluso API Gateway)
docker-compose build

# Ricostruire un singolo container
docker-compose build backend
docker-compose build api_gateway

# Avviare tutti i servizi
docker-compose up -d

# Avviare solo alcuni servizi
docker-compose up -d db rabbitmq backend api_gateway

# Riavviare un singolo container
docker-compose restart backend
docker-compose restart api_gateway
docker-compose restart backend_consumer

# Visualizzare i log dei servizi
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f api_gateway
docker-compose logs -f backend_consumer
docker-compose logs -f rabbitmq

# Fermare i container
docker-compose down

# Fermare i container e rimuovere i volumi (ATTENZIONE: cancella i dati)
docker-compose down -v
```

#### Setup Database e Migrazioni

```bash
# Eseguire le migrazioni del database
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Caricare i dati iniziali (PortList e ScanType)
docker-compose exec backend python manage.py loaddata initial_data.json

# Creare un superutente per l'admin
docker-compose exec backend python manage.py createsuperuser

# Raccogliere i file statici
docker-compose exec backend python manage.py collectstatic --noinput
```

#### Gestione del Consumer RabbitMQ

```bash
# Verificare che il consumer sia in esecuzione
docker-compose logs backend_consumer

# Avviare il consumer manualmente (se non in esecuzione automatica)
docker-compose exec backend python manage.py consume_scan_status

# Avviare il consumer con parametri personalizzati
docker-compose exec backend python manage.py consume_scan_status --queue=scan_status_updates --prefetch=5

# Verificare le code RabbitMQ (accesso web)
# Andare a http://vapter.szini.it:15672
# Username: vapter, Password: vapter123
```

### Comandi API Gateway

#### Debug e Monitoraggio Gateway

```bash
# Accedere al container API Gateway
docker-compose exec api_gateway bash

# Verificare configurazione Gateway
docker-compose exec api_gateway env | grep -E "(BACKEND_URL|DEBUG|LOG_LEVEL)"

# Visualizzare logs in tempo reale
docker-compose logs -f api_gateway

# Test health check del gateway
curl http://vapter.szini.it:8080/health/
curl http://vapter.szini.it:8080/health/detailed

# Test connettività interna Gateway -> Backend
docker-compose exec api_gateway curl http://backend:8000/api/orchestrator/customers/

# Riavviare solo il gateway
docker-compose restart api_gateway

# Rebuild del gateway con nuove modifiche
docker-compose build api_gateway && docker-compose up -d api_gateway
```

#### Configurazione Gateway

```bash
# Verificare variabili d'ambiente del gateway
docker-compose exec api_gateway printenv | grep -E "(BACKEND|CORS|LOG)"

# Test configurazione CORS
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://vapter.szini.it:8080/api/orchestrator/customers/

# Verificare timeout configurato
docker-compose exec api_gateway python -c "from app.config import settings; print(f'Backend URL: {settings.BACKEND_URL}, Timeout: {settings.BACKEND_TIMEOUT}')"
```

### Comandi Frontend

#### Gestione Frontend Development

```bash
# Accedere al container frontend
docker-compose exec frontend sh

# Verificare logs del frontend
docker-compose logs -f frontend

# Rebuild frontend dopo modifiche a package.json
docker-compose build frontend && docker-compose up -d frontend

# Verificare che il frontend sia raggiungibile
curl http://vapter.szini.it:3000/

# Test proxy API dal frontend al gateway
docker-compose exec frontend wget -O- http://api_gateway:8080/health/
```

#### Sviluppo Frontend

```bash
# Installare una nuova dipendenza nel frontend
docker-compose exec frontend npm install nome-pacchetto

# Verificare errori TypeScript
docker-compose exec frontend npm run build

# Verificare lint
docker-compose exec frontend npm run lint
```

Aggiungo comandi utili per Targets:

### Test Targets

#### Creazione Target
```bash
# Creare un target per un customer specifico
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "CUSTOMER_UUID_HERE",
    "name": "Production Web Server",
    "address": "192.168.1.100",
    "description": "Main production web server"
  }'

# Ottenere lista targets di un customer
curl "http://vapter.szini.it:8080/api/orchestrator/targets/?customer=CUSTOMER_UUID_HERE"

# Avviare una scansione su un target
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/TARGET_ID/scan/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type_id": 2}'

# Nel browser console (F12)
# Test validazione IP
import { validateIPAddress } from '/src/services/targetService'
console.log(validateIPAddress('192.168.1.1')) // true
console.log(validateIPAddress('256.1.1.1')) // false

# Test validazione FQDN
import { validateFQDN } from '/src/services/targetService'
console.log(validateFQDN('example.com')) // true
console.log(validateFQDN('example..com')) // false


### Comandi di Sviluppo

#### Debugging e Sviluppo

```bash
# Accedere al container backend per debug
docker-compose exec backend bash

# Accedere al container API Gateway per debug
docker-compose exec api_gateway bash

# Accedere alla shell Django
docker-compose exec backend python manage.py shell

# Eseguire shell Django con IPython
docker-compose exec backend python manage.py shell_plus

# Eseguire i test (quando saranno implementati)
docker-compose exec backend python manage.py test

# Verificare la configurazione Django
docker-compose exec backend python manage.py check

# Visualizzare le URL disponibili Django
docker-compose exec backend python manage.py show_urls

# Test diretto con Python nel gateway
docker-compose exec api_gateway python -c "
import httpx
response = httpx.get('http://backend:8000/api/orchestrator/customers/')
print(f'Status: {response.status_code}')
"
```

#### Gestione Database

```bash
# Eseguire migrazioni specifiche
docker-compose exec backend python manage.py migrate orchestrator_api

# Creare una nuova migrazione
docker-compose exec backend python manage.py makemigrations orchestrator_api

# Rollback delle migrazioni
docker-compose exec backend python manage.py migrate orchestrator_api 0001

# Dump del database
docker-compose exec backend python manage.py dumpdata > backup.json

# Load del database da backup
docker-compose exec backend python manage.py loaddata backup.json

# Reset del database (ATTENZIONE: cancella tutti i dati)
docker-compose exec backend python manage.py flush
```

#### API Testing

```bash
# Test API tramite Gateway (metodo raccomandato)
# Ottenere lista clienti
curl -X GET http://vapter.szini.it:8080/api/orchestrator/customers/

# Creare un nuovo cliente
curl -X POST http://vapter.szini.it:8080/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Customer", "email": "test@example.com"}'

# Test con headers personalizzati
curl -H "X-Custom-Header: test" http://vapter.szini.it:8080/api/orchestrator/customers/

# Test API tramite Backend diretto (solo development)
curl -X GET http://vapter.szini.it:8000/api/orchestrator/customers/

# Ottenere lista scan types
curl -X GET http://vapter.szini.it:8080/api/orchestrator/scan-types/

# Ottenere lista port lists
curl -X GET http://vapter.szini.it:8080/api/orchestrator/port-lists/

# Test performance comparison
echo "Gateway:" && time curl -s http://vapter.szini.it:8080/api/orchestrator/customers/ > /dev/null
echo "Backend:" && time curl -s http://vapter.szini.it:8000/api/orchestrator/customers/ > /dev/null
```

#### Test Load e Performance

```bash
# Test carico API Gateway
for i in {1..20}; do
  curl -s http://vapter.szini.it:8080/api/orchestrator/customers/ > /dev/null &
done
wait

# Test concorrenza
seq 1 50 | xargs -n1 -P10 -I{} curl -s http://vapter.szini.it:8080/health/ > /dev/null

# Monitorare requests nel gateway durante il test
docker-compose logs -f api_gateway | grep "GET.*customers"

# Test timeout (configurare BACKEND_TIMEOUT basso per test)
curl -m 30 http://vapter.szini.it:8080/api/orchestrator/scans/
```

### Comandi di Manutenzione

#### Pulizia Docker

```bash
# Rimuovere immagini dangling
docker images -q --filter "dangling=true" | xargs -r docker rmi

# Pulizia completa Docker (ATTENZIONE: rimuove tutto)
docker system prune -a

# Rimuovere solo i volumi non utilizzati
docker volume prune

# Vedere lo spazio utilizzato da Docker
docker system df

# Rimuovere solo l'immagine del gateway per rebuild
docker rmi $(docker images | grep vapter_api_gateway | awk '{print $3}')
```

#### Backup e Restore

```bash
# Backup del database PostgreSQL
docker-compose exec db pg_dump -U vapter vapter > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore del database PostgreSQL
docker-compose exec -T db psql -U vapter vapter < backup_file.sql

# Backup dei volumi Docker
docker run --rm -v vapter_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Backup della configurazione gateway
docker-compose exec api_gateway cat /app/app/config.py > gateway_config_backup.py
```

### URL di Accesso

#### Servizi Web

- **API Gateway**: http://vapter.szini.it:8080/
- **API Gateway Docs**: http://vapter.szini.it:8080/docs
- **API Gateway Health**: http://vapter.szini.it:8080/health/detailed
- **Backend API**: http://vapter.szini.it:8000/api/orchestrator/
- **Django Admin**: http://vapter.szini.it:8000/admin/
- **Backend API Documentation**: http://vapter.szini.it:8000/api/schema/swagger-ui/
- **RabbitMQ Management**: http://vapter.szini.it:15672/ (vapter/vapter123)

#### API Endpoints Principali (tramite Gateway)

- **Root Gateway**: `/`
- **Health Checks**: `/health/`, `/health/detailed`, `/health/readiness`, `/health/liveness`
- **Customers**: `/api/orchestrator/customers/`
- **Targets**: `/api/orchestrator/targets/`
- **Scans**: `/api/orchestrator/scans/`
- **Scan Types**: `/api/orchestrator/scan-types/`
- **Port Lists**: `/api/orchestrator/port-lists/`

### Troubleshooting

#### Problemi Comuni

```bash
# Verificare lo stato dei container
docker-compose ps

# Verificare i log di un servizio che non si avvia
docker-compose logs backend
docker-compose logs api_gateway

# Riavviare tutti i servizi
docker-compose restart

# Verificare la connettività al database
docker-compose exec backend python manage.py dbshell

# Verificare la connessione a RabbitMQ
docker-compose exec backend python -c "import pika; pika.BlockingConnection(pika.URLParameters('amqp://vapter:vapter123@rabbitmq:5672/'))"

# Testare consumer RabbitMQ
docker-compose exec backend python manage.py consume_scan_status --verbosity=2
```

#### Troubleshooting API Gateway

```bash
# Verificare health dell'API Gateway
curl http://vapter.szini.it:8080/health/detailed

# Se il gateway non risponde
docker-compose logs api_gateway
docker-compose restart api_gateway

# Test connettività interna Gateway -> Backend
docker-compose exec api_gateway curl http://backend:8000/health/
docker-compose exec api_gateway curl http://backend:8000/api/orchestrator/customers/

# Verificare configurazione CORS
curl -H "Origin: http://localhost:3000" -I http://vapter.szini.it:8080/api/orchestrator/customers/

# Test timeout del gateway
curl -m 5 http://vapter.szini.it:8080/api/orchestrator/scans/

# Verificare headers di risposta del gateway
curl -I http://vapter.szini.it:8080/api/orchestrator/customers/
```

#### Debug Communication Issues

```bash
# Test comunicazione completa: Gateway -> Backend -> Database
curl -v http://vapter.szini.it:8080/api/orchestrator/customers/ 2>&1 | grep -E "(HTTP|X-Request-ID|X-Process-Time)"

# Verificare che il backend sia raggiungibile dal gateway
docker-compose exec api_gateway ping backend

# Verificare porte aperte nei container
docker-compose exec backend netstat -tlnp | grep 8000
docker-compose exec api_gateway netstat -tlnp | grep 8080

# Test con JSON invalido per verificare error handling
curl -X POST http://vapter.szini.it:8080/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{"invalid": json}'
```

#### Reset Completo

```bash
# ATTENZIONE: Cancella tutti i dati e le immagini
docker-compose down -v
docker system prune -a
docker-compose build --no-cache
docker-compose up -d

# Verifica che tutti i servizi siano healthy
curl http://vapter.szini.it:8080/health/detailed
curl http://vapter.szini.it:8000/api/orchestrator/customers/
```

### Development Workflow

#### Sviluppo con Hot Reload

```bash
# Sviluppo backend (modifiche ai file Django)
# I file sono montati come volume, restart automatico

# Sviluppo API Gateway (modifiche ai file FastAPI)
# I file sono montati come volume, restart automatico con uvicorn --reload

# Per forzare restart di un servizio dopo modifiche
docker-compose restart api_gateway
docker-compose restart backend

# Build incrementale solo di un servizio
docker-compose build api_gateway && docker-compose up -d api_gateway
```

#### Testing Durante Sviluppo

```bash
# Test rapido della pipeline completa
curl -X POST http://vapter.szini.it:8080/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Dev", "email": "dev@test.com"}' \
&& curl http://vapter.szini.it:8080/api/orchestrator/customers/

# Monitoraggio logs durante sviluppo
docker-compose logs -f api_gateway backend

# Test specifico endpoint con timing
time curl -s http://vapter.szini.it:8080/api/orchestrator/customers/ | jq .
```

### Comandi Utili per il Deployment

```bash
# Verifica finale prima del deployment
docker-compose config
docker-compose ps
curl http://vapter.szini.it:8080/health/detailed

# Backup prima di deployment
docker-compose exec db pg_dump -U vapter vapter > pre_deploy_backup.sql

# Deploy con zero downtime (se possibile)
docker-compose build
docker-compose up -d --no-deps api_gateway
docker-compose up -d --no-deps backend
```