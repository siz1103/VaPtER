# VaPtER Frontend

Frontend React per la piattaforma VaPtER di Vulnerability Assessment.

## Stack Tecnologico

- **React 18** - Framework UI
- **TypeScript** - Type safety
- **Vite** - Build tool veloce
- **shadcn/ui** - Componenti UI moderni e personalizzabili
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Routing
- **Tanstack Query** - Data fetching e caching
- **Zustand** - State management
- **Axios** - HTTP client
- **Lucide React** - Icone moderne

## Struttura Progetto

```
src/
├── components/      # Componenti React riutilizzabili
│   ├── layout/      # Componenti di layout (Header, Sidebar, etc.)
│   └── ui/          # Componenti UI base (shadcn/ui)
├── hooks/           # Custom React hooks
├── lib/             # Utilities e configurazioni
├── pages/           # Componenti pagina
│   └── settings/    # Pagine di settings
├── services/        # Servizi API
├── store/           # Zustand store per stato globale
└── types/           # TypeScript type definitions
```

## Sviluppo Locale

Il frontend viene eseguito all'interno di un container Docker:

```bash
# Build e avvio
docker-compose build frontend
docker-compose up -d frontend

# Visualizzare logs
docker-compose logs -f frontend

# Accedere al container
docker-compose exec frontend sh
```

L'applicazione sarà disponibile su http://vapter.szini.it:3000/

## Configurazione

### Variabili d'Ambiente

- `VITE_API_URL`: URL base per le API (default: `/api`)

### Proxy Configuration

Il proxy per le API è configurato in `vite.config.ts`:
- Tutte le richieste a `/api/*` vengono inoltrate a `http://api_gateway:8080`

## Design System

- **Tema**: Dark mode con palette di grigi
- **Font**: System fonts per performance ottimali
- **Icone**: Lucide React per consistenza
- **Componenti**: shadcn/ui per UI moderna e accessibile

## Prossimi Step

- [x] Setup iniziale e configurazione
- [x] Implementazione componenti UI base
- [x] Layout principale con Header e Sidebar
- [x] Gestione stato con Zustand
- [x] Integrazione API services (customer service)
- [x] Pagina Dashboard base
- [x] Gestione Customer con dropdown
- [x] Modal per creazione customer
- [ ] Pagine Targets e Scans complete
- [ ] Pagine Settings (Port Lists, Scan Types)
- [ ] Polling per aggiornamenti scansioni
- [ ] Gestione errori e loading states

## Note di Sviluppo

- Tutti i componenti utilizzano TypeScript per type safety
- shadcn/ui permette personalizzazione completa dei componenti
- Il tema dark è sempre attivo come richiesto
- L'architettura è predisposta per future implementazioni (auth, WebSocket, etc.)