# **Integrazione dell'API Greenbone Community Edition con Vapter: Un Approccio Pythonico per Valutazioni Automatizzate delle Vulnerabilità**

## **I. Riepilogo Esecutivo**

Questo report delinea una metodologia robusta per integrare le capacità di scansione delle vulnerabilità di Greenbone Community Edition (GCE) nell'applicazione "Vapter". La soluzione proposta sfrutta la libreria ufficiale python-gvm e i Socket di Dominio Unix per consentire a Vapter di avviare, monitorare e recuperare programmaticamente i risultati delle scansioni GCE. Questa integrazione facilita un flusso di lavoro di valutazione post-Nmap senza interruzioni, migliorando la pipeline di valutazione automatizzata delle vulnerabilità di Vapter. La discussione enfatizza l'autenticazione sicura, la comunicazione inter-processo efficiente all'interno di ambienti Dockerizzati e le migliori pratiche per costruire un'integrazione ad alte prestazioni e manutenibile.


## **II. Fondamentali dell'Accesso all'API Greenbone**

### **Comprendere il Greenbone Management Protocol (GMP) e python-gvm**

Il Greenbone Vulnerability Manager Daemon (gvmd) funge da servizio di gestione centrale all'interno di Greenbone Community Edition, supervisionando le configurazioni di scansione, elaborando i risultati delle scansioni e gestendo le interazioni con gli utenti. L'accesso a gvmd è principalmente facilitato tramite il Greenbone Management Protocol (GMP) basato su XML. <sup>1</sup> Questo protocollo definisce la struttura per i comandi e le risposte scambiati tra i client e il servizio

gvmd, consentendo il controllo programmatico del sistema di gestione delle vulnerabilità. <sup>3</sup>

Per semplificare l'interazione con GMP, Greenbone fornisce python-gvm, una libreria API Python ufficiale. Questa libreria astrae le complessità della costruzione e dell'analisi dei messaggi XML grezzi, offrendo un'interfaccia programmatica di alto livello per gli sviluppatori. <sup>5</sup> L'utilizzo di

python-gvm semplifica significativamente lo sviluppo di script Python personalizzati per interagire con Greenbone, rendendolo lo strumento consigliato per applicazioni come Vapter. <sup>2</sup> Sebbene esistano strumenti da riga di comando come

gvm-cli per l'esecuzione diretta di comandi XML, python-gvm o gvm-pyshell sono esplicitamente indicati come più adatti per l'elaborazione dell'output XML all'interno degli script. <sup>2</sup> Questa preferenza deriva dai vantaggi intrinseci di una libreria Python nativa: elimina l'overhead associato all'avvio di nuovi processi shell, evita complesse sfide di shell escaping per i payload XML ed elimina la necessità per Vapter di analizzare manualmente le stringhe XML grezze dall'output standard. Invece,

python-gvm fornisce oggetti Python strutturati per richieste e risposte, insieme a una gestione degli errori integrata, portando a un'integrazione più robusta, manutenibile e pythonica. Questo approccio diretto offre un controllo più granulare e caratteristiche di prestazioni migliorate per un'applicazione automatizzata come Vapter.


### **Sfruttare i Socket di Dominio Unix per la Co-locazione Dockerizzata**

Per la comunicazione inter-processo (IPC) tra applicazioni che risiedono sulla stessa macchina, i socket di dominio Unix (AF_UNIX) offrono vantaggi distinti rispetto ai tradizionali socket di rete (TCP/IP). Sono esplicitamente raccomandati per la "comunicazione locale" all'interno dell'ecosistema Greenbone grazie alle loro prestazioni superiori e alla maggiore sicurezza. <sup>9</sup> Bypassando l'intero stack di rete — inclusi IP, TCP e overhead associati — i socket Unix forniscono un canale di comunicazione più veloce ed efficiente. Inoltre, l'accesso ai socket Unix è controllato dalle autorizzazioni standard del file system, che possono essere più granulari e sicure rispetto alle regole del firewall basate sulla rete. <sup>10</sup> Dato che sia Vapter che GCE sono Dockerizzati e co-locati sullo stesso server, i socket Unix rappresentano il meccanismo IPC ottimale per la loro interazione.

Il percorso canonico per il socket Unix di gvmd è tipicamente /run/gvmd/gvmd.sock. <sup>9</sup> Questo percorso di file specifico è fondamentale per stabilire una connessione da Vapter. Per consentire a Vapter di accedere a questo socket, la directory contenente

gvmd.sock deve essere condivisa tra il container GCE e il container Vapter utilizzando i volumi Docker. Ciò garantisce che il file socket, che è essenzialmente un file speciale sul file system, sia accessibile all'interno dello spazio dei nomi del file system del container Vapter.

