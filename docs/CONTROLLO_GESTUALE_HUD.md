# Controllo gestuale HUD

Il controllo gestuale si integra nell'applicazione Jarvis esistente e non crea
una seconda applicazione. I fotogrammi vengono elaborati localmente in memoria;
non vengono salvati video o immagini.

## Gesti iniziali

- Mano aperta: rilevamento/presenza della mano.
- Pizzico pollice-indice: evento di selezione/afferra.
- Movimento laterale: evento di scorrimento.
- Due mani che si separano/avvicinano: evento di zoom avanti/indietro.

Gli eventi compaiono nel flusso eventi dell'HUD e nel log. Questa prima integrazione
riconosce i gesti, ma non simula ancora clic del mouse né modifica automaticamente
ogni pannello QML: le azioni visive specifiche vanno calibrate sul comportamento
reale dell'HUD e sui gesti del video di riferimento.

## Attivazione

La camera viene aperta solo se richiesta esplicitamente:

```bash
cd ~/Desktop/Jarvis
source venv/bin/activate
JARVIS_GESTI=1 python jarvis.py
```

Senza la variabile `JARVIS_GESTI=1`, Jarvis si avvia come prima e non apre la camera.
macOS può chiedere il permesso fotocamera per Terminale o per l'app che avvia Python.

## Installazione e compatibilità

Le dipendenze sono separate da `requirements.txt` perché MediaPipe e OpenCV
potrebbero non avere pacchetti compatibili con tutte le combinazioni di Python,
macOS High Sierra 10.13 e Intel. Provare:

```bash
python -m pip install -r requirements-gesti.txt
python -c "import cv2, mediapipe; print(cv2.__version__, mediapipe.__version__)"
```

Se l'installazione fallisce, non installare versioni casuali in `requirements.txt`:
il modulo è opzionale e il resto di Jarvis continua a funzionare senza di esso.
