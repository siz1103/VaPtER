## **Componenti**

La piattaforma sarà composta da un insieme di microservizi containerizzati, orchestrati per operare in modo coeso.

## Indice

1. [Base](#spiegazione-base)
2. [Stack tecnologico](#stack-tecnologico-per-servizio)

## Spiegazione base
- **Frontend (UI):** React

- **API Gateway:** Python con FastAPI

- **Backend (Orchestratore):** Django REST Framework

- **Backend (Consumer):** Basato sull'immagine dell'orchestratore, questo modulo rimarrà in ascolto sulle varie code rabbitmq

- **Coda di Messaggi:** RabbitMQ

- **Database:** PostgreSQL

- **Moduli Scanner Dockerizzati:** ( ancora da valutare la base delle immagini, probabilmente kali o python)

* Nmap (per scansione di rete e identificazione servizi) 
* fingerprint e mappatura versioni non rilevate da nmap
* Enumerazione dei servizi 
* Scanner web
* Integrazione Greenbone Community Edition
* Vulnerability Lookup Module (per correlazione con database di vulnerabilità)

- **Report generator:** da approfondire


## Stack Tecnologico per Servizio

*   **API Gateway:**
    *   Linguaggio/Framework: Python / FastAPI
    *   Server WSGI/ASGI: Uvicorn
    *   Comunicazione con Backend: HTTP (tramite `httpx`)
*   **Backend Orchestratore:**
    *   Linguaggio/Framework: Python / Django REST Framework
    *   Server WSGI/ASGI: (Default Django dev server, Gunicorn/Uvicorn per produzione)
    *   Database ORM: Django ORM
*   **Backend (Consumer):**
    *   Linguaggio/Framework: Python / Django (Coda Rabbit: `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`)
*   **Coda di Messaggi:**
    *   Linguaggio/Framework: RabbitMQ
*   **Frontend (UI):**
    *   Linguaggio/Framework: React
*   **Database:**
    *   Sistema: PostgreSQL
*   **Report generator:**
    *   Linguaggio/Framework: Python
    *   Utilità chiave: Requests (per API backend), librerie per gestione json e pdf da valutare
    *   Comunicazione: Consuma da RabbitMQ (coda `report_requests`)
*   **Modulo Scanner Nmap (plugins/nmap_scanner):**
    *   Immagine Base: `kalilinux/kali-rolling`
    *   Linguaggio/Framework: Python
    *   Utilità chiave: `python3-nmap` (o `subprocess` per Nmap), `requests` (per API Gateway), `pika` (per RabbitMQ)
    *   Comunicazione:
        *   Consuma da RabbitMQ (coda `RABBITMQ_NMAP_SCAN_REQUEST_QUEUE`) messaggi contenenti `{scan_id, scan_type_id, target_host}`.
        *   Richiede parametri di scansione a API Gateway: `GET {INTERNAL_API_GATEWAY_URL}/api/orchestrator/scan_types/{scan_type_id}/`.
        *   Invia risultati parsati a API Gateway: `PUT {INTERNAL_API_GATEWAY_URL}/api/orchestrator/scans/{scan_id}/` con payload JSON.
        *   Pubblica aggiornamenti di stato su RabbitMQ (coda `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`).
*   **Modulo Scanner Fingerprint (plugins/fingerprint_scanner):** (Da definire in dettaglio)
    *   Immagine Base: `kalilinux/kali-rolling` (proposto)
    *   Linguaggio/Framework: go per compilazione/python
    *   Utilità chiave: Strumenti di fingerprint, FingerprintX https://github.com/praetorian-inc/fingerprintx.git (es. `dnsenum`, `enum4linux`, script personalizzati), `python3-requests`, `python3-pika`
    *   Comunicazione: Consuma da `RABBITMQ_FINGERPRINT_SCAN_REQUEST_QUEUE`, pubblica su `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`, interagisce con API Gateway.
*   **Modulo Scanner Enum (plugins/enum_scanner):** (Da definire in dettaglio)
    *   Immagine Base: `kalilinux/kali-rolling` (proposto)
    *   Linguaggio/Framework: Python (proposto)
    *   Utilità chiave: Strumenti di enumerazione (es. `dnsenum`, `enum4linux`, script personalizzati), `requests`, `pika`
    *   Comunicazione: Consuma da `RABBITMQ_ENUM_SCAN_REQUEST_QUEUE`, pubblica su `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`, interagisce con API Gateway.
*   **Modulo Scanner Web (plugins/web_scanner):** (Da definire in dettaglio)
    *   Immagine Base: `kalilinux/kali-rolling`
    *   Linguaggio/Framework: Python
    *   Utilità chiave: Strumenti di scansione web (es. `whatweb`, `nikto`, `gobuster`, `sqlmap` - da valutare attentamente per complessità), `requests`, `pika`
    *   Comunicazione: Consuma da `RABBITMQ_WEB_SCAN_REQUEST_QUEUE`, pubblica su `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`, interagisce con API Gateway.
*   **Modulo Vulnerability Lookup (plugins/vuln_lookup):** (Da definire in dettaglio)
    *   Immagine Base: `kalilinux/kali-rolling` o Python base (proposto)
    *   Linguaggio/Framework: Python (proposto)
    *   Utilità chiave: `searchsploit` (accesso al database locale di Exploit-DB), `requests` (per API NVD), `pika`
    *   Comunicazione: Consuma da `RABBITMQ_VULN_LOOKUP_REQUEST_QUEUE`, pubblica su `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`, interagisce con API Gateway.