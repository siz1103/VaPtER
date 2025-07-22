# gce/README.md

# Greenbone Community Edition (GCE) per VaPtER

Questo è il setup Docker di Greenbone Community Edition per l'integrazione con VaPtER, basato sulla versione ufficiale più recente.

## Prerequisiti

- Docker e Docker Compose installati
- Almeno 8GB di RAM disponibile
- 20GB di spazio disco libero

## Struttura directory

```
gce/
├── docker-compose-gce.yml    # Docker compose principale
├── .env.gce.example          # Template variabili d'ambiente
├── .env.gce                  # Variabili d'ambiente (da creare)
├── scripts/
│   └── setup-admin.sh        # Script per setup utente admin
├── README.md                 # Questa documentazione
└── start-gce.sh              # Script di avvio
```

## Avvio rapido

1. Crea la directory scripts e rendi eseguibile lo script:
```bash
mkdir -p scripts
chmod +x scripts/setup-admin.sh
```

2. Copia il file di configurazione:
```bash
cp .env.gce.example .env.gce
```

3. Modifica `.env.gce` con le tue credenziali preferite

4. Avvia GCE:
```bash
docker compose -f docker-compose-gce.yml --env-file .env.gce up -d
```

## Primo avvio

Il primo avvio richiederà **molto tempo** (30-60 minuti) per:
- Scaricare tutte le immagini Docker (~5GB)
- Scaricare tutti i feed di vulnerabilità
- Inizializzare il database
- Configurare tutti i componenti

Puoi monitorare il progresso con:
```bash
docker compose -f docker-compose-gce.yml logs -f
```

## Accesso

- **Web UI**: http://vapter.szini.it:8443
- **API OpenVASD**: http://vapter.szini.it:9390
- **Username**: admin (o quello configurato in .env.gce)
- **Password**: (quella configurata in .env.gce)

## Verifica stato

Controlla che tutti i container siano running:
```bash
docker compose -f docker-compose-gce.yml ps
```

Verifica i feed (dopo il primo avvio):
```bash
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd gvmd --get-nvt-feed-version
```

## Comandi utili

### Restart completo
```bash
docker compose -f docker-compose-gce.yml restart
```

### Stop
```bash
docker compose -f docker-compose-gce.yml down
```

### Stop e rimuovi volumi (ATTENZIONE: cancella tutti i dati)
```bash
docker compose -f docker-compose-gce.yml down -v
```

### Logs di un servizio specifico
```bash
docker compose -f docker-compose-gce.yml logs -f gvmd
docker compose -f docker-compose-gce.yml logs -f gsa
docker compose -f docker-compose-gce.yml logs -f openvasd
```

### Aggiornamento manuale feed
```bash
# Usa greenbone-feed-sync
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd greenbone-feed-sync
```

### Creazione utente aggiuntivo
```bash
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd \
  gvmd --create-user=newuser --password=newpassword
```

### Uso di gvm-tools per automazione
```bash
# Lista tutti i target
docker compose -f docker-compose-gce.yml run --rm gvm-tools \
  gvm-cli socket --gmp-username admin --gmp-password admin \
  --xml "<get_targets/>"
```

## Integrazione con VaPtER

L'integrazione con VaPtER avverrà tramite:

1. **Python GVM library** - Per comunicare via socket Unix con GVMD
2. **OpenVASD API** - Per interazioni dirette con lo scanner (porta 9390)
3. **RabbitMQ** - Per la gestione delle code di scansione

### Esempio di connessione Python

```python
from gvm.connections import UnixSocketConnection
from gvm.protocols.gmp import Gmp

# Connessione via socket (richiede montaggio volume)
connection = UnixSocketConnection(path='/run/gvmd/gvmd.sock')
with Gmp(connection) as gmp:
    gmp.authenticate('admin', 'password')
    # Operazioni GMP...
```

## Troubleshooting

### I container non partono
```bash
# Verifica i logs
docker compose -f docker-compose-gce.yml logs

# Verifica spazio disco
df -h

# Verifica memoria
free -h
```

### Feed non si scaricano
```bash
# Riavvia i container dei feed
docker compose -f docker-compose-gce.yml restart vulnerability-tests notus-data

# Verifica connessione internet dal container
docker compose -f docker-compose-gce.yml run --rm gvm-tools ping -c 3 feed.community.greenbone.net
```

### La web UI non risponde
```bash
# Verifica che gvmd sia pronto
docker compose -f docker-compose-gce.yml logs gvmd | grep "Manager is ready"

# Verifica GSA
docker compose -f docker-compose-gce.yml logs gsa
```

### Errori di autenticazione
```bash
# Reset password admin
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd \
  gvmd --user=admin --new-password='nuova_password'
```

## Note importanti

- Il primo avvio richiede pazienza: i feed sono molto grandi
- Non interrompere il download dei feed durante il primo avvio
- I volumi Docker persistono i dati anche dopo il restart
- Per un reset completo, usa `docker compose down -v`
- La porta 8443 per la web UI può essere cambiata nel .env.gce

## Riferimenti

- [Documentazione ufficiale Greenbone](https://greenbone.github.io/docs/latest/)
- [GVM protocols documentation](https://docs.greenbone.net/API/GMP/gmp.html)
- [Python-GVM library](https://github.com/greenbone/python-gvm)