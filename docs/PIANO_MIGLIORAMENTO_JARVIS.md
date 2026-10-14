# Ricerca e piano di miglioramento di Jarvis

Questo documento raccoglie idee tecniche osservate in progetti pubblici di assistenti chiamati Jarvis e in architetture vocali open source. Non è possibile verificare ogni repository esistente al mondo: i progetti sotto sono esempi selezionati, non una classifica esaustiva. Le idee vengono adattate alla struttura di `Fulmine1000/Jarvis`, non copiate integralmente.

## Riferimenti consultati

- [P-SAMEERA/JARVIS](https://github.com/P-SAMEERA/JARVIS) — architettura local-first modulare, memoria persistente, separazione tra comandi deterministici e richieste che richiedono un modello linguistico.
- [jmtitan/Jarvis](https://github.com/jmtitan/Jarvis) — separazione tra acquisizione microfono, riconoscimento, servizio di ragionamento e sintesi; risposta vocale a blocchi per ridurre la latenza. La sua configurazione GPU/WSL non è adatta al Mac High Sierra.
- [stevensaint/jarvis](https://github.com/stevensaint/jarvis) — provider vocali intercambiabili, modelli locali e verifiche esplicite del funzionamento prima di dichiarare un backend pronto.
- [InterGenJLU/jarvis](https://github.com/InterGenJLU/jarvis) — valutazione sistematica delle trascrizioni, instradamento verso strumenti e memoria recuperabile. La sua configurazione ROCm/GPU non è portabile sul MacBook Pro Intel del 2010.
- [Vosk API](https://alphacephei.com/vosk/) — riconoscimento offline e streaming.
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp) — riconoscimento multilingue locale tramite modelli Whisper.
- [py-webrtc-audio-processing](https://github.com/serenadeai/webrtc-audio-processing) — riferimento per elaborazione audio WebRTC; Jarvis usa già il wrapper `pywebrtc-audio` quando installato.
- [Home Assistant Assist](https://www.home-assistant.io/voice_control/) — architettura a pipeline per separare wake word, STT, intenti e TTS; utile come modello concettuale per future integrazioni smart home.

Le descrizioni dei repository sono dichiarazioni dei rispettivi progetti, non benchmark indipendenti. Le prestazioni effettive vanno misurate sul dispositivo su cui Jarvis verrà eseguito.

## Migliorie selezionate per Jarvis

### 1. Ascolto e diagnosi audio — priorità massima

- Conservare l'acquisizione continua necessaria alla wake word, ma non salvare l'audio in modo permanente per impostazione predefinita.
- Misurare RMS, picco e possibile clipping per distinguere un microfono troppo basso da un segnale distorto.
- Mostrare separatamente la trascrizione grezza del motore e quella normalizzata da Jarvis: una correzione fonetica non deve nascondere l'errore originario.
- Se Vosk fornisce le parole con i valori `conf`, esporre una confidenza media soltanto come indizio diagnostico. Non usarla da sola per autorizzare o rifiutare comandi: non è una probabilità calibrata e può mancare.
- Evitare che frammenti di una parola vengano eseguiti come comandi; mantenere il timeout della sessione e la protezione dall'eco di Jarvis.
- Valutare un VAD (Voice Activity Detection) soltanto dopo avere misurato il flusso attuale: un VAD troppo aggressivo può tagliare l'inizio o la fine delle parole.

### 2. Migliorare il riconoscimento italiano

- Tenere Vosk italiano come percorso leggero predefinito sul Mac Intel datato.
- Confrontare il modello Vosk small e quello italiano completo già disponibili, usando le stesse frasi registrate volontariamente o pronunciate durante un test, senza salvare audio automaticamente.
- Provare `whisper.cpp` solo come opzione configurabile e misurarne latenza e memoria sul Mac. Non abilitarlo automaticamente se rende l'ascolto lento.
- Correggere trascrizioni solo con regole precise, limitate e testate. Non introdurre fuzzy matching generalizzato che potrebbe trasformare conversazioni ambientali in comandi.
- Mantenere un piccolo corpus di frasi di prova italiane: wake word da sola, wake word più comando, pausa tra wake word e comando, frasi normali senza wake word, rumore, e parole simili.

### 3. Voce di Jarvis

- Mantenere un'interfaccia unica per i provider TTS: Piper quando modello e librerie sono realmente compatibili; voce macOS `say` come fallback; eventuali servizi cloud solo opt-in.
- Verificare con un test reale che il provider abbia generato e riprodotto audio prima di segnalarlo come attivo.
- Tenere il campione vocale fuori da GitHub; non inserire chiavi API o registrazioni personali nella repository.
- Valutare la riproduzione per frasi o segmenti più brevi solo dopo aver verificato che non tagli parole, non sovrapponga audio e non faccia ascoltare a Vosk la voce di Jarvis come un nuovo comando.
- Separare il nome della voce, la pronuncia della wake word e il testo pronunciato: non usare una voce inglese soltanto per correggere la parola «Jarvis» se questo peggiora il resto dell'italiano.

### 4. Intelligenza e memoria

- Mantenere i comandi deterministici (ora, timer, volume, apertura applicazioni) separati dal modello linguistico: sono più veloci e verificabili.
- Usare il modello locale per richieste aperte, pianificazione e formulazioni, senza affidargli direttamente operazioni sensibili.
- Conservare la memoria persistente con distinzione tra profilo, preferenze e contesto temporaneo; consentire di visualizzare e cancellare i ricordi.
- Prima di dichiarare un'azione completata, controllare il risultato reale dello strumento o del sistema.
- Aggiungere test di conversazione per casi reali, oltre ai test unitari.

### 5. Strumenti, dispositivi e sicurezza

- Aggiungere funzioni tramite moduli/plugin con contratti chiari, invece di duplicare il kernel.
- Richiedere conferma per cancellazioni, scritture importanti, scansioni di rete e azioni su dispositivi.
- Non trattare pagine web, documenti o risposte di modelli come istruzioni privilegiate.
- Per telefono, Bluetooth, TV e smart home, mostrare lo stato realmente verificato e non simulare connessioni.
- Mantenere un funzionamento degradato: se un modello, il microfono o un provider TTS non è disponibile, l'avvio non deve fingere che quella funzione sia operativa.

## Ordine di implementazione

1. **Diagnostica vocale osservabile** — trascrizione grezza/normalizzata, livello audio, clipping e dettagli Vosk disponibili. Implementata in `scripts/diagnostica_voce.py` e `voce/riconoscimento.py`; i test devono confermare che il riconoscimento continua anche senza i dettagli.
2. **Test ripetibili della wake word** — aumentare le prove su frasi corrette, frammenti e trascrizioni simili prima di modificare le regole di normalizzazione.
3. **Confronto dei modelli STT sul Mac** — misurare qualità, latenza e memoria; nessuna scelta basata solo sulle specifiche pubblicate.
4. **VAD e gestione del turno** — sperimentazione dietro una configurazione, con possibilità di disattivarla se taglia parole.
5. **Verifica TTS e riduzione dell'eco** — test su voce italiana, pronuncia di «Jarvis», tempi di risposta e barge-in (interrompere la voce quando l'utente parla).
6. **Memoria e strumenti più verificabili** — audit dei permessi, conferme e test end-to-end.
7. **Visione e integrazioni avanzate** — solo quando hardware, privacy e compatibilità sono confermati.

## Vincoli tecnici

Il Mac di sviluppo è un MacBook Pro Intel del 2010 con macOS High Sierra 10.13.6. Non si devono rendere obbligatori modelli o pacchetti che richiedano macOS recente, GPU moderne, Docker o servizi cloud. Le funzionalità pesanti devono restare opzionali e avere un fallback funzionante. Le modifiche vanno verificate con:

```bash
python -m compileall -q .
python -m unittest discover -s tests -p 'test_*.py' -v
```

Questi controlli dimostrano la correttezza dei test automatizzati, non garantiscono la precisione del microfono reale: per quella serve una prova audio sul Mac.
