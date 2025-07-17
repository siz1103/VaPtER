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
├── frontend/                        # ✅ COMPLETATO - React + shadcn/ui
│   ├── src/                         # Source code
│   │   ├── components/              # React components
│   │   │   ├── layout/              # Layout components
│   │   │   │   ├── Layout.tsx       # Main layout component
│   │   │   │   ├── Header.tsx       # Header with customer dropdown
│   │   │   │   ├── Sidebar.tsx      # Navigation sidebar
│   │   │   │   └── CustomerDropdown.tsx # Customer selection
│   │   │   ├── customers/           # Customer-related components
│   │   │   │   └── CustomerForm.tsx # Customer form modal
│   │   │   ├── settings/            # ✅ NUOVO - Settings components
│   │   │   │   ├── PortListForm.tsx     # Port list form modal
│   │   │   │   ├── PortListTable.tsx    # Port list data table
│   │   │   │   ├── ScanTypeForm.tsx     # Scan type form modal
│   │   │   │   └── ScanTypeTable.tsx    # Scan type data table
│   │   │   └── ui/                  # shadcn/ui components
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
│   │   │       ├── switch.tsx       # ✅ NUOVO - Switch component
│   │   │       ├── select.tsx       # ✅ NUOVO - Select component
│   │   │       ├── table.tsx        # ✅ NUOVO - Table component
│   │   │       ├── alert-dialog.tsx # ✅ NUOVO - Alert dialog component
│   │   │       └── badge.tsx        # ✅ NUOVO - Badge component
│   │   ├── hooks/                   # Custom React hooks
│   │   │   └── .gitkeep
│   │   ├── lib/                     # Utilities and helpers
│   │   │   ├── api.ts               # API client configuration
│   │   │   └── utils.ts             # Utility functions
│   │   ├── pages/                   # Page components
│   │   │   ├── Dashboard.tsx        # Dashboard page
│   │   │   └── settings/            # ✅ NUOVO - Settings pages
│   │   │       ├── PortLists.tsx    # Port lists management page
│   │   │       └── ScanTypes.tsx    # Scan types management page
│   │   ├── services/                # API service layer
│   │   │   ├── customerService.ts   # Customer API calls
│   │   │   ├── portListService.ts   # ✅ NUOVO - Port list API calls
│   │   │   └── scanTypeService.ts   # ✅ NUOVO - Scan type API calls
│   │   ├── store/                   # Zustand state management
│   │   │   └── customerStore.ts     # Customer global state
│   │   ├── types/                   # TypeScript type definitions
│   │   │   └── index.ts             # All model types
│   │   ├── App.tsx                  # ✅ AGGIORNATO - Main App with settings routes
│   │   ├── index.css                # Global styles + Tailwind
│   │   ├── main.tsx                 # Application entry point
│   │   └── vite-env.d.ts            # Vite type definitions
│   ├── index.html                   # HTML entry point
│   ├── package.json                 # ✅ AGGIORNATO - Dependencies and scripts
│   ├── tsconfig.json                # TypeScript configuration
│   ├── tsconfig.node.json           # TypeScript config for Vite
│   ├── vite.config.ts               # Vite configuration
│   ├── tailwind.config.js           # Tailwind CSS configuration
│   ├── postcss.config.js            # PostCSS configuration
│   ├── .eslintrc.cjs                # ESLint configuration
│   ├── .gitignore                   # Git ignore rules
│   ├── Dockerfile                   # Docker configuration
│   ├── create-directories.sh        # Directory creation script
│   └── Readme.md                    # Frontend documentation
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
│   ├── API.md                      # ✅ AGGIORNATO - Documentazione API con Settings
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

### ✅ COMPLETATO - Frontend React
- **Configurazione base**: React + TypeScript + Vite
- **Integrazione shadcn/ui**: Tutti i componenti UI necessari implementati
- **Tema dark**: Tema dark con palette di grigi sempre attivo
- **Struttura routing**: Routing con React Router e layout responsive
- **API client**: Axios configurato con interceptors e error handling
- **Type definitions**: TypeScript types per tutti i modelli backend
- **Layout system**: Header con customer dropdown e sidebar di navigazione
- **State management**: Zustand per customer selection globale
- **Dashboard**: Pagina dashboard con overview customer-specifica
- **Customer management**: CRUD completo con validazione e toast notifications

### ✅ NUOVO - Settings Pages Implementate
- **Port Lists Management**:
  - ✅ Pagina completa con tabella moderna e filtri dinamici
  - ✅ Form modale per creazione/modifica con validazione ports
  - ✅ Conteggio automatico porte (TCP/UDP)
  - ✅ Validazione formato porte (singole, range, combinazioni)
  - ✅ Azioni CRUD con conferma cancellazione
  - ✅ Gestione errori per dipendenze (usato da scan types)
  - ✅ Ricerca real-time per nome, descrizione, porte

