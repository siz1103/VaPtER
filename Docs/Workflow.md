## **Workflow Dettagliato di una Scansione di Host**

Questo workflow descrive il percorso di una richiesta di scansione attraverso i vari componenti della piattaforma:


### **1. Inizio Scansione (Frontend -> API Gateway -> Backend Orchestratore)**

1. L'utente, da interfaccia web **Web Application (React)** , può creare gruppi di porte, es:
* TOP 100 TCP e TOP 100 UDP
* All IANA TCP
* ecc...

2. L'utente, da interfaccia web **Web Application (React)** , può creare diversi tipi di scansioni, es:
* discovery, solo test is alive (is_alive)
* scan veloce (nmap_base) in cui rilevare solo le porte aperte
* scan approfondito (nmap_advanced) dove rilevare anche versioni applicazioni e del sistema operativo
* scan completo (nmap_complete) dove rilevare anche le possibili vulnerabilità tramite modulo nmap
* ecc...
e associare anche i gruppi di porte trovati prima, più i plugin da eseguire completata la prima scansione

3. L'utente, dopo aver aggiunto uno o più Asset (target) tramite l'interfaccia, accede alla sezione "New Scan" della **Web Application (React)**. Seleziona un Asset dall'elenco dei target disponibili e un tipo di scansione (dall'elenco creato prima). Successivamente, clicca su "Avvia Scansione".

4. La **Web Application (React)** invia una richiesta API  all'**API Gateway (FastAPI)**, includendo l'ID dell'asset selezionato e il tipo di scansione.

5. L'**API Gateway (FastAPI)** riceve la richiesta, se tutto è valido, inoltra la richiesta al **Backend Orchestratore (Django REST Framework)**. 

6. Il **Backend Orchestratore (Django REST Framework)** riceve la richiesta:

- Crea un nuovo record di scansione nel **Database (PostgreSQL)**, impostando lo stato su "In Coda".
- Prepara un messaggio JSON contenente `scan_id`, `scan_type_id` e `target_host`.
- Pubblica questo messaggio sulla coda `RABBITMQ_NMAP_SCAN_REQUEST_QUEUE`.

7. Il **modulo nmap_scanner** (in ascolto su `RABBITMQ_NMAP_SCAN_REQUEST_QUEUE`):
    - Riceve il messaggio con `scan_id`, `scan_type_id`, `target_host`.
- Pubblica uno stato iniziale (es. `{"scan_id": X, "module": "nmap", "status": "received", "message": "Scan request received by Nmap module"}`) su `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`.
    - Chiama l'API Gateway (`INTERNAL_API_GATEWAY_URL`) per ottenere i parametri specifici della scansione.
    - Converte i parametri ottenuti in flag per il comando Nmap.
    - Esegue la scansione Nmap sull'host target.
    - Pubblica stati intermedi (es. `{"scan_id": X, "module": "nmap", "status": "running"}`) su `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`.
    - Al termine della scansione Nmap:
        - Parsa l'output XML di Nmap.
        - Invia i risultati parsati (in formato JSON) all'API Gateway (`INTERNAL_API_GATEWAY_URL`) 
    - Se tutte le operazioni hanno successo, pubblica uno stato finale `{"scan_id": X, "module": "nmap", "status": "completed"}` su `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`.
    - In caso di errori in qualsiasi fase, pubblica uno stato `{"scan_id": X, "module": "nmap", "status": "error", "error_details": "..."}` su `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`.

8. Il **Backend Consumer (Django REST Framework - Management Command `consume_scan_status`)**:
    - Ascolta sulla coda unificata `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`.
    - All'arrivo di un messaggio (JSON con `scan_id`, `module`, `status`, opzionalmente `message`, `error_details`):
        - Aggiorna il record `Scan` corrispondente nel database. Ad esempio, se `module` è "nmap" e `status` è "running", lo stato della scansione diventa "Nmap Scan Running". Se `status` è "completed", imposta `scan.completed_at` (per quel modulo/fase).
        - Se lo stato è "Failed", registra `error_details`.

9. Il **Backend Orchestratore (Django REST Framework)**:
    - Riceve i dati della scansione Nmap tramite API dal modulo Nmap.
    - Aggiorna il record della scansione nel **Database (PostgreSQL)** con i risultati di Nmap (es. `parsed_nmap_results`).
    - Dopo che il **Backend Consumer** ha aggiornato lo stato (es. a "Nmap Scan Completed") basandosi sui messaggi da `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`, l'Orchestratore (tramite un task periodico, un segnale Django o logica post-salvataggio del modello Scan) può:
        - Controllare se lo stato è "Nmap Scan Completed".
        - Decidere se avviare la fase successiva (es. Enum scan) in base ai plugin selezionati nel tipo di scansione. Se sì:
            - Prepara un messaggio JSON per il modulo Enum (contenente `scan_id`, `target_host`, e forse i risultati di Nmap).
            - Pubblica questo messaggio sulla coda `RABBITMQ_ENUM_SCAN_REQUEST_QUEUE`.

10. Il **modulo enum** rimane in ascolto sulla coda `RABBITMQ_ENUM_SCAN_REQUEST_QUEUE`, quando arriva un messaggio:
    - Avvia la scansione.
    - Pubblica aggiornamenti di stato (es. `{"scan_id": X, "module": "enum", "status": "running"}` e poi `{"scan_id": X, "module": "enum", "status": "completed"}` o `{"scan_id": X, "module": "enum", "status": "error"}`) su `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`.
    - Al termine, invia i risultati all'API Gateway (`PATCH /api/orchestrator/scans/{scan_id}/`).

11. si ripetono i punti dal 7. al 10. per tutti i plugin selezionati


12. Infine Il **modulo report generator** rimane in ascolto sulla coda `RABBITMQ_REPORT_REQUEST_QUEUE`:
    - Recupera tutti i dettagli della scansione tramite API.
    - Crea un report (es. PDF).
    - Comunica tramite API all'orchestratore la creazione del file (es. `PATCH /api/orchestrator/scans/{scan_id}/` con il path del report).
    - Pubblica uno stato `{"scan_id": X, "module": "report", "status": "completed"}` su `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`.

13. Il **Backend Orchestratore** (e **Backend Consumer**) aggiornano lo stato finale e collegano il report alla scansione.

Il **Backend Consumer** (`consume_scan_status`) è cruciale per aggiornare gli stati intermedi e finali dei vari moduli nel database, basandosi sui messaggi provenienti dalla coda unificata `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`.
L'Orchestratore si basa su questi stati aggiornati per decidere quando procedere alla fase successiva della pipeline di scansione.