L'implementazione di un volume Docker condiviso per il file gvmd.sock crea un canale di comunicazione diretto e ad alte prestazioni tra i container Vapter e GCE. Questo approccio aggira completamente lo stack di rete, eliminando la latenza di rete e semplificando le configurazioni del firewall inter-container. Sfrutta efficacemente il design fondamentale dei socket Unix per IPC locali altamente efficienti. Questa strategia richiede che il servizio gvmd all'interno del container Docker GCE sia configurato per posizionare il suo socket in una posizione sul file system dell'host che possa essere montata in modo coerente da altri container. Le configurazioni Docker Compose ufficiali di Greenbone gestiscono tipicamente questa configurazione, e la risoluzione dei problemi spesso comporta la verifica dell'esistenza del file gvmd.sock e il controllo dei log del container. <sup>13</sup>

Un frammento illustrativo di Docker Compose che dimostra questa configurazione del volume è il seguente:

```yaml
\# In GCE's docker-compose.yml (assicurati che gvmd.sock sia esposto a un percorso host)\
services:\
  gvmd:\
    volumes:\
      - /var/run/gvmd:/run/gvmd # Questa riga assicura che il socket sia su un percorso host accessibile da altri container\
\
\# In Vapter's docker-compose.yml\
services:\
  vapter:\
    build:.\
    volumes:\
      - /var/run/gvmd:/mnt/gce_sockets # Monta lo stesso percorso host nel container di Vapter\
    environment:\
      GCE_SOCKET_PATH: /mnt/gce_sockets/gvmd.sock # Variabile d'ambiente per l'app Vapter
```

Questa configurazione garantisce che Vapter possa accedere direttamente al file gvmd.sock al percorso specificato (/mnt/gce_sockets/gvmd.sock in questo esempio), facilitando una comunicazione senza interruzioni con il backend Greenbone.


## **III. Configurazione dell'Autenticazione API**

### **Creazione di un Utente API Dedicato in Greenbone**

Un aspetto fondamentale dell'integrazione con l'API di Greenbone è la comprensione del suo modello di autenticazione. L'API Greenbone Management Protocol (GMP) di Greenbone non utilizza un sistema di chiavi API separato. Si basa invece sugli _stessi account utente_ e sulle relative autorizzazioni utilizzate per l'interfaccia web di Greenbone Security Assistant (GSA). <sup>9</sup> L'autenticazione per l'accesso all'API viene eseguita direttamente utilizzando un nome utente e una password. <sup>5</sup>

Per la configurazione iniziale e la facilità d'uso, la creazione di un utente API dedicato tramite l'interfaccia web di Greenbone Security Assistant (GSA) è il metodo più semplice. Un amministratore può accedere a GSA, navigare in Administration > Users e creare un nuovo account utente fornendo un Login Name (ad esempio, vapter_api) e una Password robusta. <sup>16</sup>

Sebbene l'assegnazione del ruolo Admin fornisca pieno accesso e semplifichi l'integrazione iniziale, l'adesione al principio del minimo privilegio è fondamentale per un utente API dedicato in un ambiente di produzione. Questa pratica di sicurezza impone che un utente debba possedere solo le autorizzazioni minime necessarie per svolgere le sue funzioni previste. Per Vapter, ciò significa configurare un ruolo personalizzato con autorizzazioni specifiche come authenticate, get_settings e la capacità di create_target, create_task, start_task, get_tasks, get_reports, get_configs, get_scanners e get_port_lists. <sup>14</sup> Questo approccio riduce significativamente la superficie di attacco: se le credenziali di Vapter fossero mai compromesse, il potenziale danno sarebbe limitato strettamente all'ambito delle sue operazioni Greenbone autorizzate, piuttosto che concedere il pieno controllo amministrativo sull'istanza Greenbone. Inoltre, l'applicazione di restrizioni di

Host Access può limitare ulteriormente l'autorizzazione di Vapter a scansionare solo intervalli di destinazione specifici. <sup>16</sup>

In alternativa, se un utente amministratore esiste già, è possibile creare utenti aggiuntivi programmaticamente utilizzando gvm-cli, il che può essere utile per script di distribuzione automatizzati. <sup>15</sup> Un esempio di comando

gvm-cli per la creazione di un utente sarebbe:

```bash
gvm-cli --gmp-username admin --gmp-password <admin_password> \
socket --socketpath /run/gvmd/gvmd.sock \
--xml "<create_user><name>vapter_api</name><password>your_strong_password</password><role_ids><role id='<admin_role_uuid_or_custom_role_uuid>'/></role_ids></create_user>"
```

L'UUID per il ruolo desiderato (ad esempio, il ruolo 'Admin' o un ruolo personalizzato) dovrebbe essere recuperato in anticipo utilizzando gvm-cli --xml "<get_roles/>".


