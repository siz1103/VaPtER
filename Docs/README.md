# VaPtER
Tool di vulnerability assessment

# **README: Piattaforma di Vulnerability Assessment Basata su Docker**


## ** Obiettivo del Progetto**

Sviluppare una piattaforma di Vulnerability Assessment personalizzata, basata su Docker. L'obiettivo dell'app è eseguire  **scansione di host** (identificazione di porte, servizi, versioni software) e sulla **ricerca delle vulnerabilità note** associate a tali servizi.


## Note implementative

1. **Models**: Tutti i models hanno validazioni appropriate e relazioni corrette
2. **API**: Endpoint RESTful completi con filtri e paginazione
3. **RabbitMQ**: Consumer pronto per ricevere aggiornamenti dai moduli scanner
4. **Logging**: Sistema di logging configurato per debugging e monitoraggio
5. **Cache**: Supporto per Redis in produzione, memoria locale in sviluppo
6. **Sicurezza**: Configurazioni di sicurezza per ambiente di produzione (da implementare in una fase successiva)


## **Considerazioni Aggiuntive per lo Sviluppo**

- **Dockerizzazione:** Ogni componente deve essere containerizzato.

- **Comunicazione Asincrona:** Utilizza RabbitMQ per la comunicazione tra l'Orchestratore e i moduli scanner. 

- **Gestione Segreti:** Non hardcodare credenziali (API keys, password del database, credenziali di scansione) direttamente nel codice o nelle immagini Docker. Prevedi l'uso di variabili d'ambiente o strumenti dedicati come Docker Secrets (se usi Docker Swarm) o HashiCorp Vault per iniettarle in modo sicuro a runtime.

- **Error Handling:** Implementa una robusta gestione degli errori, specialmente per le chiamate API esterne (es. NVD API rate limits, JSON parsing errors).

- **Logging:** Assicurati che ogni servizio produca log significativi per il debugging e il monitoraggio.

- **Sicurezza dei Container:** Applica le best practice Docker: usa immagini base minimali e fidate, esegui i container con il principio del minimo privilegio (non-root user, --cap-drop all e --cap-add solo le necessarie), imposta filesystem di sola lettura (--read-only) e configura la rete per isolare i container (--network custom). 

- **Orchestrazione per la Produzione:** Per un ambiente di produzione, dove scalabilità orizzontale, resilienza e alta disponibilità sono critiche, un orchestratore di container come Kubernetes o Docker Swarm sarà essenziale. Pianifica la transizione da Docker Compose a uno di questi strumenti.


### URL di Accesso

#### Servizi Web

- **Frontend React**: http://vapter.szini.it:3000/
- **API Gateway**: http://vapter.szini.it:8080/
- **API Gateway Docs**: http://vapter.szini.it:8080/docs
- **API Gateway Health**: http://vapter.szini.it:8080/health/detailed
- **Backend API**: http://vapter.szini.it:8000/api/orchestrator/
- **Django Admin**: http://vapter.szini.it:8000/admin/
- **Backend API Documentation**: http://vapter.szini.it:8000/api/schema/swagger-ui/
- **RabbitMQ Management**: http://vapter.szini.it:15672/ (vapter/vapter123)


## Base URL

### Produzione (Accesso Principale)
- **Frontend React**: `http://vapter.szini.it:3000/`
- **API Gateway**: `http://vapter.szini.it:8080/api/orchestrator/`
- **Documentazione API**: `http://vapter.szini.it:8080/docs`

### Development (Accesso Diretto)
- **Backend Django**: `http://vapter.szini.it:8000/api/orchestrator/`
- **Django Admin**: `http://vapter.szini.it:8000/admin/`
- **API Schema Django**: `http://vapter.szini.it:8000/api/schema/swagger-ui/`

### Monitoring & Health
- **Gateway Health**: `http://vapter.szini.it:8080/health/`
- **Gateway Detailed Health**: `http://vapter.szini.it:8080/health/detailed`
- **RabbitMQ Management**: `http://vapter.szini.it:15672/`


# Miglioramenti alla gestione RabbitMQ in VaPtER

## Problemi risolti

### 1. **Connessioni che cadono durante operazioni lunghe**
- Le scansioni GCE possono durare oltre 50 minuti
- Le connessioni RabbitMQ venivano resettate con `ConnectionResetError`
- Mancava un meccanismo di heartbeat efficace

