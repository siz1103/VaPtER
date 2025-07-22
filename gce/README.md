# gce/README.md

# Greenbone Community Edition (GCE) per VaPtER

Questo è il setup Docker di Greenbone Community Edition per l'integrazione con VaPtER.

## Avvio rapido

1. Copia il file di configurazione:
```bash
cp .env.gce.example .env.gce
```

2. Modifica `.env.gce` con le tue credenziali preferite

3. Avvia GCE:
```bash
docker-compose -f docker-compose-gce.yml --env-file .env.gce up -d
```

## Primo avvio

Il primo avvio richiederà **molto tempo** (30-60 minuti) per:
- Scaricare tutti i feed di vulnerabilità
- Inizializzare il database
- Configurare tutti i componenti

Puoi monitorare il progresso con:
```bash
docker-compose -f docker-compose-gce.yml logs -f
```

## Accesso

- **Web UI**: http://vapter.szini.it:8443
- **API**: http://vapter.szini.it:9390
- **Username**: admin (o quello configurato in .env.gce)
- **Password**: admin_password_123 (o quella configurata in .env.gce)

## Verifica stato

Controlla che tutti i container siano running:
```bash
docker-compose -f docker-compose-gce.yml ps
```

Verifica i feed:
```bash
docker-compose -f docker-compose-gce.yml exec gce-gvmd gvmd --get-nvt-feed-version
```

## Comandi utili

### Restart
```bash
docker-compose -f docker-compose-gce.yml restart
```

### Stop
```bash
docker-compose -f docker-compose-gce.yml down
```

### Aggiornamento feed manuale
```bash
docker-compose -f docker-compose-gce.yml exec gce-gvmd greenbone-feed-sync
```

### Creazione utente aggiuntivo
```bash
docker-compose -f docker-compose-gce.yml exec gce-gvmd gvmd --create-user=newuser --password=newpassword
```

## Integrazione con VaPtER

L'integrazione avverrà tramite:
1. Python GVM library per comunicare con l'API
2. RabbitMQ per la gestione delle code
3. API Gateway di VaPtER per il salvataggio dei risultati

## Troubleshooting

### I feed non si scaricano
Verifica la connessione internet e riavvia:
```bash
docker-compose -f docker-compose-gce.yml restart gce-vulnerability-tests
```

### La web UI non risponde
Controlla i log di gsa:
```bash
docker-compose -f docker-compose-gce.yml logs gce-gsa
```

### Errori di permessi
Assicurati che i volumi abbiano i permessi corretti:
```bash
docker-compose -f docker-compose-gce.yml down -v
docker-compose -f docker-compose-gce.yml up -d
```