### **Autenticazione di python-gvm con Greenbone**

Una volta che l'oggetto UnixSocketConnection è istanziato e configurato per connettersi al percorso gvmd.sock, l'autenticazione con Greenbone viene eseguita utilizzando il metodo authenticate dell'oggetto GMP. <sup>5</sup>

Un aspetto cruciale per la costruzione di un client API affidabile e tollerante agli errori è l'uso di EtreeCheckCommandTransform durante l'inizializzazione dell'oggetto GMP. <sup>9</sup> Questa trasformazione convalida automaticamente lo stato di successo dei comandi GMP e solleva un'eccezione

GvmError in caso di fallimento. Questa segnalazione di errori immediata ed esplicita è vitale per un sistema automatizzato come Vapter, consentendogli di rilevare e reagire prontamente a errori di autenticazione o chiamate API non valide, piuttosto che fallire silenziosamente o tentare di analizzare risposte malformate. Trasforma anche la gestione delle stringhe XML grezze in un approccio più pythonico e orientato agli oggetti, rendendo le risposte più facili da gestire.

Un esempio di codice Python per stabilire una connessione autenticata:

```python

from gvm.connections import UnixSocketConnection
from gvm.protocols.gmp import GMP
from gvm.transforms import EtreeCheckCommandTransform
from gvm.errors import GvmError

# Assicurati che questo percorso corrisponda al percorso del volume montato all'interno del container Docker di Vapter
GCE_SOCKET_PATH = '/mnt/gce_sockets/gvmd.sock'
GCE_USERNAME = 'vapter_api' # L'utente Greenbone dedicato per Vapter
GCE_PASSWORD = 'your_secure_password' # La password per l'utente API di Vapter

try:
    connection = UnixSocketConnection(path=GCE_SOCKET_PATH)
    # Usa EtreeCheckCommandTransform per un'analisi XML robusta e una gestione degli errori integrata\
    with GMP(connection, transform=EtreeCheckCommandTransform()) as gmp:
        gmp.authenticate(GCE_USERNAME, GCE_PASSWORD)
        print(f"Autenticazione a Greenbone riuscita come {GCE_USERNAME}.")
        # Procedi con i passaggi di orchestrazione della scansione
except GvmError as e:
    print(f"Autenticazione API Greenbone fallita: {e}")
    # Implementa una gestione specifica degli errori per i problemi di autenticazione in Vapter
    raise # Rilancia o gestisci come appropriato per l'architettura di Vapter
except FileNotFoundError:
    print(f"Errore: Socket Greenbone non trovato in {GCE_SOCKET_PATH}. Assicurati che il volume sia montato correttamente e che GCE sia in esecuzione.")
    raise
except Exception as e:
    print(f"Si è verificato un errore imprevisto durante la connessione/autenticazione Greenbone: {e}")
    raise
```

## **IV. Orchestrazione delle Scansioni Greenbone da Vapter con python-gvm**

### **A. Panoramica del Flusso di Lavoro di Scansione**

L'integrazione tra Vapter e Greenbone è progettata come una sequenza logica di operazioni, attivata al completamento di una scansione Nmap. Questo flusso di lavoro garantisce che le valutazioni delle vulnerabilità siano avviate con parametri precisi e che i risultati siano recuperati in modo efficiente per l'elaborazione e l'analisi successive di Vapter.

Snippet di codice

graph TD
    A --> B;
    B --> C{Chiamate API Python-GVM tramite Socket Unix};
    C --> D\[Greenbone Community Edition (GCE)];
    D -- 1. Ottieni/Crea Target --> D;
    D -- 2. Ottieni/Crea Configurazione di Scansione --> D;
    D -- 3. Ottieni ID Scanner --> D;
    D -- 4. Crea Task di Scansione --> D;
    D -- 5. Avvia Task di Scansione --> D;
    D -- 6. Monitora Stato Scansione --> D;
    D -- 7. Recupera Report di Scansione --> E;


### **B. Implementazione Passo-Passo**

Questa sezione descrive in dettaglio le chiamate python-gvm principali necessarie per orchestrare una scansione Greenbone, dalla definizione del target al recupero del report.


#### **Stabilire la UnixSocketConnection**

Come discusso in precedenza nella sezione sull'autenticazione, la UnixSocketConnection è il componente fondamentale per comunicare con gvmd. Deve essere inizializzata con il percorso corretto al file gvmd.sock, che corrisponde al percorso del volume montato all'interno del container Docker di Vapter. <sup>5</sup> Questo oggetto di connessione, combinato con il gestore del protocollo

GMP, forma l'interfaccia per tutte le successive interazioni con l'API Greenbone. <sup>7</sup>


#### **Recupero degli ID Essenziali: Configurazioni di Scansione e Scanner**

