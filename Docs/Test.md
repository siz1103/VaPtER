# 🚀 Guida Setup VaPtER - Test Completo con Settings Pages

Questa guida ti aiuterà a configurare e testare i vari componenti implementati, incluse le nuove pagine Settings per Port Lists e Scan Types.

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
vapter_frontend        npm run dev            Up             0.0.0.0:3000->3000/tcp
vapter_nmap_scanner    python3 nmap_scanner.py Up
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

### 0. Test Frontend React Completo

#### Verificare Frontend Status

```bash
# Verificare che il container frontend sia attivo
docker-compose ps frontend

# Verificare logs del frontend
docker-compose logs frontend

# Test accesso al frontend
curl -I http://vapter.szini.it:3000/

# Aprire il browser e navigare a
# http://vapter.szini.it:3000/
```

**Verifiche da fare nel browser:**
1. ✅ La pagina si carica correttamente con tema dark
2. ✅ Il layout mostra header e sidebar
3. ✅ Il dropdown dei customer è visibile nell'header
4. ✅ La navigazione tra le pagine funziona
5. ✅ I modali si aprono correttamente

#### Test Nuove Pagine Settings

**1. Test Port Lists Page:**
```bash
# Navigare a http://vapter.szini.it:3000/settings/port-lists
```

**Verifiche da fare:**
- ✅ Pagina carica con tabella port lists esistenti
- ✅ Bottone "Create Port List" funziona
- ✅ Modal di creazione si apre correttamente
- ✅ Validazione porte TCP/UDP funziona in real-time
- ✅ Conteggio porte viene mostrato durante input
- ✅ Ricerca dinamica filtra risultati
- ✅ Dropdown azioni (Edit/Delete) funziona
- ✅ Modal di conferma cancellazione si apre
- ✅ Form di modifica precompila dati esistenti

**Test Cases Port Lists:**
```bash
# Test formato porte validi:
# - Porte singole: "22,80,443"
# - Range: "1-1000"
# - Combinazione: "22,80,443,1000-2000"
# - TCP+UDP: TCP="80,443" UDP="53,123"

# Test formato porte invalidi:
# - Porte fuori range: "70000"
# - Range invalido: "1000-500"
# - Caratteri non numerici: "abc,80"
```

**2. Test Scan Types Page:**
```bash
# Navigare a http://vapter.szini.it:3000/settings/scan-types
```

**Verifiche da fare:**
- ✅ Pagina carica con tabella scan types esistenti
- ✅ Badge per Discovery/Port Scan visibili
- ✅ Plugin badges mostrano configurazione
- ✅ Bottone "Create Scan Type" funziona
- ✅ Modal complesso si apre correttamente
- ✅ Switch "Discovery Only" disabilita port list e plugin
- ✅ Dropdown Port List carica opzioni dinamicamente
- ✅ Plugin switches funzionano indipendentemente
- ✅ Summary mostra configurazione in tempo reale
- ✅ Validation impedisce Discovery + Port List

**Test Cases Scan Types:**
```bash
# Test Discovery Scan:
# - only_discovery = true
# - port_list deve essere disabilitato
# - tutti i plugin devono essere disabilitati

# Test Port Scan:
# - only_discovery = false
# - port_list selezionabile
# - plugin configurabili liberamente

# Test logica UI:
# - Cambio Discovery Only resetta altri campi
# - Summary mostra preview configurazione
```

#### Test Proxy API dal Frontend

```bash
# Verificare che il frontend possa comunicare con l'API Gateway
docker-compose exec frontend wget -qO- http://api_gateway:8080/health/

# Verificare nei Developer Tools del browser (F12)
# - Network tab: le chiamate API vanno a /api/...
# - Console: nessun errore CORS
```

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

#### Verificare Documentazione API Gateway

1. Andare a: http://vapter.szini.it:8080/docs
2. Verificare che la documentazione FastAPI sia accessibile
3. Testare alcuni endpoint direttamente dall'interfaccia Swagger

### 2. Test Database e Django

#### Verificare Django Admin

