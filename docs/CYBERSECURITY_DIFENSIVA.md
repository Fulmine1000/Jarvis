# Cybersecurity difensiva di Jarvis

Jarvis offre una raccolta locale di controlli di sicurezza in sola lettura. Le funzioni sono pensate per il Mac personale e per sistemi sui quali l'utente ha autorizzazione.

## Comandi

| Comando | Cosa controlla | Effetti |
|---|---|---|
| `stato cybersecurity` | Capacità disponibili e limiti | Nessuno |
| `controlla sicurezza mac` | Firewall applicazioni, FileVault, Gatekeeper, SIP | Legge lo stato; non cambia impostazioni |
| `analizza la mia rete` | Nome host, IP locali e interfacce | Nessun pacchetto inviato |
| `controlla processi e servizi` | Metadati processi e socket locali in ascolto | Non termina processi e non effettua scansioni |
| `controlla avvii automatici` | Plist LaunchAgents e LaunchDaemons | Non avvia, ferma o modifica job |
| `controlla permessi sensibili` | Permessi POSIX di .ssh, chiavi private note, credenziali AWS e .env nella home | Non cambia permessi e non legge i segreti |
| `hash sha256 di file PERCORSO` | Impronta SHA-256 di un file | Solo lettura |
| `analizza file PERCORSO` | Indicatori statici e possibili segreti | Non esegue il file |
| `controlla progetto PERCORSO` | Analisi statica limitata dell'albero di progetto | Non esegue file |
| `analizza log PERCORSO` | Conteggi euristici di errori e autenticazioni fallite | Non modifica il log |
| `scansiona host 192.168.1.20` | Richiede una verifica TCP limitata su un solo IPv4 privato | Non parte senza la conferma esatta |
| `confermo scansione 192.168.1.20` | Verifica le sole porte TCP in allowlist sull'host confermato | Connessioni TCP limitate |

## Dettagli e interpretazione

### Processi e porte locali

L'inventario usa psutil, già previsto tra le dipendenze di Jarvis. Il controllo è limitato ai primi 300 processi e 150 socket in ascolto. Segnala come elementi da verificare i programmi avviati da percorsi temporanei o dalla cartella Download. Una porta in ascolto su `0.0.0.0` o `::` è raggiungibile attraverso le interfacce di rete, ma questo non prova che sia vulnerabile: verificare quale servizio la usa e se deve essere esposto.

### Avvii automatici macOS

Vengono letti i file plist nelle directory LaunchAgents e LaunchDaemons standard. Jarvis mostra etichetta, programma e indicatori euristici, ad esempio un programma che punta a Download o a un percorso temporaneo, oppure un eseguibile mancante. Un servizio sconosciuto non è automaticamente malware. Non usare la sola presenza di `RunAtLoad` o `KeepAlive` come prova di compromissione.

### Permessi sensibili

Il controllo esamina solo metadati POSIX e non legge il contenuto di chiavi, credenziali o file `.env`. Per chiavi private e directory SSH, permessi di gruppo/altri utenti possono esporre materiale riservato. Jarvis non corregge automaticamente i permessi perché la scelta dipende dal proprietario e dal contesto.

### Postura macOS

Il controllo usa comandi di sistema fissi con `shell=False` e timeout. Su output ambiguo o comandi non disponibili restituisce `non verificabile`. I controlli non certificano la sicurezza complessiva del computer.

## Limiti importanti

- Nessun exploit, brute force, phishing, furto di credenziali, malware, persistenza, evasione o accesso non autorizzato.
- Nessuna scansione automatica di subnet, indirizzi pubblici o dispositivi non confermati.
- Nessuna modifica automatica a firewall, FileVault, Gatekeeper, SIP, permessi, servizi o processi.
- I rilevamenti sono euristici: possono esserci falsi positivi e falsi negativi.
- La presenza di una porta, di un processo o di un avvio automatico non dimostra una vulnerabilità.
- Gli audit macOS devono essere provati sul Mac reale: la CI GitHub esegue i test su runner Ubuntu e non sostituisce il test su High Sierra.

## Compatibilità e dipendenze

Non vengono aggiunte dipendenze pesanti. Il modulo di audit usa la libreria standard e psutil, già dichiarato in `requirements.txt`. Se psutil non è disponibile, l'audit processi/porte restituisce un errore esplicito senza bloccare Jarvis. Le funzioni macOS si dichiarano non applicabili su altri sistemi.

## Sviluppi non inclusi in questa fase

Un audit TLS/HTTP di siti indicati dall'utente, la verifica online di advisory CVE e l'analisi antivirus tramite ClamAV richiedono ulteriori moduli, regole di privacy, gestione di rete e test dedicati. Non vengono presentati come già implementati.
