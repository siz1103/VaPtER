## **Ordine di Sviluppo Consigliato (Fasi Incrementali)**

Per procedere con lo sviluppo un componente alla volta, si suggerisce il seguente ordine:

### **Fase 1: Fondamenta e Gestione Target **

L'obiettivo è avere una base dati e un'interfaccia utente minima per gestire i target e predisporre l'avvio  delle scansioni.

1. **Database (PostgreSQL):**

- Definire lo schema iniziale per le tabelle chiave: 
    - Customer (dettagli del customer, ogni istanza successiva, target, scan, ecc dovrà fare riferimento ad un customer, esclusi scantype e portlist che saranno globali )
    - Target (per gli host da scansionare)
        * id (AutoField PK)
        * name (CharField 255)
        * address (CharField 50 unique)
        * description (TextField null)
        * created_at (DateTimeField auto_now_add)
        * updated_at (DateTimeField auto_now)
    - Port_List (Elenco di porte)
        * id (AutoField PK)
        * name (CharField 50)
        * tcp_ports (TextField null)
        * udp_ports (TextField null)
        * description (TextField null)
    - ScanType (Tipologia di scansioni)
        * id (AutoField PK)
        * name (CharField 50)
        * only_discovery (BooleanField default false)
        * consider_alive (BooleanField default false)
        * be_quiet (BooleanField default false)
        * port_list ForeignKey(Port_List, on_delete=models.SET_NULL, null=True, blank=True)
        * plugin_finger (BooleanField default false)
        * plugin_enum (BooleanField default false)
        * plugin_web (BooleanField default false)
        * plugin_vuln_lookup (BooleanField default false)
        * description (TextField null)
    - Scan (scansione)
        * id (AutoField PK)
        * target_id ForeignKey(Target, on_delete=models.CASCADE)
        * scan_type_id ForeignKey(ScanType, on_delete=models.CASCADE)
        * status (CharField 50 choices=STATUS_CHOICES, default='Pending')
        * initiated_at (DateTimeField auto_now_add)
        * started_at (DateTimeField)
        * completed_at (DateTimeField)
        * parsed_nmap_results (JSONField)
        * error_message (TextField)
        STATUS_CHOICES = [
            ('Pending', 'Pending'),
            ('Queued', 'Queued'),
            ('Nmap Scan Running', 'Nmap Scan Running'),
            ('Nmap Scan Completed', 'Nmap Scan Completed'),
            ('Finger Scan Running', 'Finger Scan Running'),
            ('Finger Scan Completed', 'Finger Scan Completed'),
            ('Enum Scan Running', 'Enum Scan Running'),
            ('Enum Scan Completed', 'Enum Scan Completed'),
            ('Web Scan Running', 'Web Scan Running'),
            ('Web Scan Completed', 'Web Scan Completed'),
            ('Vuln Lookup Running', 'Vuln Lookup Running'),
            ('Completed', 'Completed'),
            ('Failed', 'Failed'),
        ]
    - Scan_detail (dettagli aggiuntivi legati ai singoli scan, tipo cve, vulnerabilità ,ecc )
    - VulnerabilityDefinitions (per i dettagli delle CVE) **Da implementare successivamente**
    - DetectedVulnerabilities (per le occorrenze specifiche delle vulnerabilità dei vari target). **Da implementare successivamente**


2. **Backend Orchestratore (Django REST Framework):**

- Implementare i modelli Django corrispondenti alle tabelle del database.
- Creare le API REST per le operazioni CRUD (Create, Read, Update, Delete) per l'inserimento dei dati.
- Creare un'API per recuperare lo stato e i risultati delle scansioni (inizialmente vuoti o con solo lo stato).

3. **API Gateway (FastAPI):**

- Configurare FastAPI per instradare le richieste dal frontend alle API del Backend Orchestratore.

4. **Frontend :**

- prima di tutto decidere il framework da utilizzare
- Creare l'interfaccia utente base per aggiungere i dati e avviare le prime scansioni
- Aggiungere un menù a tendina che elenchi i customer e permetta di crearne di nuovi.
- I dati nelle pagine target e scansioni dovranno mostrare solo i dati dello specifico customer selezionato
- Fornire un'interfaccia per avviare una scansione selezionando un target precedentemente aggiunto e un tipo di scansione.
- Creare una pagina per visualizzare l'elenco delle scansioni avviate e il loro stato.

### **Fase 2: Code RabbitMQ, API, modulo NMAP e prime scansioni base**

L'obiettivo è rendere le scansioni effettive e visualizzare i risultati.

1. **Coda di Messaggi (RabbitMQ):**

- Installare e configurare RabbitMQ. Può essere eseguito in un container Docker separato. 

2. **Backend Orchestratore (Django REST Framework) - Integrazione RabbitMQ:**

