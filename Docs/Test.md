# 🚀 Guida Setup VaPtER - Test Completo con API Gateway

Questa guida ti aiuterà a configurare e testare i vari componenti implementati, incluso il nuovo API Gateway FastAPI.

## 📋 Prerequisiti

- Docker e Docker Compose installati
- Accesso alla shell/terminale
- Tool per test API (curl, Postman, o browser)

## 🔧 Setup Iniziale

### 1. Clone e Configurazione

```bash
# Clonare il repository (se necessario)
cd vapt_project_root

# Copiare e configurare environment
cp .env.example .env
# Editare .env se necessario per il proprio ambiente
```

### 2. Avvio Servizi

```bash
# Build e avvio di tutti i servizi (incluso API Gateway)
docker-compose build
docker-compose up -d

# Verificare che tutti i servizi siano attivi
docker-compose ps
```

**Output atteso:**
```
Name                   Command                  State           Ports
------------------------------------------------------------------------
vapter_api_gateway     uvicorn app.main:app ... Up             0.0.0.0:8080->8080/tcp
vapter_backend         sh -c python manage.py   Up             0.0.0.0:8000->8000/tcp
vapter_backend_consumer python manage.py con... Up
vapter_db              docker-entrypoint.s...   Up             0.0.0.0:5432->5432/tcp
vapter_rabbitmq        docker-entrypoint.s...   Up             0.0.0.0:15672->15672/tcp, 0.0.0.0:5672->5672/tcp
```

### 3. Setup Database

```bash
# Eseguire migrazioni
docker-compose exec backend python manage.py migrate

# Caricare dati iniziali
docker-compose exec backend python manage.py loaddata initial_data.json

# Creare superuser per admin
docker-compose exec backend python manage.py createsuperuser
```

## 🧪 Test dei Componenti

### 1. Test API Gateway

#### Verificare API Gateway Status

```bash
# Health check base
curl http://vapter.szini.it:8080/health/

# Health check dettagliato (verifica connessione backend)
curl http://vapter.szini.it:8080/health/detailed

# Readiness probe
curl http://vapter.szini.it:8080/health/readiness

# Liveness probe
curl http://vapter.szini.it:8080/health/liveness
```

**Output atteso per health check dettagliato:**
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

#### Verificare Documentazione API Gateway

1. Andare a: http://vapter.szini.it:8080/docs
2. Verificare che la documentazione FastAPI sia accessibile
3. Testare alcuni endpoint direttamente dall'interfaccia Swagger

#### Test Logging del Gateway

```bash
# Visualizzare i log del gateway
docker-compose logs -f api_gateway

# Fare una richiesta e verificare che venga loggata
curl http://vapter.szini.it:8080/api/orchestrator/customers/
```

**Log atteso:**
```
INFO:     [abc12345] GET http://vapter.szini.it:8080/api/orchestrator/customers/ - Client: 172.18.0.1 - User-Agent: curl/7.68.0
INFO:     [abc12345] GET http://vapter.szini.it:8080/api/orchestrator/customers/ - Status: 200 - Duration: 0.125s
```

### 2. Test Database e Django

#### Verificare Django Admin

1. Andare a: http://vapter.szini.it:8000/admin/
2. Login con le credenziali del superuser
3. Verificare che siano visibili tutte le sezioni:
   - Customers
   - Port Lists
   - Scan Types
   - Targets
   - Scans
   - Scan Details

#### Verificare Dati Iniziali

```bash
# Tramite API Gateway (raccomandato)
curl http://vapter.szini.it:8080/api/orchestrator/port-lists/
curl http://vapter.szini.it:8080/api/orchestrator/scan-types/

# Tramite Backend diretto (per confronto)
curl http://vapter.szini.it:8000/api/orchestrator/port-lists/
```

**Output atteso:** Liste con 5 Port Lists e 6 Scan Types predefiniti.

### 3. Test API REST Tramite Gateway

#### Test CRUD Completo - Customers

```bash
# 1. Creare un cliente (tramite Gateway)
curl -X POST http://vapter.szini.it:8080/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Corporation",
    "company_name": "Test Corp Ltd",
    "email": "admin@testcorp.com",
    "phone": "+1234567890",
    "contact_person": "John Doe"
  }'

# 2. Ottenere lista clienti
curl http://vapter.szini.it:8080/api/orchestrator/customers/

# 3. Ottenere cliente specifico (sostituire {id} con UUID restituito)
curl http://vapter.szini.it:8080/api/orchestrator/customers/{customer_id}/

# 4. Aggiornare cliente
curl -X PATCH http://vapter.szini.it:8080/api/orchestrator/customers/{customer_id}/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+9876543210"}'
```

#### Test CRUD Completo - Targets