L'API GMP di Greenbone richiede Universally Unique Identifiers (UUID) per le configurazioni di scansione, i target e gli scanner quando si creano nuovi task. <sup>8</sup> Sebbene gli UUID comuni possano essere codificati per semplicità, il loro recupero dinamico offre maggiore flessibilità e adattabilità a vari ambienti Greenbone o configurazioni personalizzate.

Per ottenere i profili di scansione disponibili, viene utilizzato il metodo gmp.get_scan_configs(). <sup>20</sup> La configurazione "Full and fast" è un'impostazione predefinita frequentemente utilizzata, nota per il suo UUID

daba56c8-73ec-11df-a475-002264764cea. <sup>8</sup> Allo stesso modo,

gmp.get_scanners() elenca gli scanner disponibili. <sup>7</sup> Lo scanner "OpenVAS Default", con UUID

08b69003-5fc2-4037-a479-93b440211c73, è la scelta standard per la scansione delle vulnerabilità. <sup>8</sup>

Per una prototipazione rapida e un'integrazione iniziale, le seguenti tabelle forniscono UUID immediati e utilizzabili per i profili di scansione e gli scanner comunemente usati. Sebbene la scoperta dinamica sia raccomandata per i sistemi di produzione per garantire l'adattabilità, questi valori predefiniti servono come ottimi punti di partenza per lo sviluppo.

**Tabella: ID Comuni delle Configurazioni di Scansione Greenbone**

|                |                                      |                                                                                          |
| -------------- | ------------------------------------ | ---------------------------------------------------------------------------------------- |
| Nome           | UUID                                 | Descrizione                                                                              |
| Full and fast  | daba56c8-73ec-11df-a475-002264764cea | La maggior parte degli NVT; ottimizzata utilizzando informazioni raccolte in precedenza. |
| Host Discovery | 2d3f051c-55ba-11e3-bf43-406186ea4fc5 | Configurazione di scansione per la scoperta di host di rete.                             |
| Discovery      | 8715c877-47a0-438d-98a3-27c7a6ab2196 | Configurazione di scansione per la scoperta di rete.                                     |
| Empty          | 085569ce-73ed-11df-83c3-002264764cea | Modello di configurazione vuoto e statico.                                               |

**Tabella: ID Comuni degli Scanner Greenbone**

|                 |                                      |
| --------------- | ------------------------------------ |
| Nome            | UUID                                 |
| OpenVAS Default | 08b69003-5fc2-4037-a479-93b440211c73 |
| CVE             | 6acd0832-df90-11e4-b9d5-28d24461215b |

Un esempio di codice per il recupero dinamico di questi ID è fornito di seguito:

```python
import xml.etree.ElementTree as ET

# Assumendo che 'gmp' sia un oggetto GMP autenticato dai passaggi precedenti

# Ottieni Configurazioni di Scansione
print("Recupero delle Configurazioni di Scansione disponibili...")
scan_configs_response_xml = gmp.get_scan_configs()
config_map = {config.findtext('name'): config.get('id') 
              for config in scan_configs_response_xml.xpath('//config')}
print("Configurazioni di Scansione disponibili:", config_map)

# Ottieni Scanner
print("\nRecupero degli Scanner disponibili...")
scanners_response_xml = gmp.get_scanners()
scanner_map = {scanner.findtext('name'): scanner.get('id') 
               for scanner in scanners_response_xml.xpath('//scanner')}
print("Scanner disponibili:", scanner_map)

# Esempio: Recupera in modo sicuro gli ID comuni
full_and_fast_config_id = config_map.get('Full and fast')
openvas_scanner_id = scanner_map.get('OpenVAS Default')

if not full_and_fast_config_id:
    print("Avviso: Configurazione di scansione 'Full and fast' non trovata. Controlla la configurazione GCE.")
if not openvas_scanner_id:
    print("Avviso: Scanner 'OpenVAS Default' non trovato. Controlla la configurazione GCE.")
```

#### **Creazione di un Target di Scansione**

Un target in Greenbone definisce gli host o gli indirizzi IP che saranno soggetti alla scansione delle vulnerabilità. <sup>12</sup> Vapter utilizzerà il metodo

gmp.create_target(name, hosts, port_list_id) per definire il target per la scansione. <sup>8</sup> È importante notare che i nomi dei target devono essere unici all'interno di Greenbone. L'aggiunta di un timestamp (ad esempio, in formato ISO 8601) al nome del target è una pratica robusta per garantirne l'unicità, specialmente in un sistema automatizzato come Vapter che potrebbe avviare numerose scansioni. <sup>8</sup>