1. Andare a: http://vapter.szini.it:8000/admin/
2. Login con le credenziali del superuser
3. Verificare che siano visibili tutte le sezioni:
   - Customers
   - Port Lists ✅ NUOVO
   - Scan Types ✅ NUOVO
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

### 3. Test API REST Nuove - Settings

#### Test CRUD Completo - Port Lists

```bash
# 1. Ottenere lista port lists
curl http://vapter.szini.it:8080/api/orchestrator/port-lists/

# 2. Creare una nuova port list
curl -X POST http://vapter.szini.it:8080/api/orchestrator/port-lists/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Web Ports",
    "tcp_ports": "80,443,8080,8443",
    "udp_ports": "53,123",
    "description": "Porte per test web applications"
  }'

# 3. Ottenere port list specifica (sostituire {id})
curl http://vapter.szini.it:8080/api/orchestrator/port-lists/{id}/

# 4. Aggiornare port list
curl -X PATCH http://vapter.szini.it:8080/api/orchestrator/port-lists/{id}/ \
  -H "Content-Type: application/json" \
  -d '{"description": "Descrizione aggiornata"}'

# 5. Test validazione porte (dovrebbe fallire)
curl -X POST http://vapter.szini.it:8080/api/orchestrator/port-lists/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invalid Ports",
    "tcp_ports": "70000,abc,1000-500",
    "description": "Test porte invalide"
  }'

# 6. Eliminare port list
curl -X DELETE http://vapter.szini.it:8080/api/orchestrator/port-lists/{id}/
```

#### Test CRUD Completo - Scan Types

```bash
# 1. Ottenere lista scan types
curl http://vapter.szini.it:8080/api/orchestrator/scan-types/

# 2. Creare scan type discovery
curl -X POST http://vapter.szini.it:8080/api/orchestrator/scan-types/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Discovery",
    "only_discovery": true,
    "be_quiet": true,
    "description": "Test scan discovery only"
  }'

# 3. Creare scan type completo con plugin
curl -X POST http://vapter.szini.it:8080/api/orchestrator/scan-types/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Complete Scan",
    "only_discovery": false,
    "port_list": 1,
    "plugin_finger": true,
    "plugin_vuln_lookup": true,
    "description": "Test scan completo"
  }'

# 4. Test validazione (dovrebbe fallire - discovery con port list)
curl -X POST http://vapter.szini.it:8080/api/orchestrator/scan-types/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invalid Discovery",
    "only_discovery": true,
    "port_list": 1,
    "plugin_finger": true
  }'

# 5. Filtri avanzati scan types
curl "http://vapter.szini.it:8080/api/orchestrator/scan-types/?with_finger=true"
curl "http://vapter.szini.it:8080/api/orchestrator/scan-types/?with_web=true"
```

### 4. Test Filtri e Ricerca Avanzata

#### Test Port Lists

```bash
# Test ricerca per nome
curl "http://vapter.szini.it:8080/api/orchestrator/port-lists/?search=TCP"

# Test ricerca per porte
curl "http://vapter.szini.it:8080/api/orchestrator/port-lists/?search=80"

# Test ricerca per descrizione
curl "http://vapter.szini.it:8080/api/orchestrator/port-lists/?search=common"
```

#### Test Scan Types

```bash
# Test ricerca per nome
curl "http://vapter.szini.it:8080/api/orchestrator/scan-types/?search=Discovery"

# Test filtri plugin
curl "http://vapter.szini.it:8080/api/orchestrator/scan-types/?with_finger=true&with_enum=true"

# Test combinazioni
curl "http://vapter.szini.it:8080/api/orchestrator/scan-types/?search=Complete&with_vuln=true"
```

### 5. Test Validazioni e Error Handling

#### Test Validazioni Port Lists

```bash
# Test nome duplicato (dovrebbe fallire)
curl -X POST http://vapter.szini.it:8080/api/orchestrator/port-lists/ \
  -H "Content-Type: application/json" \
  -d '{"name": "All IANA assigned TCP", "tcp_ports": "80,443"}'

# Test senza porte (dovrebbe fallire)
curl -X POST http://vapter.szini.it:8080/api/orchestrator/port-lists/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Empty Ports", "description": "No ports specified"}'

# Test formato porte invalido
curl -X POST http://vapter.szini.it:8080/api/orchestrator/port-lists/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Bad Format", "tcp_ports": "22;80;443"}'
```

