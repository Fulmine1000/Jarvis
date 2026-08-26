# Avvio automatico di J.A.R.V.I.S.

Questa cartella contiene il supporto per l'avvio automatico di Jarvis su macOS.

Il file `com.fulmine1000.jarvis.plist` è un LaunchAgent template. Va installato nel computer dell'utente perché contiene il percorso locale del progetto e del virtual environment.

## Installazione

Dalla cartella del progetto eseguire una sola volta:

```bash
bash avvio/installa_avvio_mac.sh
```

Dopo l'installazione Jarvis verrà avviato automaticamente al login dell'utente, senza dover aprire il Terminale e senza digitare `python jarvis.py`.

## Disinstallazione

```bash
bash avvio/disinstalla_avvio_mac.sh
```