Il port_list_id è un parametro obbligatorio che specifica quali porte Greenbone dovrebbe scansionare sul target. I valori comuni di port_list_id includono "All IANA assigned TCP and UDP" (4a4717fe-57d2-11e1-9a26-406186ea4fc5) o "All TCP and Nmap top 100 UDP" (730ef368-57e2-11e1-a90f-406186ea4fc5). <sup>12</sup> Questi possono anche essere recuperati dinamicamente tramite

gmp.get_port_lists().

```python
import datetime

# Assumendo che 'gmp' sia un oggetto GMP autenticato
# Sostituisci con l'indirizzo IP effettivo ottenuto da Nmap
target_ip_from_nmap = "192.168.1.100" 

target_name = f"Vapter Scan Target - {target_ip_from_nmap} - {datetime.datetime.now().isoformat()}"

# Utilizzo di un ID di lista porte comune per dimostrazione (Tutte le porte TCP e UDP assegnate da IANA)
all_tcp_udp_port_list_id = '4a4717fe-57d2-11e1-9a26-406186ea4fc5' 

print(f"\nCreazione del target per {target_ip_from_nmap}...")
target_response = gmp.create_target(name=target_name, hosts=[target_ip_from_nmap], port_list_id=all_tcp_udp_port_list_id)
target_id = target_response.get('id') # Estrai l'UUID dalla risposta
print(f"Target '{target_name}' creato con successo con ID: {target_id}")
```

#### **Creazione di un Task di Scansione**

Un task di scansione è l'entità centrale che unisce un target specifico, una configurazione di scansione scelta e uno scanner per definire un lavoro completo di valutazione delle vulnerabilità all'interno di Greenbone. <sup>8</sup> Vapter utilizzerà il metodo

gmp.create_task(name, config_id, target_id, scanner_id, comment=None) per definire questo lavoro. <sup>8</sup> Il

config_id e lo scanner_id dovrebbero essere ottenuti dai passaggi precedenti (UUID comuni codificati o recuperati dinamicamente), e il target_id è l'UUID del target appena creato.


```python
# Assumendo che 'gmp', 'target_id', 'full_and_fast_config_id', 'openvas_scanner_id' siano disponibili

task_name = f"Vapter Automated Scan for {target_ip_from_nmap} - {datetime.datetime.now().isoformat()}"
task_comment = "Scansione automatizzata delle vulnerabilità avviata da Vapter dopo il completamento di Nmap."

print(f"\nCreazione del task di scansione '{task_name}'...")
task_response = gmp.create_task(
    name=task_name,
    config_id=full_and_fast_config_id,
    target_id=target_id,
    scanner_id=openvas_scanner_id,
    comment=task_comment
)
task_id = task_response.get('id') # Estrai l'UUID dalla risposta
print(f"Task '{task_name}' creato con successo con ID: {task_id}")
```

#### **Avvio del Task di Scansione**

L'avvio del processo di valutazione delle vulnerabilità all'interno di Greenbone si ottiene avviando il task di scansione creato. <sup>8</sup> Vapter utilizzerà il metodo

gmp.start_task(task_id) a questo scopo. <sup>7</sup> La risposta a questo comando è fondamentale, poiché contiene il
report_id, che è un identificatore univoco per i risultati della scansione. Questo report_id sarà essenziale per monitorare l'avanzamento della scansione e recuperare il report finale una volta completata la valutazione. <sup>7</sup>


```python
# Assumendo che 'gmp' e 'task_id' siano disponibili

print(f"\nAvvio del task di scansione {task_id}...")
start_response = gmp.start_task(task_id)
report_id = start_response.find('report_id').text # Estrai report_id dall'elemento XML
print(f"Task di scansione {task_id} avviato. ID Report associato: {report_id}")
```

#### **Monitoraggio dello Stato della Scansione**

Dopo aver avviato una scansione, Vapter deve monitorarne l'avanzamento per determinare quando si completa o incontra un problema. Ciò si ottiene tipicamente interrogando periodicamente Greenbone per lo stato del task. <sup>2</sup> Il metodo

gmp.get_tasks(task_id=task_id) viene utilizzato per recuperare lo stato dettagliato di un task specifico. <sup>9</sup> La risposta XML restituita conterrà un tag

<status> (ad esempio, "Running", "Done", "Stopped", "Interrupted", "Failed") e un tag <progress> che indica la percentuale di completamento. <sup>2</sup>

Dato il ruolo di Vapter come strumento di automazione, l'efficienza di questo meccanismo di polling è importante. Sebbene il polling sia il metodo diretto e supportato per monitorare lo stato della scansione tramite GMP, Vapter dovrebbe implementare un intervallo di polling strategico per evitare un consumo eccessivo di risorse sia su Vapter che su GCE. Per un'applicazione di livello produttivo, il polling ogni pochi secondi potrebbe essere troppo aggressivo per scansioni a lungo termine. Una strategia di backoff esponenziale o un intervallo fisso e ragionevole (ad esempio, ogni 30-60 secondi) è più appropriato. Il GMP di Greenbone non supporta nativamente webhook o callback per il completamento della scansione, rendendo il polling il metodo di fatto per gli aggiornamenti di stato.

