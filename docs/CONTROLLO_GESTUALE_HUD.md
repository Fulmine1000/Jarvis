# Controllo gestuale HUD e ologramma 3D

Il visualizzatore 3D usa **MediaPipe Tasks Vision — Hand Landmarker**, lo stesso approccio basato sui landmark delle mani mostrato nel riferimento Gesture Synth.

## Rilevamento

- Webcam richiesta dal browser soltanto quando si apre il visualizzatore.
- Due mani contemporaneamente, con 21 landmark per mano.
- Scheletro e punti delle dita disegnati sopra l’anteprima della webcam.
- Inferenza in un Web Worker con delegate CPU: il rendering dell’ologramma resta separato dal rilevamento.
- Risoluzione webcam ridotta (256×192), massimo circa 10 fotogrammi al secondo per limitare il carico sul PC.
- I fotogrammi vengono elaborati localmente in memoria; non vengono salvati né inviati a un server. Il browser scarica da CDN il codice WASM e il modello MediaPipe al primo avvio.

## Gesti dell’ologramma

- **Pizzico pollice-indice:** attiva/disattiva l’impulso del nucleo.
- **Una mano:** movimento laterale per ruotare l’ologramma.
- **Due mani:** allontanandole/avvicinandole si regola lo zoom.
- **Mano aperta:** presenza e tracciamento, senza attivare comandi di sistema.

Le soglie sono normalizzate rispetto al palmo per ridurre i falsi positivi dovuti alla distanza dalla webcam.

## Avvio e privacy

1. Avvia Jarvis.
2. Pronuncia o digita **“apri ologramma 3D”**.
3. Consenti l’accesso alla webcam nel browser.
4. Mantieni le mani interamente visibili e illuminate.

Il viewer è servito soltanto su `127.0.0.1`. La webcam si arresta quando si chiude la pagina. Per il caricamento iniziale del motore e del modello è necessaria una connessione Internet; il riconoscimento delle immagini avviene sul PC.

## Compatibilità

Non occorre installare MediaPipe o OpenCV in Python per il viewer 3D. Il modulo Python opzionale `interfaccia/gesti.py` resta separato e non è necessario per questa funzione. Il resto di Jarvis continua a funzionare anche se il browser non supporta webcam, WebAssembly o Web Worker.
