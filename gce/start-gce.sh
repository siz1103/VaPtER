#!/bin/bash
# gce/start-gce.sh
# Script per avviare Greenbone Community Edition

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=== Avvio Greenbone Community Edition per VaPtER ==="

# Verifica se Docker è installato
if ! command -v docker &> /dev/null; then
    echo "❌ Docker non è installato. Installa Docker prima di continuare."
    exit 1
fi

# Verifica se docker compose è disponibile
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif docker-compose version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose non è installato."
    exit 1
fi

# Crea directory scripts se non esiste
if [ ! -d "$SCRIPT_DIR/scripts" ]; then
    echo "Creazione directory scripts..."
    mkdir -p "$SCRIPT_DIR/scripts"
fi

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

# Verifica spazio disco
AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 20 ]; then
    echo "⚠️  ATTENZIONE: Solo ${AVAILABLE_SPACE}GB di spazio disponibile."
    echo "   Sono consigliati almeno 20GB per GCE."
    echo "   Vuoi continuare comunque? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Pull delle immagini
echo "Download delle immagini Docker (può richiedere tempo)..."
cd "$SCRIPT_DIR"
$COMPOSE_CMD -f docker-compose-gce.yml --env-file .env.gce pull

# Avvia i container
echo "Avvio container GCE..."
$COMPOSE_CMD -f docker-compose-gce.yml --env-file .env.gce up -d

echo ""
echo "✓ Container avviati!"
echo ""
echo "📌 NOTA IMPORTANTE:"
echo "   Il primo avvio richiederà 30-60 minuti per scaricare tutti i feed."
echo "   NON interrompere il processo durante il download dei feed!"
echo ""
echo "Puoi monitorare il progresso con:"
echo "  $COMPOSE_CMD -f docker-compose-gce.yml logs -f"
echo ""
echo "Per verificare quando GCE è pronto:"
echo "  $COMPOSE_CMD -f docker-compose-gce.yml logs gvmd | grep 'Manager is ready'"
echo ""
echo "Una volta completato, accedi a:"
echo "  🌐 Web UI: http://vapter.szini.it:${GCE_WEB_PORT:-8443}"
echo "  👤 Username: ${GCE_ADMIN_USER:-admin}"
echo "  🔑 Password: (quella configurata in .env.gce)"
echo ""
echo "Per verificare lo stato dei container:"
echo "  $COMPOSE_CMD -f docker-compose-gce.yml ps"