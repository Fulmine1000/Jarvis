# J.A.R.V.I.S. — Definitive Edition

Assistente personale modulare in Python, progettato per avvicinarsi il più possibile a un Jarvis cinematografico usando funzioni realmente disponibili su computer e dispositivi collegati.

## Funzioni

- HUD desktop futuristico animato.
- Kernel centrale con gestione moduli, eventi, configurazione e log.
- **Cervello cognitivo IA** separato dal router operativo.
- Conversazione in italiano e personalità formale/elegante.
- AI locale tramite Ollama, con funzionamento degradato sicuro se il motore locale non è disponibile.
- Contesto reale del sistema fornito al cervello senza inventare stato o azioni.
- Wake word `Jarvis`, `Hey Jarvis`, `Ehi Jarvis` e riconoscimento Vosk opzionale.
- Sintesi vocale Piper opzionale con fallback macOS `say`, Linux `espeak` e terminale.
- Supporto a un provider TTS locale con campione audio, quando il motore e il modello compatibili sono disponibili.
- Nuovi componenti vocali riutilizzabili per STT/TTS in `voce/stt.py` e `voce/tts.py`.
- Memoria persistente, profilo, ricordi e contesto.
- Memoria conversazionale riutilizzabile in `memoria/memory.py`.
- Motore conversazionale locale in `intelligenza/conversazione.py`.
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

Per la conversazione IA locale, Jarvis utilizza Ollama quando disponibile. Il modello predefinito è `llama3.2:3b`; endpoint e modello possono essere configurati tramite `JARVIS_OLLAMA_URL` e `JARVIS_OLLAMA_MODEL`.

## Motore IA su macOS High Sierra

Il MacBook Pro Intel di Jarvis usa macOS High Sierra 10.13.6. La versione attuale di Ollama per macOS richiede macOS 14 Sonoma o successivo, quindi non e una strada utilizzabile su questa macchina. citeturn1search0

Jarvis ora usa un router IA automatico: prova un backend locale disponibile, supporta llama.cpp tramite API compatibile e, se nessun backend generativo e pronto, mantiene comunque attivo il motore conversazionale locale senza bloccare l'assistente.

Per preparare il backend IA locale compatibile con il Mac:

```bash
cd ~/Desktop/Jarvis
bash scripts/prepara_motore_ia.sh
```

Il preparatore compila llama.cpp per Intel/High Sierra e scarica il modello Qwen2.5-0.5B-Instruct Q4_0, che supporta l'italiano. citeturn2search0turn2search3

Dopo la preparazione, Jarvis avvia automaticamente il server locale quando serve.
 
## Test

```bash
python -m compileall -q .
python -m unittest discover -s tests -p 'test_*.py' -v
```

## Struttura

- `jarvis.py` — unico punto di ingresso ufficiale.
- `core/` — kernel, facciata pubblica `JARVIS` e servizi fondamentali.
- `intelligenza/` — cervello cognitivo, conversazione IA e memoria conversazionale.
- `comandi/` — gestione ed esecuzione dei comandi.
- `voce/` — ascolto, wake word, riconoscimento e sintesi vocale.
- `interfaccia/` — HUD grafico.
- `memoria/` — memoria persistente e memoria conversazionale.
- `dispositivi/` — integrazioni hardware e smart home.
- `moduli/` — adattatori dei moduli Jarvis.
- `personalita/` — personalità e comportamento.
- `plugin/` — estensioni.
- `config/` — configurazioni e metadati di versione/identità.
- `examples/` — esempi di utilizzo e integrazione.
- `docs/` — documentazione.
- `tests/` — test automatici.
- `legacy/` — moduli storici mantenuti esclusivamente per compatibilità e riferimento.

La root del progetto contiene quindi solo gli elementi realmente necessari al progetto, mentre i componenti tecnici sono organizzati nelle rispettive cartelle.

## Voice Pack italiano

Il progetto incorpora e adatta alcuni componenti del Voice Pack italiano alla struttura reale di Jarvis, senza creare una seconda applicazione parallela.

I componenti principali sono:

- `voce/tts.py` — motore Text-to-Speech riutilizzabile, con supporto ai motori locali disponibili e ricerca di un campione WAV configurato.
- `voce/stt.py` — componente Speech-to-Text riutilizzabile basato su SpeechRecognition.
- `intelligenza/conversazione.py` — motore conversazionale locale con risposte italiane e gestione del contesto di base.
- `memoria/memory.py` — memoria conversazionale temporanea separata dalla memoria persistente di Jarvis.
- `config/settings.py` — configurazione riutilizzabile per voce, AI e audio.
- `core/core.py` — facciata `JARVIS` che utilizza il `KernelJarvis` esistente, evitando un secondo kernel.
- `examples/simple.py` — esempio semplice di ascolto e risposta.
- `examples/integration.py` — esempio di integrazione in un progetto esistente.
- `examples/advanced.py` — esempio con comandi personalizzati.

### Esempi

Gli esempi possono essere eseguiti dalla root della repository dopo aver preparato l'ambiente:

```bash
python examples/simple.py
python examples/integration.py
python examples/advanced.py
```

Gli esempi sono dimostrativi: il punto di ingresso ufficiale dell'applicazione completa rimane `jarvis.py`.

### Nota sulla compatibilità

Le dipendenze del Voice Pack non vengono installate automaticamente solo perché i relativi file sono presenti nella repository. Prima di modificare `requirements.txt`, le dipendenze vengono verificate rispetto all'architettura e alla versione di Python utilizzate da Jarvis.

In particolare, su sistemi meno recenti alcuni motori TTS/ML possono non avere pacchetti binari compatibili. In questi casi Jarvis deve mantenere un fallback funzionante invece di considerare il motore opzionale come obbligatorio.

## Nota

Le funzioni cinematografiche che richiedono hardware inesistente non possono essere create dal solo software. Jarvis, però, è strutturato per sfruttare l'hardware e i servizi realmente collegati senza fingere che un'azione sia stata eseguita quando non lo è stata.

## Voce clonata opzionale

Jarvis può utilizzare un campione audio locale con un motore TTS compatibile con il sistema. Il campione audio personale non deve essere inserito nella repository.

La disponibilità effettiva della clonazione vocale dipende dal motore TTS, dal modello vocale e dalla compatibilità con il sistema operativo e l'architettura del computer.

