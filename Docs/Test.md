# Docs/Test.md

# Test del Sistema

## 1. Test Backend

### Test dei Models
```bash
# Accedere alla shell Django
docker-compose exec backend python manage.py shell

# Test Customer
from orchestrator_api.models import Customer
customer = Customer.objects.create(
    name="Test Customer",
    email="test@example.com",
    company_name="Test Company"
)
print(customer.id, customer.name)

# Test PortList
from orchestrator_api.models import PortList
port_list = PortList.objects.get(name="Standard TCP Scan")
print(port_list.tcp_ports)

# Test Target
from orchestrator_api.models import Target
target = Target.objects.create(
    customer=customer,
    name="Test Server",
    address="192.168.1.100"
)
print(target.id, target.address)
```

### Test delle API

#### Test Customer API
```bash
# Creare un customer
curl -X POST http://vapter.szini.it:8080/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Customer",
    "email": "test@example.com",
    "company_name": "Test Inc",
    "contact_person": "John Doe"
  }'

# Ottenere lista customers
curl http://vapter.szini.it:8080/api/orchestrator/customers/

# Ottenere dettaglio customer (sostituire UUID)
curl http://vapter.szini.it:8080/api/orchestrator/customers/{customer-id}/
```

#### Test Target API
```bash
# Creare un target
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "{customer-id}",
    "name": "Web Server",
    "address": "192.168.1.100",
    "description": "Primary web server"
  }'

# Test validazione IP
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "{customer-id}",
    "name": "Invalid IP",
    "address": "999.999.999.999"
  }'
# Dovrebbe restituire errore di validazione

# Test validazione FQDN
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "{customer-id}",
    "name": "Domain Server",
    "address": "example.com"
  }'
```

#### Test Scan API
```bash
# Avviare una scansione
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/{target-id}/scan/ \
  -H "Content-Type: application/json" \
  -d '{
    "scan_type_id": 1
  }'

# Test scansioni multiple sullo stesso target
# Avviare prima scansione
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/{target-id}/scan/ \
  -H "Content-Type: application/json" \
  -d '{
    "scan_type_id": 1
  }'

# Avviare seconda scansione (dovrebbe funzionare senza errori)
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/{target-id}/scan/ \
  -H "Content-Type: application/json" \
  -d '{
    "scan_type_id": 2
  }'

# Verificare che entrambe le scansioni siano presenti
curl http://vapter.szini.it:8080/api/orchestrator/targets/{target-id}/scans/

# Monitorare lo stato di una scansione
curl http://vapter.szini.it:8080/api/orchestrator/scans/{scan-id}/

# Riavviare una scansione completata o fallita
curl -X POST http://vapter.szini.it:8080/api/orchestrator/scans/{scan-id}/restart/
```

### Test RabbitMQ

```bash
# Verificare che RabbitMQ sia attivo
docker-compose exec backend python -c "
import pika
connection = pika.BlockingConnection(pika.URLParameters('amqp://vapter:vapter123@rabbitmq:5672/'))
print('RabbitMQ connection successful')
connection.close()
"

# Verificare le code
docker-compose exec rabbitmq rabbitmqctl list_queues

# Pubblicare un messaggio di test
docker-compose exec backend python -c "
from orchestrator_api.services import RabbitMQService
service = RabbitMQService()
service.connect()
success = service.publish_message('nmap_scan_requests', {'test': 'message'})
print(f'Message published: {success}')
service.close()
"
```

### Test Consumer

```bash
# Avviare il consumer in modalità verbosa
docker-compose exec backend python manage.py consume_scan_status --verbosity=2

# In un'altra finestra, inviare un messaggio di test
docker-compose exec backend python -c "
import json
from orchestrator_api.services import RabbitMQService
service = RabbitMQService()
service.connect()
message = {
    'scan_id': 1,
    'module': 'nmap',
    'status': 'completed',
    'message': 'Test completed'
}
service.publish_message('scan_status_updates', message)
service.close()
"
```

## 2. Test Scanner Nmap

```bash
# Test dello scanner Nmap
docker-compose exec nmap_scanner python test_nmap.py

# Test manuale di nmap
docker-compose exec nmap_scanner nmap -sn 192.168.1.1

# Verificare i log dello scanner
docker-compose logs -f nmap_scanner
```

## 3. Test Frontend

```bash
# Verificare che il frontend sia accessibile
curl http://vapter.szini.it:3000/

# Verificare la build TypeScript
docker-compose exec frontend npm run build

# Verificare i log del frontend
docker-compose logs -f frontend

# Test del proxy API dal frontend
docker-compose exec frontend wget -O- http://api_gateway:8080/api/orchestrator/customers/
```

## 4. Test End-to-End

### Workflow Completo di Scansione

