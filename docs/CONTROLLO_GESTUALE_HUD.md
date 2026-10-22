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

**Visualizzatore 3D:** non richiede pacchetti Python. Avvia Jarvis e apri **APRI MODELLO 3D**: Chrome richiede il permesso per la fotocamera e riconosce le mani nel browser tramite MediaPipe JavaScript. È necessaria Internet per caricare le librerie dalla CDN; i fotogrammi non vengono salvati.

**Controllo gestuale dell'HUD:** è una funzione Python separata e opzionale. Per attivarla all'avvio, installa le dipendenze e imposta `JARVIS_GESTI=1`:

```bash
cd ~/Desktop/Jarvis
source venv/bin/activate
python -m pip install -r requirements-gesti.txt
JARVIS_GESTI=1 python jarvis.py
```

Queste dipendenze Python possono non essere compatibili con ogni versione di Python o sistema operativo.

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