```python
import time

# Assumendo che 'gmp' e 'task_id' siano disponibili

print(f"\nMonitoraggio dello stato della scansione per il task {task_id}...")
while True:
    task_status_response = gmp.get_tasks(task_id=task_id)
    # Usa xpath per estrarre in modo affidabile gli elementi dall'oggetto etree
    status_element = task_status_response.xpath('//task/status/text()')
    current_status = status_element if status_element else 'Unknown'
    
    progress_element = task_status_response.xpath('//task/progress/text()')
    current_progress = progress_element if progress_element else '0'

    print(f"Stato del Task {task_id}: {current_status}, Progresso: {current_progress}%")

    if current_status == 'Done':
        print("Scansione Greenbone completata con successo.")
        break
    elif current_status in:
        print(f"Scansione Greenbone terminata con stato: {current_status}. Potrebbe essere necessaria un'ulteriore indagine.")
        break
    
    time.sleep(30) # Esegui il polling ogni 30 secondi per evitare un carico eccessivo
```

#### **Recupero dei Report di Scansione**

Una volta che il task di scansione raggiunge lo stato "Done", il report completo delle vulnerabilità può essere recuperato utilizzando il report_id ottenuto durante l'avvio del task. Vapter utilizzerà il metodo gmp.get_report(report_id, report_format_id=None, details=True) a questo scopo. <sup>17</sup>

Per recuperare il report in un formato specifico (ad esempio, PDF), è necessario specificare il report_format_id. L'UUID per i report PDF è c402cc3e-b531-11e1-9163-406186ea4fc5. <sup>23</sup> Se non viene specificato alcun

report_format_id, viene tipicamente restituito il report XML predefinito. I report, specialmente i formati binari come il PDF, vengono spesso restituiti come contenuto codificato in base64 all'interno della risposta XML, richiedendo la decodifica dopo il recupero. <sup>23</sup>

**Esempio di Codice (Recupero e Analisi del Report XML):**

```python
import xmltodict
import xml.etree.ElementTree as ET

# Assumendo che 'gmp', 'report_id' e 'target_ip_from_nmap' siano disponibili

print(f"\nRecupero del report XML {report_id}...")
xml_report_response = gmp.get_report(report_id=report_id, details=True)

# Converti l'oggetto ElementTree in una stringa per l'analisi di xmltodict
report_xml_string = ET.tostring(xml_report_response, encoding='unicode')
report_dict = xmltodict.parse(report_xml_string)

# Esempio: Estrazione dei risultati [24]
# Il percorso esatto potrebbe variare leggermente in base alla versione GCE e al contenuto del report
results = report_dict.get('get_reports_response', {}).get('report', {}).get('report', {}).get('results', {}).get('result')
if results is None:
    results = # Assicurati che results sia una lista anche se non ci sono risultati
elif not isinstance(results, list):
    results = [results] # Se c'è un solo risultato, xmltodict potrebbe non restituire una lista

print(f"Il report per {target_ip_from_nmap} contiene {len(results)} risultati.")

# Salva il report XML grezzo per l'elaborazione interna o l'archiviazione di Vapter
xml_output_filename = f"greenbone_report_{target_ip_from_nmap}_{report_id}.xml"
with open(xml_output_filename, "w", encoding="utf-8") as f:
    f.write(report_xml_string)
print(f"Report XML salvato in {xml_output_filename}")
```

**Esempio di Codice (Recupero del Report PDF):**

```python
from base64 import b64decode
from pathlib import Path

# Assumendo che 'gmp', 'report_id' e 'target_ip_from_nmap' siano disponibili

pdf_report_format_id = "c402cc3e-b531-11e1-9163-406186ea4fc5" # UUID standard per il formato report PDF
pdf_output_filename = f"greenbone_report_{target_ip_from_nmap}_{report_id}.pdf"

print(f"\nRecupero del report PDF {report_id}...")
pdf_report_response = gmp.get_report(
    report_id=report_id, 
    report_format_id=pdf_report_format_id, 
    ignore_pagination=True, # Assicurati che venga restituito il contenuto completo del report
    details=True # Richiedi informazioni aggiuntive sul report
)

report_element = pdf_report_response.find("report")
# Il contenuto codificato in base64 è tipicamente nella 'coda' dell'elemento 'report_format'
content_b64 = report_element.find("report_format").tail 

if not content_b64:
    print("Avviso: Il report PDF richiesto è vuoto o la generazione è fallita all'interno di Greenbone.")
else:
    binary_base64_encoded_pdf = content_b64.encode("ascii")
    binary_pdf = b64decode(binary_base64_encoded_pdf)
    pdf_path = Path(pdf_output_filename).expanduser()
    pdf_path.write_bytes(binary_pdf)
    print(f"Report PDF salvato con successo in {pdf_path}")
```

