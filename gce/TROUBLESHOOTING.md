# gce/TROUBLESHOOTING.md

# Troubleshooting Greenbone Community Edition

## Problemi comuni e soluzioni

### 1. Container che non partono

**Sintomo**: Alcuni container sono in stato "Exited" o "Restarting"

**Verifiche**:
```bash
# Controlla lo stato
docker compose -f docker-compose-gce.yml ps

# Verifica i logs del container problematico
docker compose -f docker-compose-gce.yml logs [nome-servizio]
```

**Soluzioni comuni**:
- Verifica di avere abbastanza RAM (minimo 4GB, consigliati 8GB)
- Verifica spazio disco (minimo 20GB liberi)
- Riavvia Docker: `sudo systemctl restart docker`

### 2. GVMD non diventa mai "ready"

**Sintomo**: Il log continua a mostrare "Updating VT info" per molto tempo

**Soluzione**:
```bash
# È normale al primo avvio, può richiedere 30-60 minuti
# Verifica il progresso
docker compose -f docker-compose-gce.yml logs -f gvmd | grep -E "(Updating|Manager is ready)"
```

### 3. Errore "Failed to find port_list"

**Sintomo**: Errori nella creazione di scan task

**Soluzione**:
```bash
# Forza l'aggiornamento dei dati SCAP
docker compose -f docker-compose-gce.yml restart scap-data cert-bund-data
```

### 4. Web UI non accessibile

**Sintomo**: Connessione rifiutata su porta 8443

**Verifiche**:
```bash
# Verifica che GSA sia in esecuzione
docker compose -f docker-compose-gce.yml ps gsa

# Verifica binding porta
docker compose -f docker-compose-gce.yml port gsa 80

# Verifica firewall
sudo iptables -L -n | grep 8443
```

### 5. Autenticazione fallita

**Sintomo**: Login con admin/admin non funziona

**Soluzione**:
```bash
# Reset password admin
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd \
  gvmd --user=admin --new-password='nuova_password'

# Verifica che l'utente esista
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd \
  gvmd --get-users
```

### 6. Feed non aggiornati

**Sintomo**: Vulnerabilità obsolete o mancanti

**Soluzione**:
```bash
# Aggiornamento manuale completo
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd \
  greenbone-feed-sync

# Verifica versione feed
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd \
  gvmd --get-nvt-feed-version
```

### 7. Scan bloccati o lenti

**Sintomo**: Le scansioni non progrediscono

**Verifiche**:
```bash
# Controlla ospd-openvas
docker compose -f docker-compose-gce.yml logs ospd-openvas

# Verifica Redis
docker compose -f docker-compose-gce.yml exec redis-server redis-cli ping
```

**Soluzioni**:
- Riavvia ospd-openvas: `docker compose -f docker-compose-gce.yml restart ospd-openvas`
- Pulisci cache Redis se necessario

### 8. Errori di permessi

**Sintomo**: Permission denied nei logs

**Soluzione**:
```bash
# Fix permessi volumi
docker compose -f docker-compose-gce.yml down
sudo chown -R 1001:1001 /var/lib/docker/volumes/greenbone-community-edition_*
docker compose -f docker-compose-gce.yml up -d
```

### 9. Container esce con codice 137

**Sintomo**: Container terminato con exit code 137

**Causa**: Out of Memory (OOM)

**Soluzione**:
- Aumenta la RAM disponibile
- Riduci il numero di scan paralleli
- Monitora l'uso memoria: `docker stats`

### 10. Porte già in uso

**Sintomo**: Error starting userland proxy: bind: address already in use

**Soluzione**:
```bash
# Trova cosa usa la porta
sudo lsof -i :8443
sudo lsof -i :9390

# Cambia le porte in .env.gce
GCE_WEB_PORT=8444
GCE_API_PORT=9391
```

## Debug avanzato

### Accesso shell ai container

```bash
# Shell in GVMD
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd /bin/bash

# Shell in ospd-openvas
docker compose -f docker-compose-gce.yml exec ospd-openvas /bin/bash
```

### Verifica connettività interna

```bash
# Test socket GVMD
docker compose -f docker-compose-gce.yml exec gvm-tools \
  gvm-cli socket --socketpath /run/gvmd/gvmd.sock --xml "<get_version/>"
```

### Logs dettagliati

```bash
# Abilita debug logging per GVMD
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd \
  gvmd --log-level=debug
```

### Monitoraggio risorse

```bash
# Monitor real-time
docker stats $(docker compose -f docker-compose-gce.yml ps -q)

# Spazio disco usato dai volumi
docker system df -v | grep greenbone
```

## Reset completo

Se niente funziona, prova un reset completo:

```bash
# Backup dei dati importanti se necessario
# ...

# Stop e rimuovi tutto
docker compose -f docker-compose-gce.yml down -v
docker system prune -a --volumes

# Ricomincia da capo
rm .env.gce
./start-gce.sh
```

## Supporto

Per problemi specifici di GCE:
- [Forum Greenbone Community](https://forum.greenbone.net/)
- [GitHub Issues](https://github.com/greenbone/gvmd/issues)

Per problemi di integrazione con VaPtER:
- Controlla i logs del plugin GCE in VaPtER
- Verifica la connettività tra i container VaPtER e GCE