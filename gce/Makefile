# gce/Makefile
# Makefile per semplificare la gestione di GCE

.PHONY: help up down logs restart status clean setup

# Default target
help:
	@echo "Greenbone Community Edition - Comandi disponibili:"
	@echo ""
	@echo "  make setup     - Setup iniziale (copia .env, crea directory)"
	@echo "  make up        - Avvia tutti i container"
	@echo "  make down      - Ferma tutti i container"
	@echo "  make logs      - Mostra i logs in tempo reale"
	@echo "  make restart   - Riavvia tutti i container"
	@echo "  make status    - Mostra lo stato dei container"
	@echo "  make clean     - Rimuove container e volumi (ATTENZIONE: cancella i dati!)"
	@echo ""
	@echo "Comandi specifici:"
	@echo "  make logs-gvmd     - Logs del servizio GVMD"
	@echo "  make logs-gsa      - Logs del servizio GSA (web UI)"
	@echo "  make feed-sync     - Aggiorna manualmente i feed"
	@echo "  make check-ready   - Verifica se GCE è pronto"

# Setup iniziale
setup:
	@echo "Setup GCE..."
	@if [ ! -f .env.gce ]; then \
		cp .env.gce.example .env.gce; \
		echo "✓ File .env.gce creato"; \
	fi
	@mkdir -p scripts
	@chmod +x scripts/setup-admin.sh
	@chmod +x start-gce.sh
	@echo "✓ Setup completato"

# Avvia i container
up: setup
	docker-compose -f docker-compose-gce.yml --env-file .env.gce up -d

# Ferma i container
down:
	docker-compose -f docker-compose-gce.yml down

# Mostra i logs
logs:
	docker-compose -f docker-compose-gce.yml logs -f

# Logs specifici
logs-gvmd:
	docker-compose -f docker-compose-gce.yml logs -f gvmd

logs-gsa:
	docker-compose -f docker-compose-gce.yml logs -f gsa

logs-openvas:
	docker-compose -f docker-compose-gce.yml logs -f openvas

# Riavvia i container
restart:
	docker-compose -f docker-compose-gce.yml restart

# Mostra lo stato
status:
	docker-compose -f docker-compose-gce.yml ps

# Pulisci tutto (ATTENZIONE!)
clean:
	@echo "⚠️  ATTENZIONE: Questo comando rimuoverà tutti i dati di GCE!"
	@echo "Premi Ctrl+C per annullare o ENTER per continuare..."
	@read confirm
	docker-compose -f docker-compose-gce.yml down -v

# Aggiorna i feed manualmente
feed-sync:
	@echo "Aggiornamento feed GCE..."
	docker-compose -f docker-compose-gce.yml exec -u gvmd gvmd greenbone-feed-sync

# Verifica se GCE è pronto
check-ready:
	@echo "Verifica stato GCE..."
	@docker-compose -f docker-compose-gce.yml logs gvmd | grep -q "Manager is ready" && \
		echo "✓ GCE è pronto!" || \
		echo "⏳ GCE non ancora pronto. Riprova tra qualche minuto..."