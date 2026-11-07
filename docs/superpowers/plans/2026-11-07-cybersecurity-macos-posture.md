# Cybersecurity macOS Posture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

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

- [ ] Scrivere test per macOS con quattro output noti: firewall, FileVault, Gatekeeper e SIP.
- [ ] Eseguire il test e verificare il fallimento atteso prima dell'implementazione.
- [ ] Scrivere test che garantiscano `shell=False`, timeout limitato e argomenti fissi.
- [ ] Scrivere test per sistema non macOS e verificare che il runner non venga chiamato.
- [ ] Scrivere test per timeout, comando mancante e output sconosciuto: solo il controllo interessato diventa "non verificabile".
- [ ] Implementare il modulo con sola libreria standard e parsing conservativo.
- [ ] Eseguire i test del modulo e tutta la suite unittest.
- [ ] Commit: `Aggiunge il controllo read-only della sicurezza macOS`.

### Task 2: Collegamento al modulo cybersecurity

**Files:**
- Modify: `cybersecurity/modulo.py`
- Test: `tests/test_cybersecurity.py` o nuovo test dedicato

**Interfaces:**
- Consumes: `controlla_postura_mac()`.
- Produces: `CybersecurityJarvis.controlla_sicurezza_mac()`.

- [ ] Aggiungere un test che verifica il passaggio del risultato senza alterazioni.
- [ ] Eseguire il test e verificare il fallimento atteso.
- [ ] Aggiungere il metodo di facciata e aggiornare `stato()` con la capacità.
- [ ] Eseguire test cybersecurity e suite completa.
- [ ] Commit: `Espone la verifica postura macOS nel modulo cybersecurity`.

### Task 3: Comando vocale

**Files:**
- Modify: `comandi/gestore.py`
- Create or modify: test mirato in `tests/`

**Interfaces:**
- Consumes: `kernel.cybersecurity.controlla_sicurezza_mac()`.
- Produces: comandi `controlla sicurezza mac` e `controlla protezioni macOS`.

- [ ] Scrivere test per entrambe le frasi e per modulo non disponibile.
- [ ] Verificare il fallimento atteso.
- [ ] Implementare routing deterministico senza inoltrare al modello IA.
- [ ] Eseguire test mirati e suite completa.
- [ ] Commit: `Aggiunge il comando vocale per la postura di sicurezza Mac`.

### Task 4: Documentazione e verifica

**Files:**
- Modify: `README.md`

- [ ] Documentare comandi, significato degli stati e limiti del controllo.
- [ ] Verificare `python -m compileall -q .`.
- [ ] Verificare `python -m unittest discover -s tests -p 'test_*.py' -v`.
- [ ] Verificare i risultati GitHub Actions per Python 3.11, 3.12, 3.13 e 3.15.
- [ ] Segnalare separatamente i test non eseguibili senza il Mac fisico.
- [ ] Commit: `Documenta la verifica della sicurezza macOS`.

