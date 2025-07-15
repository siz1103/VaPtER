# 🚀 Guida Setup VaPtER - Test Completo

Questa guida ti aiuterà a configurare e testare i vari componenti implementati.

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
# Build e avvio di tutti i servizi
docker-compose build
docker-compose up -d

# Verificare che tutti i servizi siano attivi
docker-compose ps
```

**Output atteso:**
```
Name                   Command                  State           Ports
------------------------------------------------------------------------
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

### 1. Test Database e Django

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
# Verificare Port Lists caricate
curl http://vapter.szini.it:8000/api/orchestrator/port-lists/

# Verificare Scan Types caricati
curl http://vapter.szini.it:8000/api/orchestrator/scan-types/
```

**Output atteso:** Liste con 5 Port Lists e 6 Scan Types predefiniti.

### 2. Test API REST

#### Test CRUD Completo - Customers

```bash
# 1. Creare un cliente
curl -X POST http://vapter.szini.it:8000/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Corporation",
    "company_name": "Test Corp Ltd",
    "email": "admin@testcorp.com",
    "phone": "+1234567890",
    "contact_person": "John Doe"
  }'

# 2. Ottenere lista clienti
curl http://vapter.szini.it:8000/api/orchestrator/customers/

# 3. Ottenere cliente specifico (sostituire {id} con UUID restituito)
curl http://vapter.szini.it:8000/api/orchestrator/customers/{customer_id}/

# 4. Aggiornare cliente
curl -X PATCH http://vapter.szini.it:8000/api/orchestrator/customers/{customer_id}/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+9876543210"}'
```

#### Test CRUD Completo - Targets

```bash
# 1. Creare un target (sostituire {customer_id})
curl -X POST http://vapter.szini.it:8000/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "{customer_id}",
    "name": "Web Server Test",
    "address": "192.168.1.100",
    "description": "Server web di test"
  }'

# 2. Creare secondo target con FQDN
curl -X POST http://vapter.szini.it:8000/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "{customer_id}",
    "name": "DNS Server",
    "address": "google.com",
    "description": "Server DNS pubblico"
  }'

# 3. Ottenere lista targets
curl http://vapter.szini.it:8000/api/orchestrator/targets/

# 4. Ottenere targets di un cliente specifico
curl http://vapter.szini.it:8000/api/orchestrator/customers/{customer_id}/targets/
```

#### Test Creazione Scansioni

```bash
# 1. Ottenere lista scan types disponibili
curl http://vapter.szini.it:8000/api/orchestrator/scan-types/

# 2. Avviare scansione Discovery (sostituire {target_id})
curl -X POST http://vapter.szini.it:8000/api/orchestrator/targets/{target_id}/scan/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type_id": 1}'

# 3. Avviare scansione completa
curl -X POST http://vapter.szini.it:8000/api/orchestrator/targets/{target_id}/scan/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type_id": 3}'

# 4. Verificare lista scansioni
curl http://vapter.szini.it:8000/api/orchestrator/scans/

# 5. Ottenere dettagli scansione specifica
curl http://vapter.szini.it:8000/api/orchestrator/scans/{scan_id}/
```

### 3. Test RabbitMQ

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

### 4. Test Filtri e Ricerca

```bash
# Test ricerca clienti
curl "http://vapter.szini.it:8000/api/orchestrator/customers/?search=Test"

# Test filtri targets per cliente
curl "http://vapter.szini.it:8000/api/orchestrator/targets/?customer_name=Test"

# Test filtri scansioni per stato
curl "http://vapter.szini.it:8000/api/orchestrator/scans/?status=Queued"

# Test scansioni in corso
curl "http://vapter.szini.it:8000/api/orchestrator/scans/?is_running=true"

# Test ordinamento per data
curl "http://vapter.szini.it:8000/api/orchestrator/scans/?ordering=-initiated_at"

# Test paginazione
curl "http://vapter.szini.it:8000/api/orchestrator/scans/?page=1&page_size=5"
```

### 5. Test Validazioni

#### Test Validazioni Customer

```bash
# Test email duplicata (dovrebbe fallire)
curl -X POST http://vapter.szini.it:8000/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test 2", "email": "admin@testcorp.com"}'

# Output atteso: Errore 400 con messaggio di email duplicata
```

#### Test Validazioni Target

```bash
# Test indirizzo IP invalido (dovrebbe fallire)
curl -X POST http://vapter.szini.it:8000/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "{customer_id}",
    "name": "Invalid IP",
    "address": "999.999.999.999"
  }'

# Test indirizzo duplicato per stesso cliente (dovrebbe fallire)
curl -X POST http://vapter.szini.it:8000/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "{customer_id}",
    "name": "Duplicate",
    "address": "192.168.1.100"
  }'
```

### 6. Test Azioni Speciali

#### Test Statistiche

```bash
# Statistiche cliente
curl http://vapter.szini.it:8000/api/orchestrator/customers/{customer_id}/statistics/

# Statistiche generali scansioni
curl http://vapter.szini.it:8000/api/orchestrator/scans/statistics/
```

#### Test Azioni Scansioni

```bash
# Test restart scansione (solo se stato è Failed o Completed)
curl -X POST http://vapter.szini.it:8000/api/orchestrator/scans/{scan_id}/restart/

# Test cancel scansione (solo se in corso)
curl -X POST http://vapter.szini.it:8000/api/orchestrator/scans/{scan_id}/cancel/
```

## 🔍 Test API Documentation

### Swagger UI

1. Andare a: http://vapter.szini.it:8000/api/schema/swagger-ui/
2. Verificare che tutti gli endpoint siano documentati
3. Testare alcuni endpoint direttamente dall'interfaccia

### ReDoc

1. Andare a: http://vapter.szini.it:8000/api/schema/redoc/
2. Verificare documentazione alternativa

## 📊 Test di Performance (Base)

```bash
# Test carico con molte richieste
for i in {1..10}; do
  curl -s http://vapter.szini.it:8000/api/orchestrator/customers/ > /dev/null &
done
wait

# Verificare tempi di risposta
time curl http://vapter.szini.it:8000/api/orchestrator/scans/
```

## 🐛 Troubleshooting

### Problemi Comuni

#### Servizi non si avviano

```bash
# Verificare logs
docker-compose logs backend
docker-compose logs db
docker-compose logs rabbitmq

# Riavviare servizi
docker-compose restart
```

#### Database connection errors

```bash
# Verificare che PostgreSQL sia avviato
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

## ✅ Checklist Test Completo

- [X] Servizi Docker tutti avviati
- [X] Django Admin accessibile
- [X] Dati iniziali caricati (Port Lists e Scan Types)
- [X] API CRUD Customers funzionante
- [X] API CRUD Targets funzionante
- [X] API Scansioni funzionante
- [X] Validazioni funzionanti
- [X] RabbitMQ accessibile e consumer attivo
- [X] Filtri e ricerca funzionanti
- [X] Documentazione API accessibile
- [X] Test di performance base superati

Una volta completata questa checklist, il backend è pronto per l'integrazione con l'API Gateway e i moduli scanner.