## Comandi Utili (Sviluppo Locale)


## Comandi per setup iniziale


**Assumendo che si sia nella root del progetto.**

```bash

# Costruire i container
docker-compose build

# Ricostruire un singolo container
docker-compose build backend

# Avviare i container
docker-compose up -d

# Riavviare un singolo container
docker-compose restart backend

# Visualizzare i log dei servizi
docker-compose logs -f
docker-compose logs -f api_gateway
docker-compose logs -f backend

# Fermare i container
docker-compose down

# Fermare i container e pulizia volumi
docker-compose down -v

# Rimuove immagini dangling
docker images -q --filter "dangling=true" | xargs -r docker rmi 

# Eseguire comandi manage.py nel container Django
docker-compose exec backend python manage.py makemigrations orchestrator_api
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```