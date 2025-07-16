## Struttura delle Directory Aggiornata

```
vapt_project_root/
├── backend/                         # Django Backend Orchestrator
│   ├── vapter_backend/              # Django project settings
│   │   ├── __init__.py
│   │   ├── settings.py              # Django configuration
│   │   ├── urls.py                  # Main URL routing
│   │   └── wsgi.py                  # WSGI application
│   ├── orchestrator_api/            # Main Django app
│   │   ├── management/              # Django management commands
│   │   │   ├── __init__.py
│   │   │   └── commands/
│   │   │       ├── __init__.py
│   │   │       └── consume_scan_status.py  # RabbitMQ consumer command
│   │   ├── fixtures/                # Initial data
│   │   │   └── initial_data.json    # PortList and ScanType fixtures
│   │   ├── __init__.py
│   │   ├── admin.py                 # Django admin configuration
│   │   ├── apps.py                  # App configuration
│   │   ├── filters.py               # DRF filters
│   │   ├── models.py                # Database models
│   │   ├── serializers.py           # DRF serializers
│   │   ├── services.py              # Business logic and RabbitMQ services
│   │   ├── urls.py                  # API URL routing
│   │   └── views.py                 # API views
│   ├── __init__.py
│   ├── Dockerfile                   # Docker configuration for backend
│   ├── requirements.txt             # Python dependencies
│   └── manage.py                    # Django management script
├── api_gateway/                     # ✅ IMPLEMENTATO - FastAPI Gateway
│   ├── app/                         # FastAPI application
│   │   ├── __init__.py             # Package initialization
│   │   ├── main.py                 # FastAPI main application
│   │   ├── config.py               # Configuration settings
│   │   ├── routes/                 # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── health.py           # Health check endpoints
│   │   │   └── orchestrator.py     # Proxy routes to backend
│   │   ├── services/               # Service layer
│   │   │   ├── __init__.py
│   │   │   └── backend_client.py   # HTTP client for backend communication
│   │   └── middleware/             # Custom middleware
│   │       ├── __init__.py
│   │       └── logging.py          # Request logging middleware
│   ├── Dockerfile                  # Docker configuration for API Gateway
│   └── requirements.txt            # Python dependencies
├── frontend/                        # ✅ IN IMPLEMENTAZIONE - React + shadcn/ui
│   ├── src/                         # Source code
│   │   ├── components/              # React components
│   │   │   ├── layout/              # Layout components
│   │   │   └── ui/                  # shadcn/ui components
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── lib/                     # Utilities and helpers
│   │   │   ├── api.ts               # API client configuration
│   │   │   └── utils.ts             # Utility functions
│   │   ├── pages/                   # Page components
│   │   │   └── settings/            # Settings pages
│   │   ├── services/                # API service layer
│   │   ├── store/                   # Zustand state management
│   │   ├── types/                   # TypeScript type definitions
│   │   ├── App.tsx                  # Main App component
│   │   ├── index.css                # Global styles + Tailwind
│   │   ├── main.tsx                 # Application entry point
│   │   └── vite-env.d.ts            # Vite type definitions
│   ├── index.html                   # HTML entry point
│   ├── package.json                 # Dependencies and scripts
│   ├── tsconfig.json                # TypeScript configuration
│   ├── tsconfig.node.json           # TypeScript config for Vite
│   ├── vite.config.ts               # Vite configuration
│   ├── tailwind.config.js           # Tailwind CSS configuration
│   ├── postcss.config.js            # PostCSS configuration
│   ├── .eslintrc.cjs                # ESLint configuration
│   ├── .gitignore                   # Git ignore rules
│   └── Dockerfile                   # Docker configuration
├── plugins/                         # ❌ DA COMPLETARE - Scanner modules
│   ├── nmap_scanner/               # ✅ IMPLEMENTATO- Nmap scanning module
│   │   ├── __init__.py            # Package initialization
│   │   ├── nmap_scanner.py        # Main scanner application
│   │   ├── config.py              # Configuration settings
│   │   ├── test_nmap.py           # Test utility for nmap functionality
│   │   ├── Dockerfile             # Docker configuration (Kali Linux based)
│   │   └── requirements.txt       # Python dependencies
│   ├── fingerprint_scanner/        # ❌ DA IMPLEMENTARE - Fingerprinting module
│   ├── enum_scanner/               # ❌ DA IMPLEMENTARE - Enumeration module
│   ├── web_scanner/                # ❌ DA IMPLEMENTARE - Web scanning module
│   ├── vuln_lookup/                # ❌ DA IMPLEMENTARE - Vulnerability lookup module
│   └── report_generator/           # ❌ DA IMPLEMENTARE - Report generation module
├── Docs/                           # Cartella contenente tutti i file .md
│   ├── API.md                      # ✅ DA AGGIORNARE - Documentazione API
│   ├── Components.md               # Spiegazione tecnologie scelte
│   ├── Deploy.md                   # Indicazioni sulle fasi di sviluppo
│   ├── ENV.md                      # ✅ AGGIORNATO - Documentazione ENV utilizzate
│   ├── README.md                   # Descrizione del progetto
│   ├── Structure.md                # ✅ AGGIORNATO - Questo file
│   ├── Test.md                     # ✅ DA AGGIORNARE - Test da eseguire per testare i vari componenti
│   ├── Utils.md                    # ✅ DA AGGIORNARE - Comandi utili per sviluppo e l'avvio del sistema
│   └── Workflow.md                 # Spiegazione workflow scansione
├── docker-compose.yml              # ✅ AGGIORNATO - Docker Compose configuration
├── .env.example                    # ✅ AGGIORNATO - File esempio delle env utilizzate
└── .gitignore                      # file gitignore

## Stato Implementazione

### ✅ COMPLETATO
- **Backend Django Orchestrator**: Completo con models, API, admin, services
- **Database Models**: Customer, PortList, ScanType, Target, Scan, ScanDetail
- **API REST**: CRUD completo per tutti i models con filtri e paginazione
- **RabbitMQ Integration**: Services per publishing e consumer per status updates
- **API Gateway FastAPI**: Reverse proxy completo verso backend Django
- **Nmap Scanner Module**: Modulo completo per scansioni di rete con Nmap
- **Docker Configuration**: docker-compose.yml aggiornato con tutti i servizi
- **Initial Data**: Fixtures con PortList e ScanType predefiniti
- **Admin Interface**: Django admin configurato per tutti i models
- **Logging & Monitoring**: Sistema di logging centralizzato nell'API Gateway

### ✅ COMPLETATO
- **Backend Django Orchestrator**: Completo con models, API, admin, services
- **Database Models**: Customer, PortList, ScanType, Target, Scan, ScanDetail
- **API REST**: CRUD completo per tutti i models con filtri e paginazione
- **RabbitMQ Integration**: Services per publishing e consumer per status updates
- **API Gateway FastAPI**: Reverse proxy completo verso backend Django
- **Nmap Scanner Module**: Modulo completo per scansioni di rete con Nmap
- **Docker Configuration**: docker-compose.yml aggiornato con tutti i servizi
- **Initial Data**: Fixtures con PortList e ScanType predefiniti
- **Admin Interface**: Django admin configurato per tutti i models
- **Logging & Monitoring**: Sistema di logging centralizzato nell'API Gateway

### 🚧 IN SVILUPPO
- **Frontend React**: Setup iniziale completato, componenti UI in sviluppo
  - ✅ Configurazione base (React + TypeScript + Vite)
  - ✅ Integrazione shadcn/ui e Tailwind CSS
  - ✅ Tema dark con palette di grigi
  - ✅ Struttura routing e layout base
  - ✅ Configurazione API client (axios)
  - ✅ Type definitions per tutti i modelli
  - ❌ Componenti UI (in sviluppo)
  - ❌ Pagine principali (Dashboard, Targets, Scans, Settings)
  - ❌ Gestione stato con Zustand
  - ❌ Integrazione completa con API Gateway

### ✅ API Gateway - Caratteristiche Implementate
- **Reverse Proxy**: Tutti gli endpoint del backend accessibili tramite gateway
- **Health Checks**: Endpoint dedicati per monitoring e readiness/liveness probes
- **Request Logging**: Middleware personalizzato per tracciare tutte le richieste
- **Error Handling**: Gestione completa degli errori con propagazione appropriata
- **CORS Support**: Configurazione CORS per frontend development
- **Async Operations**: Supporto completo per operazioni asincrone
- **Configuration Management**: Sistema di configurazione centralizzato
- **Docker Integration**: Container completamente configurato e integrato

### ✅ Nmap Scanner Module - Caratteristiche Implementate
- **Network Scanning**: Scansioni di discovery, porte TCP/UDP, version detection
- **XML Parsing**: Parser completo per output XML di Nmap
- **RabbitMQ Integration**: Consumer per richieste e publisher per status updates
- **API Communication**: Integrazione completa con API Gateway per parametri e risultati
- **Error Handling**: Gestione robusta degli errori con timeout e retry logic
- **Security**: Container basato su Kali Linux con user non-root
- **Configuration**: Sistema di configurazione flessibile con validazione target
- **Testing**: Suite di test completa per verificare funzionalità

### ❌ DA IMPLEMENTARE
- **Altri Scanner Modules**: Fingerprint, Enum, Web, Vuln Lookup, Report Generator
- **Authentication**: Sistema di autenticazione (struttura predisposta)
- **Rate Limiting**: Limitazione delle richieste (opzionale)
- **Testing**: Unit tests e integration tests

## Note Tecniche

### API Gateway FastAPI
- **Framework**: FastAPI 0.109.0 con supporto asincrono
- **HTTP Client**: httpx per comunicazione con backend
- **Middleware**: Custom logging middleware per tracciamento richieste
- **Configuration**: Pydantic Settings per gestione configurazioni
- **Error Handling**: Gestione centralizzata degli errori con logging dettagliato
- **Health Checks**: Endpoint dedicati per Kubernetes-style probes

### Comunicazione Inter-Servizi
- **API Gateway → Backend**: HTTP/REST tramite httpx async client
- **Backend → RabbitMQ**: pika per messaggi asincroni
- **Scanner Modules → API Gateway**: HTTP/REST (futuro)

### URL Mapping
- **Frontend**: http://vapter.szini.it:3000 (futuro)
- **API Gateway**: http://vapter.szini.it:8080
- **Backend Django**: http://vapter.szini.it:8000 (diretto + tramite gateway)
- **RabbitMQ Management**: http://vapter.szini.it:15672

### Pattern Implementati
- **API Gateway Pattern**: Single entry point per tutti i servizi
- **Circuit Breaker**: Timeout e retry logic nel client HTTP
- **Centralized Logging**: Logging unificato nell'API Gateway
- **Health Check Pattern**: Endpoint standard per monitoring
```