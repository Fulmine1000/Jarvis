# Jarvis Cybersecurity — Design

## Intent

Aggiungere a Jarvis un arsenale pratico di cybersecurity ed ethical hacking, richiamabile a voce e dall'HUD, per proteggere e verificare il Mac, i dispositivi e le reti che l'utente possiede o è autorizzato a testare. "Tutte le tecniche del mondo" non è un obiettivo tecnicamente finito: il progetto adotterà invece un catalogo estendibile di controlli professionali, con limiti e risultati verificabili.

## Stato attuale rilevato

Il branch `master` contiene già `cybersecurity/modulo.py`, collegato a `KernelJarvis`, con inventario rete passivo, verifica TCP limitata a un singolo IPv4 privato e conferma esatta, SHA-256, analisi statica euristica di file/progetti e analisi di log. Esistono dieci test dedicati in `tests/test_cybersecurity.py`; il gestore comandi espone già comandi vocali per queste funzioni. Non duplicare questi moduli.

## Obiettivi

- Integrare verifiche read-only e conservative compatibili con Python 3.11 e macOS High Sierra su Intel.
- Non aggiungere dipendenze obbligatorie al runtime di base.
- Rendere ogni controllo esplicito, limitato, spiegabile e registrato.
- Mostrare risultati distinti da inferenze: attivo, disattivo, non disponibile, non verificabile.
- Collegare i controlli al kernel e ai comandi vocali senza eseguire azioni distruttive.
- Aggiungere test unitari ripetibili; usare GitHub Actions per la matrice Python esistente e richiedere test hardware separati sul Mac.

## Non-obiettivi e limiti di sicurezza

- Nessun accesso non autorizzato, exploit automatico, furto di credenziali, brute force, malware, persistenza, evasione, phishing, deautenticazione Wi-Fi o esfiltrazione.
- Nessun aggiramento di PIN, biometria, firewall o protezioni del sistema.
- Nessun comando con privilegi elevati, nessun `sudo`, nessuna modifica a firewall, FileVault, Gatekeeper o SIP.
- Nessuna scansione di subnet o di indirizzi pubblici.
- Non dichiarare una macchina sicura solo perché i controlli disponibili non hanno trovato problemi.

## Approcci considerati

1. **Suite unica con molte dipendenze e scansioni automatiche** — esclusa: pesante per il Mac 2010/High Sierra, difficile da verificare e con rischio di azioni inattese.
2. **Moduli Python nativi, incrementali e read-only** — scelta: compatibile con l'architettura esistente, nessuna dipendenza obbligatoria, controlli separati e testabili.
3. **Integrazioni opzionali con strumenti esterni** — fase successiva solo per tool presenti e verificati, ciascuno isolato, disattivato di default e invocato esplicitamente.

## Prima fase: postura di sicurezza macOS

Aggiungere un controllo read-only per lo stato del firewall applicazioni, FileVault, Gatekeeper e System Integrity Protection. Eseguire solo gli strumenti di sistema macOS previsti, con argomenti fissi, `shell=False`, timeout breve, nessuna elevazione dei privilegi e gestione esplicita degli output non riconosciuti. Su sistemi non macOS il controllo deve dichiararsi non applicabile. Il comando vocale sarà `controlla sicurezza Mac` e un alias `controlla protezioni macOS`.

## Stato aggiornato — 7 novembre 2026

Sono implementati e collegati al kernel/comandi vocali:
- baseline macOS read-only per firewall applicazioni, FileVault, Gatekeeper e SIP;
- inventario locale di processi e socket TCP/UDP in ascolto tramite psutil, con limiti e indicatori euristici;
- lettura statica dei LaunchAgents/LaunchDaemons macOS;
- controllo dei permessi POSIX di directory SSH, chiavi private note, credenziali AWS e file .env standard;
- scansione locale opzionale con ClamAV, solo se il binario è già installato, con timeout e limiti, senza rimozione o quarantena;
- rapporto unificato `rapporto cybersecurity`, pulsante CYBER nell'HUD e documentazione in `docs/CYBERSECURITY_DIFENSIVA.md`.

La CI completa ha eseguito 350 test (1 skipped) con esito positivo su Python 3.11, 3.12, 3.13 e 3.15. I runner sono Ubuntu: il test fisico del Mac Intel/High Sierra resta obbligatorio prima di considerare validate le uscite dei comandi macOS e la disponibilità reale di ClamAV.

## Evoluzione prevista

1. Baseline macOS read-only.
2. Inventario processi, servizi e applicazioni di avvio con spiegazione dei permessi e nessuna terminazione automatica.
3. Audit locale delle configurazioni TLS/certificati e degli header HTTP su un URL esplicitamente indicato, senza autenticarsi né inviare dati.
4. Audit dipendenze e configurazioni dei progetti, con advisory aggiornati solo su richiesta e previa informativa sui dati trasmessi.
5. Analisi malware opzionale tramite scanner locale già installato (es. ClamAV), senza eseguire i campioni.
6. Report HUD e storico locale minimizzato, con esportazione esplicita.

Ogni fase avrà una specifica e test propri; gli strumenti esterni e le verifiche online non diventeranno dipendenze obbligatorie.

## Vincoli

- Piattaforma di sviluppo: Mac Intel 2010, macOS High Sierra 10.13.6.
- Runtime target noto: Python 3.11; la CI corrente verifica Python 3.11, 3.12, 3.13 e 3.15.
- Conservare compatibilità e fallback; niente dipendenze pesanti nel `requirements.txt`.
- Le modifiche di progetto vanno su `master`, con test prima del codice e verifica CI dopo ogni fase.