- Modificare l'API "Avvia Scansione":
    - Dopo aver creato il record di scansione nel DB con stato "Pending":
    - Pubblica un messaggio JSON sulla coda RabbitMQ `nmap_scan_requests`. Il messaggio contiene: `scan_id`, `target_id`, `target_address`, `scan_type_id`.
    - Se la pubblicazione ha successo, aggiorna lo stato della scansione a "Queued".
    - Se la pubblicazione fallisce, aggiorna lo stato a "Failed" e registra un errore.

- Implementare un consumer nel Backend (es. come comando di gestione Django):
    - Si connette a RabbitMQ e rimane in ascolto sulla coda unificata `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`. (Implementato ad esempio tramite il comando `python manage.py consume_scan_status`)
    - All'arrivo di un messaggio (JSON atteso con `scan_id`, `module`, `status`, `message`, `error_details`, `timestamp`):
        - Aggiorna il record `Scan` corrispondente nel database con il nuovo stato e/o logga i dettagli.
        - Potrebbe anche avviare la fase successiva della scansione se lo stato indica il completamento di un modulo.
        - Gestisce i messaggi di acknowledge/not acknowledge (ack/nack) per RabbitMQ.

3. **Modulo Scanner Nmap (Dockerizzato in `plugins/nmap_scanner`):**

- Creare un Dockerfile per il container Nmap (basato su `kalilinux/kali-rolling`).

- Scrivere lo script Python (`nmap_scanner.py`) che:
    - Si connette a RabbitMQ.
    - Consuma messaggi dalla coda `RABBITMQ_NMAP_SCAN_REQUEST_QUEUE` (contenenti `scan_id`, `scan_type_id`, `target_host`).
    - Esegue Nmap sul target in base alla scansione scelta.
    - Pubblica aggiornamenti di stato (es. "running", "parsing", "completed", "error") sulla coda `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE`.
    - Parsa l'output XML di Nmap.
    - Invia i risultati parsati (JSON) tramite API Gateway al backend. 


4. **Backend Orchestratore (Django REST Framework) - Gestione Risultati e Flusso:**

- tramite API riceve i risultati dai moduli scanner (es. Nmap) e li salva nel record `Scan` appropriato (es. nel campo `parsed_nmap_results`).
- Il consumer che ascolta `RABBITMQ_SCAN_STATUS_UPDATE_QUEUE` aggiorna lo stato della scansione nel database in base ai messaggi ricevuti. Quando un modulo (es. Nmap) riporta "completed" (e i risultati sono stati salvati), nel caso lo stato sia completed aggiorna anche la data di completamento.


### **Fase 4: Analisi scansione e prima organizzazione dei risultati**

1. **backend - organizzazione dati scansione :**
- Il backend una volta ricevuti i dati della scansione completa nmap li salva nella tabella Scan, in particolar modo nella colonna parsed_nmap_results, contestualmente dovrebbe fare anche queste operazioni:
1) parsare le porte aperte rilevate e le eventuali app e versioni e salvarle nella tabella Scan_details, colonna open_ports, così da poterle riutilizzare negli altri moduli
2) salvare la versione del sistema operativo nella tabella Scan_details colonna os_guess, confrontando i dati più rilevanti della scansione e integrandoli anche con eventuali riscontri trovati negli altri punti della scansione
3) salvare le eventuali vulnerabilità trovate nella tabella Vulnerability_details 

2. **Frontend - Pubblicazione su frontend:**
- Il frontend nella lista dei target dovrà mostrare un pulsante dettagli, che se cliccato apra una nuova pagina in cui verranno mostrati:
1) nome target
2) indirizzo target
3) probabile sistema operativo
4) lista porte con applicazione e versione se rilevate
5) lista vulnerabilità (per ora solo il nome, poi integreremo il vulnerability lookup e miglioreremo questi dati)

3. **Frontend/backend - Creazione porte e scansioni statiche iniziale:**
- Creare tre liste di porte base, già presenti all'avvio del sistema, utilizzabili da subito (prendiamo esempio da quelle openvas):
1) All IANA assigned TCP
2) All IANA assigned TCP and UDP
3) All TCP and Nmap top 100 UDP
- Creare tre tipi di scansioni base, già presenti all'avvio del sistema, utilizzabili da subito:
1) Discovery -> scansione veloce che stabilisce se il target è alive, in sostanza quella lanciata col flag discovery_only
2) Scan Base -> scansione più approfondita testando il gruppo di porte All IANA assigned TCP and UDP
3) Scan Completo -> scansione approfondita con finger versioni app e SO, script ecc utilizzando le porte All TCP and Nmap top 100 UDP

### **Fase 5: Implementazione plugin**

1. **FingerprintX :**
- Implementiamo il plugin FingerprintX, github di riferimento https://github.com/praetorian-inc/fingerprintx.
Suddividiamo l'implementazione in più fasi
1) aggiunta flag su scan type e relativa implementazione sui models
2) implementazione coda rabbitmq e logica di avvio sul backend
3) creazione docker, basandosi sul plugins nmap_scanner, riciclare quanto possibile, stampa iniziale del risultato sui log, senza ulteriori attività
4) creazione API per il salvataggio dei dati e aggiornamento stato su coda rabbit

