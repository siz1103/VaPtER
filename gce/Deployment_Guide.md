# GCE Plugin Deployment Guide

## Riepilogo Implementazione

Il plugin GCE per VaPtER è stato implementato con successo. Ecco cosa è stato creato:

### 📁 File Backend
- `backend/orchestrator_api/models.py` - Aggiunto modello `GceResult`
- `backend/orchestrator_api/migrations/0003_add_gceresult.py` - Migration per il nuovo modello
- `backend/orchestrator_api/serializers.py` - Aggiunto serializers per GCE
- `backend/orchestrator_api/views.py` - Aggiunte API endpoints per GCE
- `backend/orchestrator_api/admin.py` - Configurazione admin per GceResult
- `backend/orchestrator_api/urls.py` - Routing per le nuove API
- `backend/orchestrator_api/services.py` - Aggiunta gestione completamento GCE
- `backend/test_gce_integration.py` - Script di test integrazione

### 📁 File Plugin
- `plugins/gce_scanner/Dockerfile` - Container basato su Python 3.12
- `plugins/gce_scanner/requirements.txt` - Dipendenze Python (python-gvm, etc.)
- `plugins/gce_scanner/config.py` - Configurazione del plugin
- `plugins/gce_scanner/gce_scanner.py` - Logica principale del plugin
- `plugins/gce_scanner/test_gce.py` - Test di connessione GCE
- `plugins/gce_scanner/__init__.py` - Package initialization
- `plugins/gce_scanner/README.md` - Documentazione del plugin

### 📁 File Configurazione
- `.env.example` - Aggiornato con variabili GCE
- `docker-compose.yml` - Aggiunto servizio gce_scanner
- `setup-gce-volume.sh` - Script per configurare i volumi condivisi

### 📁 File GCE
- `gce/.env.gce.example` - Template configurazione GCE
- `gce/start-gce.sh` - Script avvio facilitato
- `gce/scripts/setup-vapter-user.sh` - Script creazione utente API
- `gce/python_integration_example.py` - Esempio integrazione diretta

### 📁 Documentazione
- `Docs/API.md` - Aggiornato con endpoints GCE
- `Docs/ENV.md` - Aggiornato con variabili GCE
- `GCE_DEPLOYMENT_GUIDE.md` - Questa guida

## 🚀 Steps per il Deployment

### 1. Avviare GCE

```bash
cd gce
cp .env.gce.example .env.gce
# Editare .env.gce con le password desiderate
chmod +x start-gce.sh
./start-gce.sh
```

### 2. Configurare il Volume Condiviso

```bash
# Dalla root del progetto
chmod +x setup-gce-volume.sh
sudo ./setup-gce-volume.sh
```

### 3. Aggiornare .env di VaPtER

```bash
# Aggiungere al file .env principale
GCE_USERNAME=vapter_api
GCE_PASSWORD=your_secure_password_here  # Stessa password configurata in .env.gce
```

### 4. Applicare le Migrazioni

```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

### 5. Ricostruire e Avviare i Container

```bash
# Build del nuovo plugin
docker-compose build gce_scanner

# Riavviare tutti i servizi
docker-compose down
docker-compose up -d
```

### 6. Verificare il Funzionamento

```bash
# Test connessione GCE
docker-compose exec gce_scanner python test_gce.py

# Verificare i log
docker-compose logs -f gce_scanner

# Test dal backend
docker-compose exec backend python test_gce_integration.py
```

## 🔍 Troubleshooting

### Socket non trovato
```bash
# Verificare che il volume sia montato
docker-compose exec gce_scanner ls -la /mnt/gce_sockets/
```

### Autenticazione fallita
```bash
# Verificare/creare utente in GCE
cd gce
docker compose -f docker-compose-gce.yml exec -u gvmd gvmd \
  gvmd --create-user=vapter_api --password=your_password
```

### Container non parte
```bash
# Verificare i log
docker-compose logs gce_scanner
```

## 📊 Utilizzo

1. **Abilitare GCE in un Scan Type**:
   - Admin Django: http://vapter.szini.it:8000/admin/
   - Editare un Scan Type e abilitare `plugin_gce`

2. **Avviare una scansione**:
   - Creare un target
   - Avviare una scansione con un tipo che ha GCE abilitato
   - Il plugin si attiverà automaticamente dopo nmap (e fingerprint se abilitata)

3. **Monitorare il progresso**:
   - Admin Django → GCE Results
   - API: GET /api/orchestrator/gce-results/
   - Logs: `docker-compose logs -f gce_scanner`

## 🔐 Sicurezza

- Le password GCE sono gestite tramite variabili d'ambiente
- Il socket Unix è montato in sola lettura (`:ro`)
- L'utente `vapter_api` dovrebbe avere solo i permessi necessari
- I report completi sono salvati nel database (considerare la cifratura per dati sensibili)

## 🔄 Prossimi Passi

1. **Parsing dei Report**: Implementare il parsing XML/JSON per estrarre le singole vulnerabilità
2. **UI Frontend**: Aggiungere visualizzazione risultati GCE nell'interfaccia React
3. **Profili di Scansione**: Permettere selezione dinamica dei profili GCE
4. **Scansioni Autenticate**: Supporto per credenziali SSH/SMB
5. **Report Differenziali**: Confronto tra scansioni successive

## 📝 Note Finali

- Il plugin è progettato per essere asincrono e non bloccare altri plugin
- Le scansioni GCE possono richiedere molto tempo (ore)
- I log completi sono molto verbosi, considerare la rotazione
- Il parsing dei report XML può essere memory-intensive per target grandi

Per supporto o domande, consultare la documentazione nei file README dei singoli componenti.