```bash
# 1. Creare un target (sostituire {customer_id})
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "{customer_id}",
    "name": "Web Server Test",
    "address": "192.168.1.100",
    "description": "Server web di test"
  }'

# 2. Creare secondo target con FQDN
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "{customer_id}",
    "name": "DNS Server",
    "address": "google.com",
    "description": "Server DNS pubblico"
  }'

# 3. Ottenere lista targets
curl http://vapter.szini.it:8080/api/orchestrator/targets/

# 4. Ottenere targets di un cliente specifico
curl http://vapter.szini.it:8080/api/orchestrator/customers/{customer_id}/targets/
```

#### Test Creazione Scansioni

```bash
# 1. Ottenere lista scan types disponibili
curl http://vapter.szini.it:8080/api/orchestrator/scan-types/

# 2. Avviare scansione Discovery (sostituire {target_id})
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/{target_id}/scan/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type_id": 1}'

# 3. Avviare scansione completa
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/{target_id}/scan/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type_id": 3}'

# 4. Verificare lista scansioni
curl http://vapter.szini.it:8080/api/orchestrator/scans/

# 5. Ottenere dettagli scansione specifica
curl http://vapter.szini.it:8080/api/orchestrator/scans/{scan_id}/
```

### 4. Test RabbitMQ

#### Verificare RabbitMQ Management

1. Andare a: http://vapter.szini.it:15672/
2. Login: `vapter` / `vapter123`
3. Verificare che siano create le code:
   - `nmap_scan_requests`
   - `scan_status_updates`
   - E altre code definite nel settings

#### Test Consumer

```bash
# Verificare che il consumer sia in esecuzione
docker-compose logs backend_consumer

# Output atteso: "Waiting for messages. To exit press CTRL+C"

# Avviare consumer manualmente per test
docker-compose exec backend python manage.py consume_scan_status --verbosity=2
```

### 5. Test Comparativo Gateway vs Backend Diretto

#### Test Performance e Comportamento

```bash
# Test tempo di risposta Gateway
time curl -s http://vapter.szini.it:8080/api/orchestrator/customers/ > /dev/null

# Test tempo di risposta Backend diretto
time curl -s http://vapter.szini.it:8000/api/orchestrator/customers/ > /dev/null

# Test con header personalizzati (verificare X-Request-ID nel gateway)
curl -I http://vapter.szini.it:8080/api/orchestrator/customers/
```

#### Test Gestione Errori Gateway

```bash
# Test con endpoint inesistente
curl http://vapter.szini.it:8080/api/orchestrator/nonexistent/

# Test con dati invalidi
curl -X POST http://vapter.szini.it:8080/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{"invalid": "json"}'

# Verificare che il gateway gestisca correttamente gli errori
```

### 6. Test Filtri e Ricerca

```bash
# Test ricerca clienti (tramite Gateway)
curl "http://vapter.szini.it:8080/api/orchestrator/customers/?search=Test"

# Test filtri targets per cliente
curl "http://vapter.szini.it:8080/api/orchestrator/targets/?customer_name=Test"

# Test filtri scansioni per stato
curl "http://vapter.szini.it:8080/api/orchestrator/scans/?status=Queued"

# Test scansioni in corso
curl "http://vapter.szini.it:8080/api/orchestrator/scans/?is_running=true"

# Test ordinamento per data
curl "http://vapter.szini.it:8080/api/orchestrator/scans/?ordering=-initiated_at"

# Test paginazione
curl "http://vapter.szini.it:8080/api/orchestrator/scans/?page=1&page_size=5"
```

### 7. Test Validazioni

#### Test Validazioni Customer

```bash
# Test email duplicata (dovrebbe fallire)
curl -X POST http://vapter.szini.it:8080/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test 2", "email": "admin@testcorp.com"}'

# Output atteso: Errore 400 con messaggio di email duplicata
```

#### Test Validazioni Target

```bash
# Test indirizzo IP invalido (dovrebbe fallire)
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "{customer_id}",
    "name": "Invalid IP",
    "address": "999.999.999.999"
  }'

# Test indirizzo duplicato per stesso cliente (dovrebbe fallire)
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "{customer_id}",
    "name": "Duplicate",
    "address": "192.168.1.100"
  }'
```

### 8. Test Azioni Speciali

#### Test Statistiche

```bash
# Statistiche cliente (tramite Gateway)
curl http://vapter.szini.it:8080/api/orchestrator/customers/{customer_id}/statistics/

# Statistiche generali scansioni
curl http://vapter.szini.it:8080/api/orchestrator/scans/statistics/
```

#### Test Azioni Scansioni

```bash
# Test restart scansione (solo se stato è Failed o Completed)
curl -X POST http://vapter.szini.it:8080/api/orchestrator/scans/{scan_id}/restart/

# Test cancel scansione (solo se in corso)
curl -X POST http://vapter.szini.it:8080/api/orchestrator/scans/{scan_id}/cancel/
```

