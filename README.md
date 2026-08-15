# J.A.R.V.I.S. 3.0

Assistente intelligente personale modulare (kernel + moduli + plugin + memoria
persistente). Avvia in modalità vocale se microfono, Vosk e modello sono
disponibili, altrimenti entra automaticamente in **modalità solo-testo**.

## Avvio rapido

```bash
pip install -r requirements.txt
python main.py
```

## Requisiti

- Python 3.11+ (testato anche su 3.13)
- `pip install -r requirements.txt`

### Dipendenze Python

| Pacchetto      | Obbligatoria? | Note                                                |
|----------------|---------------|-----------------------------------------------------|
| `vosk`         | No            | Riconoscimento vocale. Senza → solo-testo.          |
| `sounddevice`  | No            | Acquisizione microfono. Senza → solo-testo.         |
| `psutil`       | No            | Metriche di sistema. Senza → "Non disponibile".     |

### Dipendenze di sistema (binari esterni)

| Binario  | Piattaforma | Scopo                                   | Installazione                  |
|----------|-------------|-----------------------------------------|--------------------------------|
| PortAudio| macOS/Linux | Backend di `sounddevice`                | `brew install portaudio` / `apt install portaudio19-dev` |
| `piper`  | Tutte       | Sintesi vocale Jarvis (voce personalizzata) | https://github.com/rhasspy/piper |
| `say`    | macOS       | Sintesi vocale di fallback              | Nativo                         |
| `afplay` | macOS       | Riproduzione audio generato da Piper    | Nativo                         |
| `espeak` | Linux       | Sintesi vocale di fallback              | `apt install espeak`           |
| `adb`    | Tutte       | Controllo reale telefono Android        | Android Platform Tools         |

### Modello Vosk (riconoscimento vocale italiano)

Scaricare il modello `vosk-model-small-it-0.22` e decomprimerlo nella root del
progetto:

```bash
# Esempio
wget https://alphacephei.com/vosk/models/vosk-model-small-it-0.22.zip
unzip vosk-model-small-it-0.22.zip
```

Il percorso atteso è `./vosk-model-small-it-0.22/` (configurabile in
`config/config.json` → `voce.modello_riconoscimento`).

### Modello vocale Piper (voce personalizzata, facoltativo)

Posizionare il modello `.onnx` in `voce/modelli/`. Il percorso predefinito è
`voce/modelli/it_IT-jarvis.onnx` (configurabile in `config/config.json` →
`voce.modello`). Se assente, Jarvis usa il fallback di sistema (`say` su macOS,
`espeak` su Linux).

## Modalità di avvio

- **Modalità vocale**: microfono + Vosk + modello presenti → ascolto continuo
  tramite wake word ("Jarvis").
- **Modalità solo-testo**: dipendenze audio mancanti → Jarvis accetta comandi
  da terminale con `input()`. Avviene automaticamente.

## Comandi disponibili (esempi)

- `buongiorno` / `come stai` / `aiutami`
- `che ore sono` / `che giorno è`
- `ricorda <chiave> è <valore>` / `cosa ricordi di me`
- `chiamami <nome>` / `come mi chiamo`
- `stato sistema` / `stato dispositivi` / `quali dispositivi`
- `stato motorola` / `identifica motorola` / `sincronizza motorola`
- `trasferisciti sul telefono` / `stato telefono` / `torna al motorola`
- `apri <app>` / `chiudi <app>` (sul telefono attivo)
- `accendi <nome>` / `spegni <nome>` (smart home)
- `esci` / `chiudi` / `stop`

## Architettura

```
main.py                 ← Entry point ufficiale
core/                   ← kernel, logger, event_bus, manager, config
memoria/                ← memoria, database, profilo, preferenze, contesto
voce/                   ← ascoltatore, riconoscimento, sintesi, wake_word, motore_ascolto, assistente_voce
comandi/                ← gestore comandi
dispositivi/            ← telefono, computer, rete, bluetooth, smart_home, console, gestore, connessione, identita
moduli/                 ← voce_modulo, dispositivi_modulo, comandi_modulo
plugin/                 ← plugin_base, plugin_manager, sistema
interfaccia/            ← hud (interfaccia testuale)
personalita/            ← personalita
sicurezza.py            ← sicurezza
stato.py                ← monitor di sistema
aggiornamenti.py        ← backup/versione
```

I file legacy (`voce.py`, `ascolto.py`, `comandi.py`, `interfaccia.py`,
`jarvis_vosk.py`, `gestore_memoria.py`, `jarvis.py`) sono mantenuti per
riferimento storico e non sono usati dal kernel 3.0.