## **V. Migliori Pratiche e Considerazioni Avanzate**


### **Gestione Robusta degli Errori e Logging**

L'implementazione di una gestione completa degli errori è cruciale per qualsiasi applicazione di livello produttivo. Vapter dovrebbe racchiudere tutte le chiamate API python-gvm all'interno di blocchi try-except GvmError. <sup>9</sup> Come notato in precedenza, l'utilizzo di

EtreeCheckCommandTransform garantisce che le eccezioni GvmError vengano automaticamente sollevate per i fallimenti dell'API, semplificando significativamente il rilevamento degli errori e consentendo a Vapter di reagire programmaticamente a problemi come problemi di connettività, errori di autenticazione o parametri di comando non validi.

Inoltre, l'utilizzo del modulo logging standard di Python è essenziale per un output dettagliato di debug e informazioni. <sup>9</sup> In un ambiente Dockerizzato, dove l'accesso diretto alla console di un container in esecuzione potrebbe essere limitato, il logging completo e strutturato diventa il meccanismo primario e più efficace per diagnosticare i problemi operativi. Combinato con il monitoraggio dei log del container GCE (

docker compose logs -f può essere utile per i problemi lato GCE <sup>13</sup>), il logging fornisce una traccia di audit inestimabile per la risoluzione dei problemi di connettività (ad esempio, percorsi socket errati, problemi di autorizzazione), errori di autenticazione o risposte API inattese. Il logging proattivo e dettagliato riduce al minimo il tempo necessario per identificare e risolvere i problemi relativi all'interazione con l'API Greenbone, il che è fondamentale per mantenere l'affidabilità del flusso di lavoro automatizzato di Vapter.


### **Gestione Asincrona delle Scansioni**

Vapter è progettato per gestire valutazioni delle vulnerabilità, che spesso coinvolgono processi a lungo termine, in particolare per le scansioni Greenbone che possono richiedere da minuti a ore per essere completate. L'avvio e il monitoraggio di queste scansioni in modo sincrono bloccherebbe il thread principale dell'applicazione Vapter, portando a una mancanza di reattività e a una scalabilità limitata.

Per mantenere la reattività e consentire l'elaborazione parallela, Vapter dovrebbe implementare modelli di programmazione asincrona (ad esempio, asyncio di Python per I/O non bloccante) o integrare una coda di task distribuita. Dato che Vapter utilizza già RabbitMQ per Nmap, estendere questa infrastruttura esistente per scaricare l'avvio delle scansioni Greenbone e il polling dello stato a worker in background (ad esempio, utilizzando Celery) è un'estensione architetturale logica. Questo design consente a Vapter di elaborare in modo efficiente i nuovi risultati delle scansioni Nmap, avviare le successive scansioni Greenbone e gestire altra logica applicativa senza diventare non responsivo o bloccato da operazioni di lunga durata. Questa considerazione architetturale è vitale per la scalabilità a lungo termine e l'esperienza utente di Vapter, garantendo che possa gestire efficacemente più valutazioni di vulnerabilità concorrenti.


### **Migliori Pratiche di Sicurezza per le Credenziali API**

Come strumento di valutazione delle vulnerabilità, Vapter stesso deve aderire a pratiche di sicurezza esemplari. Una vulnerabilità di sicurezza critica deriva dalla codifica delle credenziali API di Greenbone (nome utente e password) direttamente nel codice sorgente di Vapter. Questa pratica espone informazioni sensibili e può portare a compromissione se il codice o l'immagine del container vengono accessi.

Invece, Vapter dovrebbe sfruttare pratiche di gestione sicura delle credenziali. Ciò include il passaggio delle credenziali come variabili d'ambiente al container Docker di Vapter in fase di runtime. Per una sicurezza più robusta in orchestrazioni come Docker Swarm o Kubernetes, si raccomanda l'utilizzo di Docker Secrets o Kubernetes Secrets per iniettare le credenziali in modo sicuro senza esporle in testo in chiaro all'interno di file di configurazione o immagini di container. Per distribuzioni di livello enterprise, l'integrazione con un sistema di gestione dei segreti dedicato come HashiCorp Vault fornisce un livello di sicurezza ancora più elevato. Oltre alla gestione delle credenziali, è anche essenziale garantire che il file del socket Unix (gvmd.sock) sul file system dell'host abbia le autorizzazioni appropriate (ad esempio, di proprietà dell'utente/gruppo gvm, con accesso minimo di lettura/scrittura per altri utenti) per prevenire l'accesso non autorizzato da altri processi o container sull'host. Sebbene la configurazione Docker Compose predefinita di Greenbone gestisca tipicamente questo in modo sicuro, la verifica è un passo prudente. Queste pratiche proteggono l'istanza Greenbone dall'accesso non autorizzato anche se il container o l'host di Vapter vengono compromessi.