#### Test Validazioni Scan Types

```bash
# Test nome duplicato
curl -X POST http://vapter.szini.it:8080/api/orchestrator/scan-types/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Discovery", "only_discovery": true}'

# Test port list inesistente
curl -X POST http://vapter.szini.it:8080/api/orchestrator/scan-types/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Invalid Port List", "port_list": 999}'
```

### 6. Test Dipendenze e Cancellazioni

#### Test Cancellazione Port List in Uso

```bash
# 1. Verificare scan types che usano port list 1
curl "http://vapter.szini.it:8080/api/orchestrator/scan-types/?port_list=1"

# 2. Tentare cancellazione port list usata (dovrebbe fallire)
curl -X DELETE http://vapter.szini.it:8080/api/orchestrator/port-lists/1/

# Output atteso: Errore 400 con messaggio di dipendenza
```

#### Test Cancellazione Scan Type in Uso

```bash
# Dopo aver creato scansioni con un scan type
# Tentare cancellazione scan type usato (dovrebbe fallire)
curl -X DELETE http://vapter.szini.it:8080/api/orchestrator/scan-types/1/
```

### 7. Test Frontend Integration E2E

#### Test Workflow Completo Frontend

1. **Aprire http://vapter.szini.it:3000/**
2. **Selezionare/Creare Customer** dal dropdown header
3. **Navigare a Settings → Port Lists**
4. **Creare nuova Port List:**
   - Nome: "Test E2E Ports"
   - TCP: "80,443,8080-8090"
   - UDP: "53,123"
   - Descrizione: "Test end-to-end"
5. **Verificare validazione in tempo reale** durante input
6. **Salvare e verificare** in tabella
7. **Navigare a Settings → Scan Types**
8. **Creare nuovo Scan Type:**
   - Nome: "Test E2E Scan"
   - Port List: Selezionare quella creata
   - Plugins: Abilitare Fingerprinting e Vuln Lookup
9. **Verificare preview configurazione**
10. **Salvare e verificare** in tabella
11. **Test ricerca dinamica** in entrambe le pagine
12. **Test modifica** di entrambe le entità
13. **Test cancellazione** (con conferma)

#### Test Error Handling Frontend

```bash
# 1. Spegnere backend temporaneamente
docker-compose stop backend

# 2. Tentare operazioni nel frontend
# Verificare che vengano mostrati toast di errore appropriati

# 3. Riavviare backend
docker-compose start backend

# 4. Verificare che le operazioni tornino a funzionare
```

### 8. Test RabbitMQ e Consumer

```bash
# Verificare che il consumer sia in esecuzione
docker-compose logs backend_consumer

# Verificare code RabbitMQ
# Andare a http://vapter.szini.it:15672/
# Login: vapter/vapter123
# Verificare presenza code con messaggi processati
```

### 9. Test Performance e UI/UX

#### Test Performance Frontend

```bash
# Nel browser, aprire DevTools (F12)
# Andare al tab Network
# Navigare tra le pagine Settings
# Verificare:
# - Tempi di caricamento < 500ms
# - Nessun errore CORS
# - API calls efficienti (no N+1 queries)
# - Caching TanStack Query funzionante
```

#### Test Responsiveness

```bash
# Testare su diverse dimensioni schermo:
# - Desktop (1920x1080)
# - Tablet (768x1024)
# - Mobile (375x667)

# Verificare:
# - Tabelle responsive
# - Modal si adattano allo schermo
# - Sidebar collassa su mobile
# - Form rimangono usabili
```

### 10. Test Accessibility

```bash
# Nel browser:
# 1. Utilizzare solo la tastiera per navigare
# 2. Verificare focus management nei modal
# 3. Testare screen reader compatibility
# 4. Verificare contrasti colori (tema dark)
# 5. Testare con browser zoom al 200%
```

#### Test Customer Selection
```bash
# 1. Aprire http://vapter.szini.it:3000/targets senza customer selezionato
# Verificare messaggio che invita a selezionare customer

# 2. Selezionare un customer dal dropdown
# Verificare che la pagina si carichi con i targets del customer
```

