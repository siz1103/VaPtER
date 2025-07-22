# VaPtER Project Structure

Questo documento descrive la struttura completa del progetto VaPtER.

## Struttura Completa

```
vapter/
├── backend/                         # ✅ COMPLETATO - Django Orchestrator
│   ├── orchestrator_api/             # Main Django app
│   │   ├── __init__.py
│   │   ├── models.py                 # Customer, PortList, ScanType, Target, Scan, ScanDetail
│   │   ├── serializers.py            # DRF serializers
│   │   ├── views.py                  # ViewSets con API REST complete
│   │   ├── urls.py                   # URL routing
│   │   ├── admin.py                  # Django admin configuration
│   │   ├── apps.py                   # App configuration
│   │   ├── filters.py                # Django filters per API
│   │   ├── services.py               # Business logic e orchestration
│   │   ├── mixins.py                 # Mixins per models (timestamp, soft delete)
│   │   ├── validators.py             # Custom validators
│   │   ├── migrations/               # Database migrations
│   │   └── tests/                    # Test suite
│   ├── core/                         # Core Django settings
│   │   ├── __init__.py
│   │   ├── settings.py               # Django settings
│   │   ├── urls.py                   # Root URL configuration
│   │   ├── wsgi.py                   # WSGI application
│   │   └── asgi.py                   # ASGI application
│   ├── manage.py                     # Django management script
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Docker configuration
│   └── .env.example                  # Environment variables example
├── api_gateway/                      # ✅ COMPLETATO - FastAPI Gateway
│   ├── app/                          # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI main application
│   │   ├── config.py                 # Configuration settings
│   │   ├── models.py                 # Pydantic models
│   │   ├── proxy.py                  # Proxy logic per backend
│   │   ├── health.py                 # Health check endpoints
│   │   └── middleware/               # Custom middleware
│   │       ├── __init__.py
│   │       └── logging.py            # Request logging middleware
│   ├── Dockerfile                    # Docker configuration for API Gateway
│   └── requirements.txt              # Python dependencies
├── frontend/                         # ✅ COMPLETATO - React + shadcn/ui
│   ├── src/                          # Source code
│   │   ├── components/               # React components
│   │   │   ├── layout/               # Layout components
│   │   │   │   ├── Layout.tsx        # Main layout component
│   │   │   │   ├── Header.tsx        # Header with customer dropdown
│   │   │   │   ├── Sidebar.tsx       # Navigation sidebar
│   │   │   │   └── CustomerDropdown.tsx # Customer selection
│   │   │   ├── customers/            # Customer-related components
│   │   │   │   └── CustomerForm.tsx  # Customer form modal
│   │   │   ├── settings/             # ✅ COMPLETATO - Settings components
│   │   │   │   ├── PortListForm.tsx      # Port list form modal
│   │   │   │   ├── PortListTable.tsx     # Port list data table
│   │   │   │   ├── ScanTypeForm.tsx      # Scan type form modal
│   │   │   │   └── ScanTypeTable.tsx     # Scan type data table
│   │   │   ├── targets/              # ✅ COMPLETATO - Target-related components
│   │   │   │   ├── TargetForm.tsx        # Target form modal con validazione IP/FQDN
│   │   │   │   ├── TargetTable.tsx       # Target data table con azioni
│   │   │   │   └── StartScanDialog.tsx   # Dialog per avvio scansioni
│   │   │   ├── scans/                # ✅ NUOVO - Scan-related components
│   │   │   │   ├── ScanStatusBadge.tsx   # Badge colorato per status scansioni
│   │   │   │   ├── ScanTable.tsx         # Tabella scansioni con expand/collapse
│   │   │   │   └── ScanActions.tsx       # Dropdown azioni scansioni
│   │   │   └── ui/                   # shadcn/ui components
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       ├── dialog.tsx
│   │   │       ├── dropdown-menu.tsx
│   │   │       ├── input.tsx
│   │   │       ├── label.tsx
│   │   │       ├── textarea.tsx
│   │   │       ├── toast.tsx
│   │   │       ├── toaster.tsx
│   │   │       ├── use-toast.ts
│   │   │       ├── switch.tsx        # ✅ COMPLETATO - Switch component
│   │   │       ├── select.tsx        # ✅ COMPLETATO - Select component
│   │   │       ├── table.tsx         # ✅ COMPLETATO - Table component
│   │   │       ├── alert-dialog.tsx  # ✅ COMPLETATO - Alert dialog component
│   │   │       ├── badge.tsx         # ✅ COMPLETATO - Badge component
│   │   │       └── collapsible.tsx   # ✅ NUOVO - Collapsible component
│   │   ├── hooks/                    # Custom React hooks
│   │   │   └── .gitkeep
│   │   ├── lib/                      # Utilities and helpers
│   │   │   ├── api.ts                # API client configuration
│   │   │   └── utils.ts              # Utility functions
│   │   ├── pages/                    # Page components
│   │   │   ├── Dashboard.tsx         # Dashboard page
│   │   │   ├── Targets.tsx           # ✅ COMPLETATO - Targets management page
│   │   │   ├── Scans.tsx             # ✅ NUOVO - Scans management page
│   │   │   └── settings/             # ✅ COMPLETATO - Settings pages
│   │   │       ├── PortLists.tsx     # Port lists management page
│   │   │       └── ScanTypes.tsx     # Scan types management page
│   │   ├── services/                 # API service layer
│   │   │   ├── customerService.ts    # Customer API calls
│   │   │   ├── portListService.ts    # Port list API calls
│   │   │   ├── scanTypeService.ts    # Scan type API calls
│   │   │   ├── targetService.ts      # ✅ COMPLETATO - Target API calls con validazione
│   │   │   └── scanService.ts        # ✅ NUOVO - Scan API calls e utilities
│   │   ├── store/                    # Zustand state management
│   │   │   └── customerStore.ts      # Customer global state
│   │   ├── types/                    # TypeScript type definitions
│   │   │   └── index.ts              # All model types
│   │   ├── App.tsx                   # ✅ AGGIORNATO - Main App with scans route
│   │   ├── index.css                 # Global styles + Tailwind
│   │   ├── main.tsx                  # Application entry point
│   │   └── vite-env.d.ts             # Vite type definitions
│   ├── index.html                    # HTML entry point
│   ├── package.json                  # ✅ AGGIORNATO - Dependencies with date-fns & radix collapsible
│   ├── tsconfig.json                 # TypeScript configuration
│   ├── tsconfig.node.json            # TypeScript config for Vite
│   ├── vite.config.ts                # Vite configuration
│   ├── tailwind.config.js            # Tailwind CSS configuration
│   ├── postcss.config.js             # PostCSS configuration
│   ├── .eslintrc.cjs                 # ESLint configuration
│   ├── .gitignore                    # Git ignore rules
│   ├── Dockerfile                    # Docker configuration
│   ├── create-directories.sh         # Directory creation script
│   └── Readme.md                     # Frontend documentation
├── plugins/                          # ❌ DA COMPLETARE - Scanner modules
│   ├── nmap_scanner/                 # ✅ IMPLEMENTATO- Nmap scanning module
│   │   ├── __init__.py              # Package initialization
│   │   ├── nmap_scanner.py          # Main scanner application
│   │   ├── config.py                # Configuration settings
│   │   ├── test_nmap.py             # Test utility for nmap functionality
│   │   ├── Dockerfile               # Docker configuration (Kali Linux based)
│   │   └── requirements.txt         # Python dependencies
│   ├── fingerprint_scanner/          # ❌ DA IMPLEMENTARE - Fingerprinting module
│   ├── gce_scanner/                 # ❌ DA IMPLEMENTARE - Gce module
│   ├── web_scanner/                  # ❌ DA IMPLEMENTARE - Web scanning module
│   ├── vuln_lookup/                  # ❌ DA IMPLEMENTARE - Vulnerability lookup module
│   └── report_generator/             # ❌ DA IMPLEMENTARE - Report generation module
├── Docs/                             # Cartella contenente tutti i file .md
│   ├── API.md                        # ✅ AGGIORNATO - Documentazione API con Settings
│   ├── Components.md                 # Spiegazione tecnologie scelte
│   ├── Deploy.md                     # Indicazioni sulle fasi di sviluppo
│   ├── ENV.md                        # ✅ AGGIORNATO - Documentazione ENV utilizzate
│   ├── README.md                     # Descrizione del progetto
│   ├── Structure.md                  # ✅ AGGIORNATO - Questo file
│   ├── Test.md                       # ✅ DA AGGIORNARE - Test da eseguire per testare i vari componenti
│   ├── Utils.md                      # ✅ DA AGGIORNARE - Comandi utili per sviluppo e l'avvio del sistema
│   └── Workflow.md                   # Spiegazione workflow scansione
├── gce/                                # Directory per Greenbone Community Edition
│   ├── docker-compose-gce.yml          # Docker compose per GCE (basato su versione ufficiale)
│   ├── .env.gce.example                # Esempio variabili d'ambiente
│   ├── .env.gce                        # Variabili d'ambiente (da creare copiando .example)
│   ├── README.md                       # Documentazione dettagliata GCE
│   ├── start-gce.sh                    # Script di avvio facilitato
│   ├── python_integration_example.py   # Esempio integrazione Python con GCE
│   ├── structure.txt                   # Questo file
│   └── scripts/                        # Directory per script ausiliari
│       └── setup-admin.sh              # Script per configurazione admin user
├── docker-compose.yml                # ✅ AGGIORNATO - Docker Compose configuration
├── .env.example                      # ✅ AGGIORNATO - File esempio delle env utilizzate
└── .gitignore                        # file gitignore

## Stato Implementazione

### ✅ COMPLETATO
- **Backend Django Orchestrator**: Completo con models, API, admin, services
- **Database Models**: Customer, PortList, ScanType, Target, Scan, ScanDetail
- **API REST**: CRUD completo per tutti i modelli con filtri e paginazione
- **API Gateway FastAPI**: Proxy completo con logging e health checks
- **Database Setup**: PostgreSQL con migrazioni complete
- **Message Queue**: RabbitMQ per comunicazione con scanner modules
- **Frontend Base**: React + TypeScript + shadcn/ui + Tailwind CSS
- **Layout e Routing**: Header, Sidebar, Layout principale con routing completo
- **State Management**: Zustand per gestione stato customer
- **API Integration**: TanStack Query per data fetching e caching

### ✅ NUOVO - Implementazioni Complete (Questa Fase)

- **Pagina Scans Completa**:
  - ✅ Lista scansioni filtrata per customer selezionato
  - ✅ Tabella expandable con dettagli completi
  - ✅ Badge colorati per status scansioni con animazioni
  - ✅ Azioni complete: restart, cancel, delete, change scan type
  - ✅ Visualizzazione risultati nmap (parsed_nmap_results)
  - ✅ Polling automatico ogni 3 secondi per scansioni attive
  - ✅ Statistiche real-time (totali, attive, completate, fallite)
  - ✅ Ricerca avanzata per ID, target, scan type, status

- **Componenti Scans**:
  - ✅ ScanTable.tsx - Tabella principale con expand/collapse
  - ✅ ScanStatusBadge.tsx - Badge colorati con animazione per status attivi
  - ✅ ScanActions.tsx - Dropdown completo con tutte le azioni
  - ✅ Collapsible UI component per dettagli scansioni

- **Service Layer Scans**:
  - ✅ scanService.ts completo con tutte le API calls
  - ✅ Utilities per status management e colori
  - ✅ Gestione errori e feedback utente
  - ✅ Integration con TanStack Query per polling

- **UI/UX Enhancements**:
  - ✅ Interface coerente con altre pagine del sistema
  - ✅ Loading states e error handling
  - ✅ Responsive design per mobile e desktop
  - ✅ Feedback visivo per azioni (toast notifications)
  - ✅ Animazioni per scansioni attive (pulse effect)

### 🚧 IN SVILUPPO
- **Frontend React**: Layout principale e componenti base completati
  - ✅ Configurazione base (React + TypeScript + Vite)
  - ✅ Integrazione shadcn/ui e Tailwind CSS
  - ✅ Tema dark con palette di grigi
  - ✅ Struttura routing e layout base
  - ✅ Configurazione API client (axios)
  - ✅ Type definitions per tutti i modelli
  - ✅ Componenti UI base (Button, Card, Dialog, Input, etc.)
  - ✅ Layout con Header e Sidebar
  - ✅ Gestione stato con Zustand
  - ✅ Customer dropdown con creazione
  - ✅ Dashboard page base
  - ✅ Customer service API integration
  - ✅ Pagine Settings (Port Lists, Scan Types)
  - ✅ Pagina Targets
  - ✅ Pagina Scans (NUOVA IMPLEMENTAZIONE)
  - ✅ Polling per aggiornamenti scansioni (IMPLEMENTATO)

### ❌ DA IMPLEMENTARE (Fasi Future)
- **Altri Scanner Modules**: Fingerprint, Gce, Web, Vuln Lookup, Report Generator
- **Report Generation e Download**: Sistema di generazione e download report
- **Advanced Results Visualization**: Grafici e visualizzazioni avanzate per risultati
- **Authentication**: Sistema di autenticazione utente
- **Permissions**: Controllo accessi e autorizzazioni
- **Advanced Filtering**: Filtri avanzati per tutte le pagine
- **Data Export**: Export di dati in vari formati
- **Notifications**: Sistema di notifiche real-time (WebSocket)
- **Dashboards Avanzate**: Grafici e analytics
- **API Rate Limiting**: Limitazione delle richieste

## Note Tecniche Aggiornate

### Nuove Funzionalità Scans

#### Polling Intelligente
- Polling attivo ogni 3 secondi solo se ci sono scansioni in corso
- Automatico stop del polling quando tutte le scansioni sono complete
- Ottimizzazione performance con TanStack Query

#### Status Management
- 15 diversi status supportati (da Pending a Completed/Failed)
- Badge colorati con animazioni per status attivi
- Logic per determinare azioni disponibili basate su status

#### Azioni Avanzate
- **Restart**: Per scansioni fallite o completate
- **Cancel**: Per scansioni in corso
- **Delete**: Per scansioni non attive (con conferma)
- **Change Scan Type**: Modifica tipo di scansione

#### Visualizzazione Risultati
- Visualizzazione JSON formattata per tutti i risultati
- Expand/collapse per dettagli completi
- Supporto per tutti i tipi di risultati (nmap, finger, gce, web, vuln)
- Timestamps e durata scansioni

### Dipendenze Aggiunte
- **date-fns**: Per formattazione date e relativi calcoli
- **@radix-ui/react-collapsible**: Per componenti expandable

### Pattern Architetturali Consolidati
- **Service Layer Pattern**: Separazione logica tra components e API calls
- **Query/Mutation Pattern**: TanStack Query per gestione stato server
- **Compound Components**: Componenti riutilizzabili e modulari
- **Error Boundary Pattern**: Gestione errori centralizzata
- **Loading State Pattern**: Stati di caricamento consistenti

## URLs di Accesso Aggiornati

### Servizi Web
- **Frontend**: http://vapter.szini.it:3000/
  - **Dashboard**: http://vapter.szini.it:3000/
  - **Targets**: http://vapter.szini.it:3000/targets
  - **Scans**: http://vapter.szini.it:3000/scans ✅ NUOVO
  - **Settings - Port Lists**: http://vapter.szini.it:3000/settings/port-lists
  - **Settings - Scan Types**: http://vapter.szini.it:3000/settings/scan-types

### Note di Sviluppo Aggiornate

#### Performance Considerations
- Polling intelligente per ridurre carico server
- Lazy loading per grandi dataset
- Ottimizzazione query con filtri backend
- Caching intelligente con TanStack Query

#### Accessibility
- Supporto screen reader per tutte le azioni
- Keyboard navigation completa
- ARIA labels appropriati
- Contrast ratio conforme WCAG

#### Mobile Responsiveness
- Layout adattivo per dispositivi mobili
- Touch-friendly interactions
- Responsive tables con scroll orizzontale
- Ottimizzazione spazio per schermi piccoli