### **Compatibilità della Versione di python-gvm e GCE**

La libreria python-gvm è in fase di sviluppo attivo e ha requisiti specifici di compatibilità di versione con diverse versioni del Greenbone Management Protocol (GMP). <sup>5</sup> Ad esempio, le versioni di

python-gvm precedenti alla 21.5 sono richieste per le versioni GMP 7, 8 o 9, e le versioni precedenti alla 24.6 per GMP 20.8 o 21.4.

Le discrepanze tra la versione della libreria python-gvm utilizzata da Vapter e la versione del backend gvmd in GCE possono portare a comportamenti API inattesi, errori criptici o persino a interruzioni funzionali. Per mitigare ciò, è fondamentale consultare sempre la documentazione ufficiale di python-gvm (<https://greenbone.github.io/python-gvm/>) per la matrice di compatibilità più recente. Fissare la versione di python-gvm nel requirements.txt di Vapter (ad esempio, python-gvm==X.Y.Z) è una buona pratica per garantire un comportamento coerente tra le distribuzioni e per prevenire problemi derivanti da conflitti di dipendenza. La gestione e la verifica proattiva della compatibilità di python-gvm con la specifica distribuzione GCE garantiscono la stabilità e l'affidabilità di Vapter.


## **VI. Conclusione e Raccomandazioni**

Sfruttando strategicamente python-gvm e i Socket di Dominio Unix, Vapter può integrare senza problemi Greenbone Community Edition nel suo flusso di lavoro di valutazione delle vulnerabilità. Questo approccio fornisce un'interfaccia ad alte prestazioni, sicura e programmatica per orchestrare le scansioni GCE, estendendo efficacemente le capacità di Vapter oltre Nmap per valutazioni di sicurezza complete. L'uso dei socket Unix è ottimale per i container Docker co-locati, garantendo una comunicazione inter-processo efficiente e sicura.

Per migliorare ulteriormente le capacità di valutazione delle vulnerabilità di Vapter e consolidare la sua posizione come strumento di sicurezza robusto, si raccomandano i seguenti miglioramenti futuri:

- **Analisi e Parsing Automatizzato dei Report:** Oltre a semplicemente recuperare i report grezzi, Vapter potrebbe implementare un parsing avanzato dei report XML (utilizzando xml.etree.ElementTree o xmltodict <sup>24</sup>) per estrarre risultati specifici, categorizzare le vulnerabilità, prioritizzare i rischi e integrarli direttamente nel modello di dati interno di Vapter o in una dashboard di reporting centralizzata. Ciò trasformerebbe i dati grezzi delle scansioni in intelligence azionabile.

- **Gestione Personalizzata delle Configurazioni di Scansione:** Consenti agli utenti di Vapter di definire e gestire configurazioni di scansione Greenbone personalizzate direttamente tramite l'interfaccia utente di Vapter. Vapter potrebbe quindi utilizzare gmp.create_scan_config() o gmp.clone_scan_config() <sup>17</sup> per il provisioning di queste configurazioni all'interno di GCE, offrendo maggiore flessibilità e personalizzazione delle valutazioni delle vulnerabilità.

- **Gestione delle Credenziali di Scansione Autenticate:** Implementa un meccanismo sicuro all'interno di Vapter per gestire e fornire credenziali (ad esempio, SSH, SMB, login di applicazioni web) all'interno di Greenbone per scansioni autenticate. Ciò comporterebbe l'utilizzo di gmp.create_credential() <sup>17</sup> per consentire valutazioni delle vulnerabilità più approfondite e accurate dei sistemi target, che spesso richiedono accesso privilegiato.

- **API per Altre Entità Greenbone:** Estendi il controllo programmatico di Vapter per gestire altre entità Greenbone come utenti, ruoli, avvisi e filtri utilizzando la ricca API GMP. <sup>17</sup> Ciò potrebbe consentire a Vapter di automatizzare le attività di amministrazione di Greenbone, semplificando ulteriormente il processo complessivo di gestione della sicurezza.

- **Integrazione Migliorata dell'Interfaccia Utente:** Visualizza in tempo reale l'avanzamento delle scansioni Greenbone, i risultati dettagliati e i report generati direttamente nell'interfaccia utente di Vapter. Ciò fornirebbe un'esperienza unificata e intuitiva per la gestione delle vulnerabilità, offrendo agli utenti un unico pannello di controllo per le loro attività di valutazione.