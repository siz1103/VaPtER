## Comandi Utili (Sviluppo Locale)

### Comandi per setup iniziale

**Assumendo che si sia nella root del progetto.**

#### Setup Docker Environment

```bash
# Copiare e configurare le variabili d'ambiente
cp .env.example .env
# Editare il file .env con i valori desiderati

# Costruire tutti i container
docker-compose build

# Ricostruire un singolo container
docker-compose build backend
docker-compose build api_gateway

# Avviare tutti i servizi
docker-compose up -d

# Avviare solo alcuni servizi
docker-compose up -d db rabbitmq backend

# Riavviare un singolo container
docker-compose restart backend
docker-compose restart backend_consumer

# Visualizzare i log dei servizi
docker-compose logs -f
docker-compose logs -f backend
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
# Avviare il consumer manualmente (se non in esecuzione automatica)
docker-compose exec backend python manage.py consume_scan_status

# Avviare il consumer con parametri personalizzati
docker-compose exec backend python manage.py consume_scan_status --queue=scan_status_updates --prefetch=5

# Verificare le code RabbitMQ (accesso web)
# Andare a http://vapter.szini.it:15672
# Username: vapter, Password: vapter123
```

### Comandi di Sviluppo

#### Debugging e Sviluppo

```bash
# Accedere al container backend per debug
docker-compose exec backend bash

# Accedere alla shell Django
docker-compose exec backend python manage.py shell

# Eseguire shell Django con IPython
docker-compose exec backend python manage.py shell_plus

# Eseguire i test (quando saranno implementati)
docker-compose exec backend python manage.py test

# Verificare la configurazione Django
docker-compose exec backend python manage.py check

# Visualizzare le URL disponibili
docker-compose exec backend python manage.py show_urls
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
# Test API con curl
# Ottenere lista clienti
curl -X GET http://vapter.szini.it:8000/api/orchestrator/customers/

# Creare un nuovo cliente
curl -X POST http://vapter.szini.it:8000/api/orchestrator/customers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Customer", "email": "test@example.com"}'

# Ottenere lista scan types
curl -X GET http://vapter.szini.it:8000/api/orchestrator/scan-types/

# Ottenere lista port lists
curl -X GET http://vapter.szini.it:8000/api/orchestrator/port-lists/
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
```

#### Backup e Restore

```bash
# Backup del database PostgreSQL
docker-compose exec db pg_dump -U vapter vapter > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore del database PostgreSQL
docker-compose exec -T db psql -U vapter vapter < backup_file.sql

# Backup dei volumi Docker
docker run --rm -v vapter_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### URL di Accesso

#### Servizi Web

- **Backend API**: http://vapter.szini.it:8000/api/orchestrator/
- **Django Admin**: http://vapter.szini.it:8000/admin/
- **API Documentation**: http://vapter.szini.it:8000/api/schema/swagger-ui/
- **RabbitMQ Management**: http://vapter.szini.it:15672/ (vapter/vapter123)

#### API Endpoints Principali

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

# Riavviare tutti i servizi
docker-compose restart

# Verificare la connettività al database
docker-compose exec backend python manage.py dbshell

# Verificare la connessione a RabbitMQ
docker-compose exec backend python -c "import pika; pika.BlockingConnection(pika.URLParameters('amqp://vapter:vapter123@rabbitmq:5672/'))"

# Testare consumer RabbitMQ
docker-compose exec backend python manage.py consume_scan_status --verbosity=2
```

#### Reset Completo

```bash
# ATTENZIONE: Cancella tutti i dati e le immagini
docker-compose down -v
docker system prune -a
docker-compose build --no-cache
docker-compose up -d
```