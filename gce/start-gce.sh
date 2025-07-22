#!/bin/bash
# gce/start-gce.sh
# Script per avviare Greenbone Community Edition

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=== Avvio Greenbone Community Edition per VaPtER ==="

# Verifica se esiste .env.gce
if [ ! -f "$SCRIPT_DIR/.env.gce" ]; then
    echo "File .env.gce non trovato. Copio da .env.gce.example..."
    cp "$SCRIPT_DIR/.env.gce.example" "$SCRIPT_DIR/.env.gce"
    echo "✓ File .env.gce creato. Modifica le credenziali prima di continuare!"
    echo "  Premi ENTER per continuare con le credenziali di default o CTRL+C per annullare..."
    read -r
fi

# Carica le variabili d'ambiente
export $(grep -v '^#' "$SCRIPT_DIR/.env.gce" | xargs)

echo "Configurazione:"
echo "- Web UI Port: ${GCE_WEB_PORT:-8443}"
echo "- API Port: ${GCE_API_PORT:-9390}"
echo "- Admin User: ${GCE_ADMIN_USER:-admin}"
echo ""

# Avvia i container
echo "Avvio container GCE..."
cd "$SCRIPT_DIR"
docker-compose -f docker-compose-gce.yml --env-file .env.gce up -d

echo ""
echo "✓ Container avviati!"
echo ""
echo "NOTA: Il primo avvio richiederà 30-60 minuti per scaricare tutti i feed."
echo ""
echo "Puoi monitorare il progresso con:"
echo "  docker-compose -f docker-compose-gce.yml logs -f"
echo ""
echo "Una volta completato, accedi a:"
echo "  Web UI: http://vapter.szini.it:${GCE_WEB_PORT:-8443}"
echo "  Username: ${GCE_ADMIN_USER:-admin}"
echo "  Password: (quella configurata in .env.gce)"
echo ""
echo "Per verificare lo stato:"
echo "  docker-compose -f docker-compose-gce.yml ps"