## 🔍 Test API Documentation

### API Gateway Documentation

1. Andare a: http://vapter.szini.it:8080/docs
2. Verificare che tutti gli endpoint dell'orchestrator siano documentati
3. Testare alcuni endpoint direttamente dall'interfaccia

### Backend Documentation

1. Andare a: http://vapter.szini.it:8000/api/schema/swagger-ui/
2. Verificare documentazione backend Django
3. Confrontare con quella del gateway

## 📊 Test di Performance

### Test Load Base

```bash
# Test carico con molte richieste tramite Gateway
for i in {1..10}; do
  curl -s http://vapter.szini.it:8080/api/orchestrator/customers/ > /dev/null &
done
wait

# Verificare tempi di risposta Gateway
time curl http://vapter.szini.it:8080/api/orchestrator/scans/

# Confrontare con accesso diretto backend
time curl http://vapter.szini.it:8000/api/orchestrator/scans/
```

### Test Concurrent Requests

```bash
# Test 50 richieste concorrenti tramite Gateway
seq 1 50 | xargs -n1 -P50 -I{} curl -s http://vapter.szini.it:8080/api/orchestrator/customers/ > /dev/null

# Verificare nei log del gateway che tutte le richieste siano state processate
docker-compose logs api_gateway | grep "GET.*customers" | wc -l
```

## 🐛 Troubleshooting

### Problemi Comuni

#### API Gateway non si avvia

```bash
# Verificare logs del gateway
docker-compose logs api_gateway

# Verificare configurazione
docker-compose exec api_gateway env | grep -E "(BACKEND_URL|DEBUG|LOG_LEVEL)"

# Riavviare gateway
docker-compose restart api_gateway
```

#### Gateway non comunica con Backend

```bash
# Test health check dettagliato
curl http://vapter.szini.it:8080/health/detailed

# Verificare connettività interna
docker-compose exec api_gateway curl http://backend:8000/api/orchestrator/customers/

# Verificare logs di entrambi i servizi
docker-compose logs backend api_gateway
```

#### Servizi non si avviano

```bash
# Verificare logs di tutti i servizi
docker-compose logs

# Verificare che database sia pronto
docker-compose exec db pg_isready -U vapter

# Test connessione da backend
docker-compose exec backend python manage.py dbshell
```

#### RabbitMQ connection errors

```bash
# Verificare RabbitMQ
docker-compose exec rabbitmq rabbitmqctl status

# Test connessione da backend
docker-compose exec backend python -c "
import pika
conn = pika.BlockingConnection(pika.URLParameters('amqp://vapter:vapter123@rabbitmq:5672/'))
print('RabbitMQ OK')
conn.close()
"
```

### Test Specifici per API Gateway

#### Test Timeout Gateway

```bash
# Simulare timeout (se backend è lento)
# Configurare BACKEND_TIMEOUT basso e fare richieste
curl http://vapter.szini.it:8080/api/orchestrator/scans/
```

#### Test Headers Personalizzati

```bash
# Verificare header X-Request-ID
curl -I http://vapter.szini.it:8080/api/orchestrator/customers/

# Verificare header X-Process-Time
curl -s -D - http://vapter.szini.it:8080/api/orchestrator/customers/ | grep "X-Process-Time"
```

### Reset Completo

Se qualcosa non funziona:

```bash
# ATTENZIONE: Cancella tutti i dati
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Rifare setup database
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py loaddata initial_data.json
```

### 9. Test Modulo Nmap Scanner

#### Verificare Modulo Nmap Scanner

```bash
# Verificare che il container nmap_scanner sia in esecuzione
docker-compose ps nmap_scanner

# Verificare logs del nmap scanner
docker-compose logs nmap_scanner

# Output atteso: "Nmap Scanner started, waiting for messages on nmap_scan_requests"

# Test dell'installazione nmap nel container
docker-compose exec nmap_scanner python3 test_nmap.py

# Test connettività RabbitMQ dal modulo nmap
docker-compose exec nmap_scanner python3 -c "
import pika
conn = pika.BlockingConnection(pika.URLParameters('amqp://vapter:vapter123@rabbitmq:5672/'))
print('RabbitMQ connection OK')
conn.close()
"
```

#### Test Workflow Completo di Scansione

