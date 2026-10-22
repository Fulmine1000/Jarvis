# Integrazione dei tre Shorts in Jarvis

Questa guida documenta le funzioni ispirate ai tre video analizzati con vidIQ e come provarle nella repository `Fulmine1000/Jarvis`. Sono state adattate ai moduli esistenti; non viene simulato hardware o stato non verificato.

## 1. Controllo di più telefoni Android

Jarvis può individuare più dispositivi Android già autorizzati da ADB e inviare un'azione a ciascuno.

1. Installa Android Platform Tools.
2. Attiva Opzioni sviluppatore e Debug USB su ogni telefono.
3. Collega i telefoni via USB e approva la richiesta di autorizzazione su ciascuno.
4. Verifica da terminale:

```bash
adb devices
```

Comandi vocali o testuali:

- `accendi tutti i telefoni` — risveglia gli schermi.
- `apri youtube su tutti i telefoni`
- `apri spotify su tutti i telefoni`
- `apri chrome su tutti i telefoni`
- `apri https://www.youtube.com/watch?v=VIDEO_ID su tutti i telefoni`
- `riproduci la mia canzone preferita su tutti i telefoni`

Per l'ultimo comando, configura un URL esplicito prima di avviare Jarvis.

PowerShell:

```powershell
$env:JARVIS_MEDIA_PREFERITA_URL="https://www.youtube.com/watch?v=VIDEO_ID"
python jarvis.py
```

Git Bash:

```bash
export JARVIS_MEDIA_PREFERITA_URL="https://www.youtube.com/watch?v=VIDEO_ID"
python jarvis.py
```

**Limite di sicurezza:** Jarvis può accendere gli schermi e aprire app o link, ma non aggira PIN, password, biometria o schermate di consenso. Se un telefono è bloccato, l'autenticazione rimane manuale. L'apertura di un video non garantisce l'avvio automatico della riproduzione: dipende da Android, dall'app e dai consensi richiesti.

## 2. Widget HUD

Il dock laterale dell'HUD offre accesso rapido a:

- Ora e data locali.
- Meteo (richiesta online, con città predefinita Napoli).
- Titoli delle notizie internazionali tramite feed RSS.
- Calcolatrice aritmetica con parser limitato; non esegue codice Python.
- Blocco note salvato localmente in `data/hud_note.txt`.
- Test di velocità della rete, se è disponibile il pacchetto opzionale `speedtest-cli`.

Comandi supportati:

- `meteo` oppure `meteo Roma`
- `notizie`
- `calcola (12 + 4) * 3`
- `nota: ricordare il progetto`
- `leggi nota`
- `test velocità rete`

Le richieste meteo, notizie e velocità richiedono Internet e possono fallire se il servizio remoto non è disponibile. Il test completo della velocità non è incluso nelle dipendenze obbligatorie: se necessario, installa `speedtest-cli` nel virtualenv con `python -m pip install speedtest-cli`. La compatibilità del pacchetto dipende dalla versione di Python e dal sistema operativo.

## 3. Ologramma 3D e gesti

Il nucleo centrale dell'HUD passa all'accento arancione mentre Jarvis ascolta o parla e torna al ciano in standby. Il pulsante **APRI MODELLO 3D** dell'HUD apre il visualizzatore locale `interfaccia/ologramma_3d.html`. Mostra una macchina wireframe procedurale. Il riconoscimento gestuale gira in Chrome tramite MediaPipe JavaScript caricato da CDN; serve una connessione Internet al primo caricamento.

- Trascinamento mouse o dito: rotazione.
- Rotella: zoom.
- Pulsante nel viewer: vista esplosa/ricomposta dei componenti.
- Se il controllo gestuale opzionale è attivo, scorrimento ruota il modello, due mani regolano lo zoom e il pizzico commuta la vista esplosa.

Per il controllo gestuale della macchina 3D non serve installare pacchetti Python:

```bash
python jarvis.py
```

Apri **APRI MODELLO 3D**: Chrome richiede il permesso per la fotocamera e avvia il tracciamento delle mani direttamente nel browser. I fotogrammi vengono elaborati localmente e non vengono salvati. Se il permesso viene negato, consenti la fotocamera per `127.0.0.1` nelle impostazioni di Chrome e ricarica la pagina. La pagina deve poter caricare MediaPipe dalla CDN, quindi è necessaria Internet.

Il viewer è una dimostrazione 3D wireframe procedurale: non è una scansione reale di un oggetto e non genera automaticamente modelli 3D da file. Il server di collegamento ascolta soltanto su `127.0.0.1` e serve la pagina e una coda limitata di eventi gestuali.

## Test

Dalla root del progetto:

```bash
python -m compileall -q .
python -m unittest discover -s tests -p 'test_controllo_android_multi.py' -v
python -m unittest discover -s tests -p 'test_dashboard_hud.py' -v
```

Questi comandi sono istruzioni per verificare il checkout locale; non implicano che i test siano già stati eseguiti sul computer dell'utente.
