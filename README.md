# J.A.R.V.I.S. — versione definitiva

Assistente intelligente personale modulare per macOS/Linux con companion Android, kernel centrale, memoria persistente, voce offline, wake word, gestione dispositivi, smart home, plugin e integrazione opzionale con TV LG webOS.

## Avvio

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
python main.py
```

Oppure:

```bash
./scripts/start_jarvis.sh
```

Se microfono, Vosk o PortAudio non sono disponibili, Jarvis entra automaticamente in modalità solo-testo.

## Voce

Per l'ascolto offline italiano usare il modello `vosk-model-small-it-0.22` nella root del progetto. La wake word supporta `Jarvis`, `Ehi Jarvis` e `Hey Jarvis`.

Per la sintesi vocale Piper, mettere il modello `.onnx` in `voce/modelli/`; in assenza del modello viene usato il fallback disponibile sul sistema.

## TV LG webOS

L'integrazione è opzionale e non impedisce l'avvio di Jarvis.

1. Aprire `config/config.json`.
2. Impostare `tv_lg.ip` con l'indirizzo IP della TV.
3. Avviare Jarvis e dire `connetti tv`.
4. Accettare la richiesta di associazione sulla TV se viene mostrata.
5. Usare comandi come `stato tv`, `spegni tv`, `volume tv 20`, `muta tv`.

La chiave di associazione viene salvata localmente in `config/lg_tv_client_key.txt` quando webOS la restituisce. Non inserire credenziali o chiavi personali nel repository pubblico.

Nota: l'accensione da rete non viene simulata; dipende dal modello LG e dalle funzioni Wake-on-LAN/webOS supportate.

## Comandi principali

- `buongiorno`, `buonasera`, `come stai`, `aiutami`
- `che ore sono`, `che giorno è`
- `ricorda <chiave> è <valore>`, `cosa ricordi di me`
- `chiamami <nome>`, `come mi chiamo`
- `stato sistema`, `stato dispositivi`, `quali dispositivi`
- `stato motorola`, `trasferisciti sul telefono`, `torna al motorola`
- `apri <app>`, `chiudi <app>`
- `accendi <dispositivo>`, `spegni <dispositivo>`
- `stato tv`, `connetti tv`, `spegni tv`, `volume tv <0-100>`, `muta tv`
- `esci`, `chiudi`, `stop`

## Architettura

```text
main.py                  entry point
core/                    kernel, configurazione, eventi, logging
memoria/                 memoria, profilo, preferenze, contesto
voce/                    ascolto, Vosk, wake word, sintesi
comandi/                 router dei comandi
dispositivi/             telefono, computer, rete, Bluetooth, smart home, TV LG
moduli/                  moduli kernel
plugin/                  sistema plugin
interfaccia/             HUD
personalita/             personalità e risposte
sicurezza.py             controlli di sicurezza
stato.py                 monitor sistema
aggiornamenti.py         aggiornamenti/backup
scripts/                 avvio
tests/                   regressioni automatiche
```

I file legacy sono mantenuti per compatibilità/storia; il percorso ufficiale è `main.py` → `core.kernel.KernelJarvis`.

## Test

```bash
python -m unittest discover -s tests -v
```

La CI GitHub esegue automaticamente i test sulle versioni Python supportate.