- **Scan Types Management**:
  - ✅ Pagina completa con tabella avanzata e badges
  - ✅ Form modale complesso con switch e select
  - ✅ Logica "Discovery Only" che disabilita port lists e plugins
  - ✅ Integrazione con Port Lists dropdown
  - ✅ Configurazione plugin opzionali (finger, enum, web, vuln)
  - ✅ Preview configurazione con summary
  - ✅ Azioni CRUD con conferma cancellazione
  - ✅ Filtri dinamici e ricerca avanzata

- **Componenti UI Aggiunti**:
  - ✅ Switch component per boolean values
  - ✅ Select component con dropdown
  - ✅ Table component responsivo e moderno
  - ✅ AlertDialog per conferme cancellazione
  - ✅ Badge component per status e tags

- **Services e API Integration**:
  - ✅ portListService.ts con validazione e utilities
  - ✅ scanTypeService.ts per tutte le operazioni CRUD
  - ✅ Error handling e toast notifications
  - ✅ TanStack Query per caching e sincronizzazione
  - ✅ Invalidazione cache automatica dopo mutazioni

### 🚧 DA SVILUPPARE (Prossima Fase)
- **Pagine Targets**: CRUD per target management customer-specific
- **Pagine Scans**: Visualizzazione e gestione scansioni
- **Polling Updates**: Real-time status updates per scansioni in corso
- **Results Visualization**: Visualizzazione risultati scansioni
- **Report Management**: Download e gestione report generati

### ❌ DA IMPLEMENTARE (Fasi Future)
- **Altri Scanner Modules**: Fingerprint, Enum, Web, Vuln Lookup, Report Generator
- **Authentication**: Sistema di autenticazione utente
- **Permissions**: Controllo accessi e autorizzazioni
- **Advanced Filtering**: Filtri avanzati per tutte le pagine
- **Data Export**: Export di dati in vari formati
- **Notifications**: Sistema di notifiche real-time
- **Dashboards Avanzate**: Grafici e analytics
- **API Rate Limiting**: Limitazione delle richieste

## Note Tecniche Aggiornate

### Nuovi Componenti UI Implementati
- **Switch**: Componente toggle per valori boolean con accessibilità
- **Select**: Dropdown con search e multi-select capabilities
- **Table**: Tabella responsiva con sorting e hover effects
- **AlertDialog**: Dialog modali per conferme distruttive
- **Badge**: Componenti per status, tags e categorizzazione

### Pattern di Validazione
- **Port Validation**: Regex e logica per validare formati porte complessi
- **Form Validation**: Validazione real-time con feedback immediato
- **API Error Handling**: Gestione centralizzata errori con toast notifications

### State Management Pattern
- **Global State**: Zustand per customer selection
- **Server State**: TanStack Query per API data con caching intelligente
- **Form State**: React Hook Form per gestione form complessi
- **UI State**: useState locale per modali e UI temporanea

### Routing Architecture
```
/                     # Dashboard
/targets             # Target management (da implementare)
/scans               # Scan management (da implementare)
/settings/port-lists # ✅ Port Lists management
/settings/scan-types # ✅ Scan Types management
```

### API Integration Pattern
- **Servizio Layer**: Separazione concerns tra UI e API calls
- **Type Safety**: Tipizzazione completa per request/response
- **Error Boundaries**: Gestione errori a livello di pagina
- **Loading States**: Stati di caricamento consistenti
- **Optimistic Updates**: Aggiornamenti UI ottimistici quando appropriato

### Design System
- **Color Palette**: Dark theme con grigi e accent colors
- **Typography**: Sistema tipografico coerente
- **Spacing**: Spacing system basato su Tailwind
- **Components**: shadcn/ui come base per consistenza
- **Icons**: Lucide React per iconografia moderna

### Performance Optimizations
- **Code Splitting**: Lazy loading per pagine
- **Query Optimization**: TanStack Query con staleTime e cacheTime
- **Bundle Size**: Tree shaking e import ottimizzati
- **Render Optimization**: Memo e callback ottimizzazioni

### URL Mapping Aggiornato
- **Frontend**: http://vapter.szini.it:3000 ✅ ATTIVO
- **API Gateway**: http://vapter.szini.it:8080 ✅ ATTIVO
- **Backend Django**: http://vapter.szini.it:8000 ✅ ATTIVO
- **RabbitMQ Management**: http://vapter.szini.it:15672 ✅ ATTIVO

### Pattern Implementati
- **CRUD Operations**: Pattern consistente per tutte le entità
- **Modal Management**: Gestione modali con state e props drilling
- **Table Actions**: Dropdown menu pattern per azioni entità
- **Search & Filter**: Pattern di ricerca real-time
- **Form Handling**: Pattern validazione e submission
- **Error Handling**: Pattern gestione errori API e UI
- **Loading States**: Pattern loading states consistenti