### 2. **Inconsistenza nel formato dei messaggi**
- Il backend consumer si aspettava `'module'` ma GCE scanner inviava `'plugin'`
- Questo causava errori di validazione dei messaggi

### 3. **Mancanza di reconnection automatica**
- Se una connessione cadeva, il servizio si fermava
- Non c'era retry logic per operazioni fallite

## Soluzioni implementate

### 1. **Classe RabbitMQConnection unificata**
Creata una classe robusta per gestire le connessioni con:
- **Heartbeat automatico**: mantiene viva la connessione
- **Reconnection automatica**: si riconnette in caso di disconnessione
- **Retry logic con exponential backoff**: riprova con delay crescenti
- **Thread safety**: gestione sicura in ambienti multi-thread
- **Connection pooling**: riutilizzo efficiente delle connessioni

### 2. **Configurazione RabbitMQ ottimizzata**
File `rabbitmq.conf` con:
- Heartbeat a 60 secondi
- TCP keepalive abilitato
- Consumer timeout disabilitato per operazioni lunghe
- Frame size aumentato a 128KB
- Message TTL di default a 1 ora

### 3. **Docker Compose aggiornato**
- Health checks per tutti i servizi
- Dipendenze con condition per startup ordinato
- Variabili d'ambiente per heartbeat e timeout
- Restart policy per resilienza

### 4. **Gestione messaggi migliorata**
- Supporto sia per `'module'` che `'plugin'` nel consumer
- Validazione messaggi con error handling
- Dead letter queue per messaggi non processabili
- Acknowledge esplicito solo dopo processing riuscito

## Come utilizzare

### 1. **Importare la classe comune**
```python
from common.rabbitmq_utils import RabbitMQConnection

# Creare una connessione
connection = RabbitMQConnection(
    host='rabbitmq',
    port=5672,
    queue_name='my_queue',
    heartbeat=60
)

# Connettere
if connection.connect():
    print("Connected successfully")
```

### 2. **Publisher pattern**
```python
# Pubblicare un messaggio
message = {
    'scan_id': 123,
    'module': 'nmap',
    'status': 'running'
}

success = connection.publish(message)
```

### 3. **Consumer pattern**
```python
def process_message(channel, method, properties, message):
    print(f"Received: {message}")
    # Process message here
    
# Avviare il consumer
connection.consume(process_message)
```

### 4. **Context manager**
```python
with RabbitMQConnection('rabbitmq', 5672, 'my_queue') as conn:
    conn.publish({'test': 'message'})
```

## Monitoraggio

### 1. **RabbitMQ Management UI**
Accedere a http://localhost:15672
- Username: vapter
- Password: vapter_password

### 2. **Log monitoring**
```bash
# Vedere i log di un servizio
docker-compose logs -f gce_scanner

# Vedere tutti i log
docker-compose logs -f
```

### 3. **Health checks**
```bash
# Verificare lo stato dei servizi
docker-compose ps

# Verificare la salute di RabbitMQ
docker exec vapter_rabbitmq rabbitmq-diagnostics ping
```

## Best practices

1. **Sempre usare heartbeat** per connessioni che potrebbero durare a lungo
2. **Implementare retry logic** per operazioni critiche
3. **Loggare eventi di connessione** per debugging
4. **Usare connection pooling** per applicazioni ad alto throughput
5. **Impostare TTL sui messaggi** per evitare accumulo
6. **Monitorare code e connessioni** tramite Management UI

## Troubleshooting

### Connessione rifiutata
```bash
# Verificare che RabbitMQ sia in esecuzione
docker-compose ps rabbitmq

# Verificare i log
docker-compose logs rabbitmq
```

### Messaggi persi
- Verificare che le code siano dichiarate come `durable`
- Verificare che i messaggi abbiano `delivery_mode=2`
- Controllare il TTL dei messaggi

### Performance issues
- Aumentare il `prefetch_count` per consumer veloci
- Usare batch publishing per alto volume
- Monitorare memory usage in Management UI

## Prossimi passi

1. **Implementare Dead Letter Exchange** per gestire messaggi falliti
2. **Aggiungere metriche Prometheus** per monitoring avanzato
3. **Implementare Circuit Breaker** per resilienza
4. **Aggiungere connection pooling** per scalabilità