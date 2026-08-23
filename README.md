# J.A.R.V.I.S. — Definitive Edition

Assistente personale modulare in Python, progettato per avvicinarsi il più possibile a un Jarvis cinematografico usando funzioni realmente disponibili su computer e dispositivi collegati.

## Funzioni

- HUD desktop futuristico **animato**, ispirato al riferimento fornito: anelli concentrici, segmenti rotanti, tacche radiali, nucleo centrale, accento giallo, pannelli tecnici e stati `SYSTEM ONLINE`, `LISTENING`, `SPEAKING`.
- Kernel centrale con gestione moduli, eventi, configurazione e log.
- Conversazione in italiano e personalità formale/elegante.
- AI locale opzionale tramite Ollama per conversazioni libere.
- Wake word `Jarvis`, `Hey Jarvis`, `Ehi Jarvis` e riconoscimento Vosk opzionale.
- Sintesi vocale Piper opzionale con fallback macOS `say`, Linux `espeak` e terminale.
- Memoria persistente, profilo, ricordi e contesto.
- Calcolatrice sicura, ora/data, diagnostica, CPU/RAM/disco, browser, app, cartelle, screenshot, volume e timer.
- Automazioni e attività pianificate.
- Modulo visione predisposto e rilevamento camera.
- Integrazioni per computer, telefono Android, rete, Bluetooth, smart home e TV LG webOS.
- Plugin caricabili.
- Sicurezza con conferma per operazioni protette.
- Suite di test e GitHub Actions CI.

## Avvio

```bash
python3 main.py
```

oppure:

```bash
./scripts/avvia_jarvis.sh
```

## Test

```bash
python -m compileall -q .
python -m unittest discover -s tests -p 'test_*.py' -v
```

## Struttura

`core/` kernel e servizi · `comandi/` comandi · `memoria/` memoria · `voce/` audio · `interfaccia/` HUD · `dispositivi/` integrazioni · `moduli/` adattatori · `personalita/` personalità · `plugin/` estensioni · `config/` configurazione · `tests/` test · `docs/` documentazione · `scripts/` avvio.

## Nota

Le funzioni cinematografiche che richiedono hardware inesistente non possono essere create dal solo software. Jarvis, però, è strutturato per sfruttare l'hardware e i servizi realmente collegati senza fingere che un'azione sia stata eseguita quando non lo è stata.
