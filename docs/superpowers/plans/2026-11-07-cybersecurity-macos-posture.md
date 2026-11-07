# Cybersecurity macOS Posture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Aggiungere a Jarvis un controllo read-only della postura di sicurezza macOS, invocabile a voce e compatibile con High Sierra/Python 3.11.

**Architecture:** Un modulo piccolo e indipendente esegue quattro controlli di sistema con argomenti fissi e `subprocess.run(..., shell=False)`. `CybersecurityJarvis` espone il risultato; `GestoreComandi` aggiunge due frasi vocali. I risultati sconosciuti o non disponibili non vengono trasformati in falsi allarmi né in affermazioni di sicurezza.

**Tech Stack:** Python standard library, unittest, GitHub Actions già presente.

**Spec:** `docs/superpowers/specs/2026-11-07-cybersecurity-design.md`

## Global Constraints

- Target di sviluppo: macOS High Sierra 10.13.6 su Intel; Python 3.11.
- Nessuna nuova dipendenza runtime obbligatoria.
- Solo comandi read-only, argomenti fissi, `shell=False`, timeout massimo 4 secondi per controllo.
- Vietati `sudo`, modifiche alle impostazioni, exploit, scansioni di rete e accessi a sistemi terzi.
- Su sistemi non macOS il risultato deve dichiarare che il controllo non è applicabile.
- Non esporre output grezzo potenzialmente sensibile oltre a una breve motivazione.

## Review Focus

- Comandi di sistema assenti o non eseguibili: il modulo deve restituire "non verificabile", non interrompere Jarvis.
- Output inatteso o localizzato: non dedurre "attivo" o "disattivo" da stringhe ambigue.
- Timeout e errori subprocess: ogni controllo deve degradare indipendentemente.
- Sistemi non macOS: nessun comando esterno deve essere eseguito.
- Sicurezza di esecuzione: nessuna shell, input utente o percorso libero deve essere passato ai comandi di sistema.

---

### Task 1: Modulo indipendente di verifica macOS

**Files:**
- Create: `cybersecurity/postura_mac.py`
- Test: `tests/test_cybersecurity_postura_mac.py`

**Interfaces:**
- Produces: `controlla_postura_mac(sistema=None, runner=None) -> dict`.
- Il risultato include `ok`, `sistema`, `controlli` e `nota`; ogni controllo include `nome`, `stato` e `dettaglio`.

- [x] Scrivere test per macOS con quattro output noti: firewall, FileVault, Gatekeeper e SIP.
- [x] Eseguire il test e verificare il fallimento atteso prima dell'implementazione.
- [x] Scrivere test che garantiscano `shell=False`, timeout limitato e argomenti fissi.
- [x] Scrivere test per sistema non macOS e verificare che il runner non venga chiamato.
- [x] Scrivere test per timeout, comando mancante e output sconosciuto: solo il controllo interessato diventa "non verificabile".
- [x] Implementare il modulo con sola libreria standard e parsing conservativo.
- [x] Eseguire i test del modulo e tutta la suite unittest.
- [x] Commit: `Aggiunge il controllo read-only della sicurezza macOS`.

### Task 2: Collegamento al modulo cybersecurity

**Files:**
- Modify: `cybersecurity/modulo.py`
- Test: `tests/test_cybersecurity.py` o nuovo test dedicato

**Interfaces:**
- Consumes: `controlla_postura_mac()`.
- Produces: `CybersecurityJarvis.controlla_sicurezza_mac()`.

- [x] Aggiungere un test che verifica il passaggio del risultato senza alterazioni.
- [x] Eseguire il test e verificare il fallimento atteso.
- [x] Aggiungere il metodo di facciata e aggiornare `stato()` con la capacità.
- [x] Eseguire test cybersecurity e suite completa.
- [x] Commit: `Espone la verifica postura macOS nel modulo cybersecurity`.

### Task 3: Comando vocale

**Files:**
- Modify: `comandi/gestore.py`
- Create or modify: test mirato in `tests/`