```bash
# 1. Creare un cliente per il test
customer_response=$(curl -s -X POST http://vapter.szini.it:8080/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Nmap Customer", "email": "nmap@test.com"}')

customer_id=$(echo $customer_response | jq -r '.id')
echo "Created customer: $customer_id"

# 2. Creare un target di test (localhost per sicurezza)
target_response=$(curl -s -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d "{\"customer\": \"$customer_id\", \"name\": \"Test Localhost\", \"address\": \"127.0.0.1\"}")

target_id=$(echo $target_response | jq -r '.id')
echo "Created target: $target_id"

# 3. Avviare una scansione Discovery (la più sicura)
scan_response=$(curl -s -X POST http://vapter.szini.it:8080/api/orchestrator/targets/$target_id/scan/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type_id": 1}')

scan_id=$(echo $scan_response | jq -r '.id')
echo "Started scan: $scan_id"

# 4. Monitorare lo stato della scansione
echo "Monitoring scan progress..."
for i in {1..30}; do
  status=$(curl -s http://vapter.szini.it:8080/api/orchestrator/scans/$scan_id/ | jq -r '.status')
  echo "Scan $scan_id status: $status"
  
  if [[ "$status" == "Completed" || "$status" == "Failed" ]]; then
    break
  fi
  
  sleep 2
done

# 5. Verificare risultati della scansione
curl -s http://vapter.szini.it:8080/api/orchestrator/scans/$scan_id/ | jq '.parsed_nmap_results'
```

#### Test Avanzato con Scansione Porte

```bash
# Test scansione con porte (solo su localhost per sicurezza)
advanced_scan_response=$(curl -s -X POST http://vapter.szini.it:8080/api/orchestrator/targets/$target_id/scan/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type_id": 5}')  # Quick Scan

advanced_scan_id=$(echo $advanced_scan_response | jq -r '.id')
echo "Started advanced scan: $advanced_scan_id"

# Monitorare e verificare risultati
sleep 10
curl -s http://vapter.szini.it:8080/api/orchestrator/scans/$advanced_scan_id/ | jq '.status'
```

#### Test Error Handling

```bash
# Test con target invalido
invalid_target_response=$(curl -s -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d "{\"customer\": \"$customer_id\", \"name\": \"Invalid Target\", \"address\": \"999.999.999.999\"}")

# Il target invalido dovrebbe essere rifiutato dalla validazione
echo $invalid_target_response | jq '.address'
```

### 10. Test Code RabbitMQ con Nmap

#### Verificare Code RabbitMQ

```bash
# Verificare code tramite management UI
# Andare a http://vapter.szini.it:15672/
# Login: vapter/vapter123
# Verificare presenza code:
# - nmap_scan_requests
# - scan_status_updates

# Test manuale publishing su coda nmap
docker-compose exec backend python3 -c "
import json
import pika
from django.conf import settings

# Connect to RabbitMQ
conn = pika.BlockingConnection(pika.URLParameters('amqp://vapter:vapter123@rabbitmq:5672/'))
channel = conn.channel()

# Declare queues
channel.queue_declare(queue='nmap_scan_requests', durable=True)

# Test message
test_message = {
    'scan_id': 999,
    'scan_type_id': 1,
    'target_host': '127.0.0.1',
    'target_name': 'Test Manual',
    'customer_id': 'test-uuid',
    'timestamp': '2025-01-01T10:00:00Z'
}

# Publish test message
channel.basic_publish(
    exchange='',
    routing_key='nmap_scan_requests',
    body=json.dumps(test_message),
    properties=pika.BasicProperties(delivery_mode=2)
)

print('Test message published to nmap_scan_requests')
conn.close()
"

# Verificare che il nmap scanner processi il messaggio
docker-compose logs -f nmap_scanner
```

## ✅ Checklist Test Completo

- [X] Servizi Docker tutti avviati (incluso API Gateway e Nmap Scanner)
- [X] API Gateway health check OK
- [X] Gateway comunica correttamente con backend
- [X] Django Admin accessibile
- [X] Dati iniziali caricati (Port Lists e Scan Types)
- [X] API CRUD Customers funzionante tramite Gateway
- [X] API CRUD Targets funzionante tramite Gateway
- [X] API Scansioni funzionante tramite Gateway
- [X] Validazioni funzionanti
- [X] RabbitMQ accessibile e consumer attivo
- [X] Filtri e ricerca funzionanti tramite Gateway
- [X] Documentazione API Gateway accessibile
- [X] Logging Gateway funzionante
- [X] Test di performance base superati
- [X] Headers personalizzati del gateway presenti
- [X] Gestione errori del gateway corretta
- [ ] Modulo Nmap Scanner avviato e connesso a RabbitMQ
- [ ] Test nmap installation nel container
- [ ] Workflow completo di scansione funzionante
- [ ] Parsing risultati XML nmap corretto
- [ ] Aggiornamenti stato via RabbitMQ funzionanti
- [ ] Invio risultati all'API Gateway funzionante

## 🚀 Prossimi Passi

Una volta completata questa checklist:
1. L'API Gateway è pronto per l'integrazione con i moduli scanner
2. Il frontend potrà utilizzare il gateway come unico punto di accesso
3. Pronto per implementazione autenticazione
4. Pronto per aggiunta rate limiting se necessario

Il sistema è ora pronto per la fase successiva: implementazione del frontend React o dei moduli scanner.