1. **Creare un customer**
```bash
CUSTOMER_ID=$(curl -s -X POST http://vapter.szini.it:8080/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "E2E Test", "email": "e2e@test.com"}' | jq -r '.id')
echo "Customer ID: $CUSTOMER_ID"
```

2. **Creare un target**
```bash
TARGET_ID=$(curl -s -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d "{\"customer\": \"$CUSTOMER_ID\", \"name\": \"Test Target\", \"address\": \"127.0.0.1\"}" | jq -r '.id')
echo "Target ID: $TARGET_ID"
```

3. **Avviare una scansione**
```bash
SCAN_ID=$(curl -s -X POST http://vapter.szini.it:8080/api/orchestrator/targets/$TARGET_ID/scan/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type_id": 1}' | jq -r '.id')
echo "Scan ID: $SCAN_ID"
```

4. **Monitorare lo stato**
```bash
# Loop per monitorare lo stato
while true; do
  STATUS=$(curl -s http://vapter.szini.it:8080/api/orchestrator/scans/$SCAN_ID/ | jq -r '.status')
  echo "Status: $STATUS"
  if [[ "$STATUS" == "Completed" ]] || [[ "$STATUS" == "Failed" ]]; then
    break
  fi
  sleep 5
done
```

5. **Test scansioni multiple**
```bash
# Avviare una seconda scansione sullo stesso target
SCAN2_ID=$(curl -s -X POST http://vapter.szini.it:8080/api/orchestrator/targets/$TARGET_ID/scan/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type_id": 2}' | jq -r '.id')
echo "Second Scan ID: $SCAN2_ID"

# Verificare che entrambe le scansioni esistano
curl -s http://vapter.szini.it:8080/api/orchestrator/targets/$TARGET_ID/scans/ | jq '.[] | {id, status, scan_type_name}'
```

## 5. Test di Performance

```bash
# Test carico API
ab -n 1000 -c 10 http://vapter.szini.it:8080/api/orchestrator/customers/

# Test carico con POST
ab -n 100 -c 5 -p test_data.json -T application/json http://vapter.szini.it:8080/api/orchestrator/targets/

# Monitor risorse durante i test
docker stats
```

## 6. Test di Sicurezza (Base)

```bash
# Test SQL Injection (dovrebbe fallire)
curl -X GET "http://vapter.szini.it:8080/api/orchestrator/customers/?search=';DROP TABLE customers;--"

# Test XSS (dovrebbe essere sanitizzato)
curl -X POST http://vapter.szini.it:8080/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "<script>alert(1)</script>", "email": "xss@test.com"}'

# Test autenticazione (quando implementata)
# curl -X GET http://vapter.szini.it:8080/api/orchestrator/customers/ \
#   -H "Authorization: Bearer invalid-token"
```

## 7. Verifica Logs

```bash
# Tutti i log
docker-compose logs

# Log specifici con follow
docker-compose logs -f backend
docker-compose logs -f api_gateway
docker-compose logs -f nmap_scanner

# Filtrare per errori
docker-compose logs | grep -i error

# Log delle ultime 2 ore
docker-compose logs --since 2h
```

## 8. Troubleshooting Test

### Database Issues
```bash
# Reset database di test
docker-compose exec backend python manage.py flush --no-input
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py loaddata initial_data.json
```

### RabbitMQ Issues
```bash
# Reset code RabbitMQ
docker-compose exec rabbitmq rabbitmqctl stop_app
docker-compose exec rabbitmq rabbitmqctl reset
docker-compose exec rabbitmq rabbitmqctl start_app
```

### Container Issues
```bash
# Ricreare un container specifico
docker-compose stop backend
docker-compose rm -f backend
docker-compose up -d backend

# Rebuild completo
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Test Checklist

- [ ] Backend API risponde correttamente
- [ ] Customer CRUD funzionante
- [ ] Target validation (IP/FQDN) funzionante
- [ ] Scan creation funzionante
- [ ] Multiple scans sullo stesso target funzionanti
- [ ] RabbitMQ connection funzionante
- [ ] Nmap scanner riceve messaggi
- [ ] Status updates processati correttamente
- [ ] Frontend carica correttamente
- [ ] API Gateway proxy funzionante
- [ ] Logs senza errori critici
- [ ] Scan completa con successo (stato "Completed")

## Note Importanti

1. **Plugin Non Implementati**: I test per fingerprint, enum, web e vuln lookup sono placeholder
2. **Scansioni Multiple**: Ora è possibile eseguire più scansioni sullo stesso target senza errori
3. **Completamento Scan**: Le scansioni vengono marcate come "Completed" dopo nmap, indipendentemente dai plugin abilitati
4. **Autenticazione**: Non ancora implementata, tutti gli endpoint sono pubblici