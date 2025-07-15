# VaPtER
Tool di vulnerability assessment

# **README: Piattaforma di Vulnerability Assessment Basata su Docker**


## ** Obiettivo del Progetto**

Sviluppare una piattaforma di Vulnerability Assessment personalizzata, basata su Docker. L'obiettivo dell'app è eseguire  **scansione di host** (identificazione di porte, servizi, versioni software) e sulla **ricerca delle vulnerabilità note** associate a tali servizi.


## Note implementative

1. **Models**: Tutti i models hanno validazioni appropriate e relazioni corrette
2. **API**: Endpoint RESTful completi con filtri e paginazione
3. **RabbitMQ**: Consumer pronto per ricevere aggiornamenti dai moduli scanner
4. **Logging**: Sistema di logging configurato per debugging e monitoraggio
5. **Cache**: Supporto per Redis in produzione, memoria locale in sviluppo
6. **Sicurezza**: Configurazioni di sicurezza per ambiente di produzione (da implementare in una fase successiva)


## **Considerazioni Aggiuntive per lo Sviluppo**

- **Dockerizzazione:** Ogni componente deve essere containerizzato.

- **Comunicazione Asincrona:** Utilizza RabbitMQ per la comunicazione tra l'Orchestratore e i moduli scanner. 

- **Gestione Segreti:** Non hardcodare credenziali (API keys, password del database, credenziali di scansione) direttamente nel codice o nelle immagini Docker. Prevedi l'uso di variabili d'ambiente o strumenti dedicati come Docker Secrets (se usi Docker Swarm) o HashiCorp Vault per iniettarle in modo sicuro a runtime.

- **Error Handling:** Implementa una robusta gestione degli errori, specialmente per le chiamate API esterne (es. NVD API rate limits, JSON parsing errors).

- **Logging:** Assicurati che ogni servizio produca log significativi per il debugging e il monitoraggio.

- **Sicurezza dei Container:** Applica le best practice Docker: usa immagini base minimali e fidate, esegui i container con il principio del minimo privilegio (non-root user, --cap-drop all e --cap-add solo le necessarie), imposta filesystem di sola lettura (--read-only) e configura la rete per isolare i container (--network custom). 

- **Orchestrazione per la Produzione:** Per un ambiente di produzione, dove scalabilità orizzontale, resilienza e alta disponibilità sono critiche, un orchestratore di container come Kubernetes o Docker Swarm sarà essenziale. Pianifica la transizione da Docker Compose a uno di questi strumenti.