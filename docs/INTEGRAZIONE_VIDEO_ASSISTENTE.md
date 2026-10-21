# Integrazione delle funzioni dai video

Questa integrazione riutilizza i componenti esistenti di Jarvis e aggiunge un rilevatore opzionale del doppio battito e notifiche email verso Telegram. Non sostituisce il kernel, l'HUD o il controllo Android già presenti.

## Controllo del telefono

Con Android Platform Tools (ADB) installato e debug USB autorizzato, Jarvis può già eseguire comandi come:
- apri YouTube sul telefono
- apri WhatsApp sul telefono
- apri Chrome sul telefono
- accendi lo schermo del telefono
- chiama mia sorella (apre Contatti) oppure chiama +39... (prepara il dialer)

Jarvis non aggira PIN, password o biometria e non avvia chiamate in modo silenzioso: l'utente controlla il passaggio finale sul telefono.

## Attivazione con due battiti

Il rilevatore non registra né salva l'audio. È disattivato per impostazione predefinita, perché apre uno stream audio separato e alcuni driver non consentono a riconoscimento vocale e rilevatore di usare contemporaneamente lo stesso microfono.

PowerShell:
```powershell
$env:JARVIS_DOPPIO_BATTITO="1"
python jarvis.py
```

Git Bash:
```bash
export JARVIS_DOPPIO_BATTITO=1
python jarvis.py
```

Se l'audio diventa instabile, avviare Jarvis senza la variabile (o impostarla a 0) e usare la wake word standard. La soglia RMS predefinita è 0.18; per modificarla, impostare JARVIS_BATTITO_SOGLIA_RMS a un valore numerico positivo. Una soglia troppo bassa può causare falsi positivi, una troppo alta può non rilevare battiti distanti dal microfono.

Per aprire app o pagine quando viene rilevato il doppio battito, configurare esplicitamente gli elementi desiderati:

PowerShell:
```powershell
$env:JARVIS_BATTITO_APPS="chrome,Spotify"
$env:JARVIS_BATTITO_URLS="https://calendar.google.com,https://github.com"
```

Git Bash:
```bash
export JARVIS_BATTITO_APPS="chrome,Spotify"
export JARVIS_BATTITO_URLS="https://calendar.google.com,https://github.com"
```

Gli elenchi sono facoltativi. Sono configurazioni locali della sessione e non vengono salvate in memoria. Per gli URL vengono accettati soltanto schemi http:// e https://.

## Notifiche email via Telegram (opzionali)

Jarvis può controllare periodicamente la cartella IMAP in sola lettura e inviare su Telegram soltanto mittente e oggetto delle email non lette. Non scarica il corpo o gli allegati, non marca i messaggi come letti e non invia email. Il monitor è disattivato per impostazione predefinita.

Configurare prima le variabili d'ambiente con le credenziali del proprio provider IMAP e con un bot Telegram creato dall'utente. Non inserire token o password nei file del repository.

PowerShell:
```powershell
$env:JARVIS_NOTIFICHE_EMAIL_TELEGRAM="1"
$env:JARVIS_IMAP_HOST="imap.example.com"
$env:JARVIS_IMAP_PORT="993"
$env:JARVIS_IMAP_USER="tuo-indirizzo@example.com"
$env:JARVIS_IMAP_PASSWORD="password-app"
$env:JARVIS_IMAP_MAILBOX="INBOX"
$env:JARVIS_TELEGRAM_BOT_TOKEN="token-del-tuo-bot"
$env:JARVIS_TELEGRAM_CHAT_ID="id-della-tua-chat"
python jarvis.py
```

Git Bash:
```bash
export JARVIS_NOTIFICHE_EMAIL_TELEGRAM=1
export JARVIS_IMAP_HOST="imap.example.com"
export JARVIS_IMAP_PORT=993
export JARVIS_IMAP_USER="tuo-indirizzo@example.com"
export JARVIS_IMAP_PASSWORD="password-app"
export JARVIS_IMAP_MAILBOX=INBOX
export JARVIS_TELEGRAM_BOT_TOKEN="token-del-tuo-bot"
export JARVIS_TELEGRAM_CHAT_ID="id-della-tua-chat"
python jarvis.py
```

Sostituire tutti i valori di esempio. Alcuni provider richiedono IMAP abilitato e una password per app. Non condividere le credenziali con altre persone. Per disattivare il monitor, impostare JARVIS_NOTIFICHE_EMAIL_TELEGRAM a 0 o rimuovere la variabile.

## Limiti dei video analizzati

Il video sul controllo del telefono mostra funzioni già in parte coperte dal modulo dispositivi/controllo_android.py; questo aggiornamento le documenta e aggiunge il doppio battito. Il secondo video fornito è una dimostrazione di una mod per Cyberpunk 2077 che integra BT-7274 di Titanfall 2, non un assistente personale né un'API generica da integrare in Jarvis: non è stato copiato codice o contenuto del gioco.

La generazione di risposte nello stile dell'utente e l'invio automatico di messaggi privati non sono abilitati: richiedono API e autorizzazioni specifiche, regole per i contatti consentiti e una conferma esplicita prima dell'invio.
