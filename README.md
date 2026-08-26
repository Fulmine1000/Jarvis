# J.A.R.V.I.S. — Definitive Edition

Assistente personale modulare in Python, progettato per avvicinarsi il più possibile a un Jarvis cinematografico usando funzioni realmente disponibili su computer e dispositivi collegati.

## Funzioni

- HUD desktop futuristico animato.
- Kernel centrale con gestione moduli, eventi, configurazione e log.
- Conversazione in italiano e personalità formale/elegante.
- AI locale opzionale tramite Ollama.
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

Il punto di ingresso ufficiale è `jarvis.py`:

```bash
python jarvis.py
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

- `jarvis.py` — unico punto di ingresso ufficiale.
- `core/` — kernel e servizi fondamentali.
- `comandi/` — gestione ed esecuzione dei comandi.
- `voce/` — ascolto, wake word, riconoscimento e sintesi vocale.
- `interfaccia/` — HUD grafico.
- `memoria/` — memoria persistente.
- `dispositivi/` — integrazioni hardware e smart home.
- `moduli/` — adattatori dei moduli Jarvis.
- `personalita/` — personalità e comportamento.
- `plugin/` — estensioni.
- `config/` — configurazioni e metadati di versione/identità.
- `docs/` — documentazione.
- `tests/` — test automatici.
- `legacy/` — moduli storici mantenuti esclusivamente per compatibilità e riferimento.

La root del progetto contiene quindi solo gli elementi realmente necessari al progetto, mentre i componenti tecnici sono organizzati nelle rispettive cartelle.

## Nota

Le funzioni cinematografiche che richiedono hardware inesistente non possono essere create dal solo software. Jarvis, però, è strutturato per sfruttare l'hardware e i servizi realmente collegati senza fingere che un'azione sia stata eseguita quando non lo è stata.
