# Avvio automatico di J.A.R.V.I.S.

Questa cartella contiene il supporto per l'avvio automatico di Jarvis su macOS.

Il file `com.fulmine1000.jarvis.plist` è un LaunchAgent template. Va installato nel computer dell'utente perché contiene il percorso locale del progetto e del virtual environment.

## Installazione

Dalla cartella del progetto eseguire una sola volta:

```bash
bash avvio/installa_avvio_mac.sh
```

Dopo l'installazione il guardiano vocale verrà avviato automaticamente al login dell'utente, senza dover aprire il Terminale. Quando riconosce la wake word, avvia la sessione di Jarvis. L'installer crea anche un token casuale per il gateway locale autenticato, se non esiste già.

Il token e le impostazioni del gateway sono conservati in `~/.config/jarvis/gateway.env`, fuori dal repository, con permessi `600`; la cartella ha permessi `700`. Il LaunchAgent avvia un wrapper che carica questo file e passa le variabili al processo Jarvis. Il gateway continua ad ascoltare esclusivamente su `127.0.0.1:8767`: per Alexa servirà comunque un tunnel HTTPS protetto da Cloudflare Access.

**Limite attuale:** il LaunchAgent avvia il guardiano vocale, non un Core permanente. Il gateway viene creato soltanto quando il guardiano riconosce la wake word e avvia `jarvis.py`; quando la sessione Jarvis termina, anche il gateway si arresta. Di conseguenza Alexa può raggiungere Jarvis solo mentre quella sessione è attiva. L'esecuzione continua del Core, indipendente dall'HUD e dal guardiano, è un passaggio ancora da implementare e verificare prima di dichiarare Alexa operativa.

Per controllare il gateway dopo l'avvio, verificare il log `logs/guardiano_wake.log` e il log errori `logs/guardiano_wake_error.log`. Non copiare il token in chat o nel repository.

## Disinstallazione

```bash
bash avvio/disinstalla_avvio_mac.sh
```