**Interfaces:**
- Consumes: `kernel.cybersecurity.controlla_sicurezza_mac()`.
- Produces: comandi `controlla sicurezza mac` e `controlla protezioni macOS`.

- [x] Scrivere test per entrambe le frasi e per modulo non disponibile.
- [x] Verificare il fallimento atteso.
- [x] Implementare routing deterministico senza inoltrare al modello IA.
- [x] Eseguire test mirati e suite completa.
- [x] Commit: `Aggiunge il comando vocale per la postura di sicurezza Mac`.

### Task 4: Documentazione e verifica

**Files:**
- Modify: `README.md`

- [x] Documentare comandi, significato degli stati e limiti del controllo.
- [x] Verificare `python -m compileall -q .`.
- [x] Verificare `python -m unittest discover -s tests -p 'test_*.py' -v`.
- [x] Verificare i risultati GitHub Actions per Python 3.11, 3.12, 3.13 e 3.15.
- [x] Segnalare separatamente i test non eseguibili senza il Mac fisico.
- [x] Commit: `Documenta la verifica della sicurezza macOS`.



## Esito dell'esecuzione

- Test-first verificato: i test dedicati hanno fallito prima delle rispettive implementazioni e sono passati dopo.
- GitHub Actions: `compileall`, `pip check` e suite completa superati su Python 3.11, 3.12, 3.13 e 3.15.
- Conteggio aggiornato dopo il rapporto unificato e i limiti ClamAV: 350 test, 1 skipped, nessun errore (Python 3.11).
- Verifica fisica su macOS High Sierra non eseguita: i runner GitHub usano Ubuntu; occorre provarla sul Mac per confermare gli output reali dei comandi di sistema.
- CodeRabbit non è esposto come strumento eseguibile in questa sessione; revisione finale effettuata manualmente sui file modificati.

## Fase successiva completata: audit host e antimalware opzionale

- [x] Test-first per inventario processi e socket in ascolto.
- [x] Test-first per inventario plist LaunchAgents/LaunchDaemons.
- [x] Test-first per permessi di directory SSH e file sensibili.
- [x] Test-first per ClamAV assente, pulito, infetto e timeout.
- [x] Facciata CybersecurityJarvis e routing dei comandi vocali.
- [x] Pulsante CYBER aggiunto all'HUD.
- [x] Documentazione dedicata in `docs/CYBERSECURITY_DIFENSIVA.md`.
- [x] CI finale: run `42369684454`, 344 test (1 skipped), Python 3.11/3.12/3.13/3.15 tutti superati.
- [ ] Prova fisica su macOS High Sierra: in attesa di esecuzione sul Mac dell'utente.
- [ ] Verifica ClamAV sul Mac: dipende dal fatto che `clamscan` sia già installato.

- [x] Rapporto unico `rapporto cybersecurity` che orchestra tutti gli audit read-only.
- [x] Pulsante CYBER HUD collegato al rapporto unificato.
- [x] Scanner ClamAV: rifiuto preventivo di file oltre 5 MB e risultato esplicitamente limitato alle dimensioni/numero di file consentiti.
- [x] CI finale del rapporto: run `42369853273`, 350 test (1 skipped), Python 3.11/3.12/3.13/3.15 tutti superati.

- [x] Audit LaunchAgents/LaunchDaemons: include directory utente, `/Library` e `/System/Library`; salta symlink e plist oltre 1 MB.
- [x] I controlli parziali o non verificabili vengono esposti esplicitamente nel rapporto e nel comando postura macOS.
- [x] CI finale aggiornata: run `42370138950`, 350 test (1 skipped), Python 3.11/3.12/3.13/3.15 tutti superati.

- [x] Audit permessi: distingue gli stati non verificabili da permessi troppo aperti e marca il rapporto come parziale.
- [x] CI finale dopo l'ultimo hardening: run `42370138950`, 350 test (1 skipped), Python 3.11/3.12/3.13/3.15 tutti superati.
