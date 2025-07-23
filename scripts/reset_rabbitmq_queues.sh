#!/bin/bash
# reset_rabbitmq_queues.sh
# Script per eliminare e ricreare le code RabbitMQ in caso di conflitti

echo "Resetting RabbitMQ queues..."

# Elimina le code esistenti
docker-compose exec rabbitmq rabbitmqctl delete_queue gce_scan_requests
docker-compose exec rabbitmq rabbitmqctl delete_queue scan_status_updates

echo "Queues deleted. They will be recreated automatically when services restart."

# Riavvia i servizi
echo "Restarting services..."
docker-compose restart gce_scanner
docker-compose restart backend

echo "Done! Check logs with: docker-compose logs -f gce_scanner"