# 1. Test creazione target
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "customer-uuid",
    "name": "Web Server Test",
    "address": "192.168.1.100",
    "description": "Test server"
  }'

# 2. Test validazione indirizzo (dovrebbe fallire)
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "customer-uuid",
    "name": "Invalid Target",
    "address": "invalid.address.300",
    "description": "Should fail"
  }'

# 3. Test avvio scansione da target
curl -X POST http://vapter.szini.it:8080/api/orchestrator/targets/1/scan/ \
  -H "Content-Type: application/json" \
  -d '{"scan_type_id": 2}'

## ✅ Checklist Test Completo Aggiornata

### Frontend Base
- [X] Frontend React avviato e accessibile
- [X] Layout con tema dark funzionante
- [X] Navigazione tra pagine funzionante
- [X] Comunicazione Frontend → API Gateway funzionante
- [X] Customer dropdown e gestione funzionante

### Nuove Pagine Settings
- [ ] **Port Lists Page completa e funzionante**
  - [ ] Tabella con dati caricati correttamente
  - [ ] Ricerca dinamica funzionante
  - [ ] Modal creazione/modifica apertura
  - [ ] Validazione porte in tempo reale
  - [ ] Conteggio porte automatico
  - [ ] CRUD operations complete
  - [ ] Error handling appropriato
  - [ ] Conferma cancellazione
- [ ] **Scan Types Page completa e funzionante**
  - [ ] Tabella con badges e configurazioni
  - [ ] Modal complesso con tutti i controlli
  - [ ] Logica Discovery Only funzionante
  - [ ] Integration con Port Lists
  - [ ] Plugin configuration switches
  - [ ] Preview configurazione in tempo reale
  - [ ] CRUD operations complete
  - [ ] Validazioni appropriate

### API e Backend
- [X] Servizi Docker tutti avviati
- [X] API Gateway health check OK
- [X] Django Admin accessibile
- [X] Dati iniziali caricati
- [ ] **API Port Lists funzionanti tramite Gateway**
  - [ ] GET lista port lists
  - [ ] POST creazione con validazione
  - [ ] PATCH/PUT aggiornamento
  - [ ] DELETE con controllo dipendenze
  - [ ] Filtri e ricerca API
- [ ] **API Scan Types funzionanti tramite Gateway**
  - [ ] GET lista scan types
  - [ ] POST creazione con validazione
  - [ ] Integration con Port Lists
  - [ ] Plugin filters API
  - [ ] DELETE con controllo dipendenze

### Integration e E2E
- [ ] **Workflow completo Port Lists**
  - [ ] Creazione → Visualizzazione → Modifica → Cancellazione
  - [ ] Validazione formati porte complessi
  - [ ] Error handling per dipendenze
- [ ] **Workflow completo Scan Types**
  - [ ] Creazione → Configuration → Preview → Save
  - [ ] Discovery vs Port Scan logic
  - [ ] Plugin configuration
- [ ] **Performance frontend accettabile**
  - [ ] Caricamento pagine < 500ms
  - [ ] TanStack Query caching funzionante
  - [ ] UI responsive su tutti i dispositivi
- [ ] **Error handling robusto**
  - [ ] Toast notifications appropriate
  - [ ] Fallback per errori API
  - [ ] Loading states consistenti

### Sistema Completo
- [X] RabbitMQ accessibile e consumer attivo
- [X] Modulo Nmap Scanner funzionante
- [X] Logging Gateway funzionante
- [X] Headers personalizzati del gateway presenti
- [X] Gestione errori del gateway corretta

## 🚀 Prossimi Passi

Una volta completata questa checklist:
1. ✅ Le pagine Settings sono complete e pronte per l'uso
2. ✅ Il sistema di configurazione è operativo
3. 🔄 Pronti per implementare Target e Scan management
4. 🔄 Fondamenta pronte per polling e real-time updates
5. 🔄 Pattern stabiliti per future pagine CRUD

Il sistema di configurazione è ora completo e pronto per la gestione operativa delle scansioni!