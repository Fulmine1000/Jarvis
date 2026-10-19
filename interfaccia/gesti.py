"""Controllo gestuale opzionale per l'HUD di J.A.R.V.I.S.

Dipendenze opzionali: opencv-python e mediapipe.
Non salva immagini o video. La camera viene aperta solo quando il modulo
viene avviato esplicitamente dal launcher (JARVIS_GESTI=1).
"""
from __future__ import annotations

import math
import threading
import time
from typing import Callable, Optional


class ControlloGesti:
    """Rileva gesti semplici in un thread e li consegna a una callback."""

    def __init__(
        self,
        callback: Callable[[str], None],
        camera: int = 0,
        logger=None,
        cooldown: float = 0.9,
    ):
        self.callback = callback
        self.camera = camera
        self.logger = logger
        self.cooldown = max(0.4, float(cooldown))
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._ultimo_gesto = ""
        self._ultimo_tempo = 0.0
        self._ultimo_x = None
        self._ultimo_movimento = 0.0
        self._distanza_due_mani = None
        self.disponibile = False

    def avvia(self) -> bool:
        if self._thread and self._thread.is_alive():
            return True
        try:
            import cv2  # noqa: F401
            import mediapipe as mp  # noqa: F401
        except Exception as errore:
            self._log(f"Controllo gestuale non disponibile: installare requirements-gesti.txt ({errore})")
            return False
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._esegui, name="JarvisGesti", daemon=True
        )
        self._thread.start()
        self.disponibile = True
        self._log("Controllo gestuale avviato: la camera elabora i fotogrammi localmente.")
        return True

    def ferma(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self.disponibile = False

    def _log(self, messaggio: str) -> None:
        try:
            if self.logger:
                self.logger.info(messaggio)
        except Exception:
            pass

    def _emetti(self, gesto: str, forza: bool = False) -> None:
        adesso = time.monotonic()
        if not forza and (gesto == self._ultimo_gesto and adesso - self._ultimo_tempo < self.cooldown):
            return
        if not forza and adesso - self._ultimo_tempo < self.cooldown:
            return
        self._ultimo_gesto = gesto
        self._ultimo_tempo = adesso
        try:
            self.callback(gesto)
        except Exception as errore:
            self._log(f"Errore callback gestuale: {errore}")

    @staticmethod
    def _distanza(a, b) -> float:
        return math.hypot(a.x - b.x, a.y - b.y)

    @staticmethod
    def _dita_alzate(landmarks) -> int:
        # Indice, medio, anulare e mignolo: confronta la punta con
        # l'articolazione sottostante; il pollice usa la coordinata x.
        count = 0
        for punta, articolazione in ((8, 6), (12, 10), (16, 14), (20, 18)):
            if landmarks[punta].y < landmarks[articolazione].y:
                count += 1
        if abs(landmarks[4].x - landmarks[2].x) > 0.06:
            count += 1
        return count

    def _esegui(self) -> None:
        import cv2
        import mediapipe as mp

        hands_api = mp.solutions.hands
        disegno = mp.solutions.drawing_utils
        cap = cv2.VideoCapture(self.camera)
        if not cap.isOpened():
            self._log("Controllo gestuale: impossibile aprire la camera.")
            self.disponibile = False
            return
        try:
            with hands_api.Hands(
                static_image_mode=False,
                max_num_hands=2,
                model_complexity=0,
                min_detection_confidence=0.65,
                min_tracking_confidence=0.55,
            ) as hands:
                while not self._stop.is_set():
                    ok, frame = cap.read()
                    if not ok:
                        time.sleep(0.05)
                        continue
                    frame = cv2.flip(frame, 1)
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    risultato = hands.process(rgb)
                    if not risultato.multi_hand_landmarks:
                        self._distanza_due_mani = None
                        self._ultimo_x = None
                        continue

                    tutte = risultato.multi_hand_landmarks
                    for mano in tutte:
                        disegno.draw_landmarks(frame, mano, hands_api.HAND_CONNECTIONS)
                    punti = [mano.landmark for mano in tutte]
                    prima = punti[0]
                    dita = self._dita_alzate(prima)
                    pollice = prima[4]
                    indice = prima[8]
                    distanza_pizzico = self._distanza(pollice, indice)

                    # Pizzico: selezione/afferra; mano aperta: interazione pronta.
                    if distanza_pizzico < 0.045:
                        self._emetti("pizzico")
                    elif dita >= 4:
                        self._emetti("mano_aperta")

                    # Scorrimento laterale con il polso, filtrato per ridurre falsi positivi.
                    x = prima[0].x
                    adesso = time.monotonic()
                    if self._ultimo_x is not None and abs(x - self._ultimo_x) > 0.18 and adesso - self._ultimo_movimento > 0.7:
                        self._emetti("scorri_destra" if x > self._ultimo_x else "scorri_sinistra")
                        self._ultimo_movimento = adesso
                    self._ultimo_x = x

                    # Distanza tra i polsi di due mani: indica zoom avanti/indietro.
                    if len(punti) >= 2:
                        distanza = self._distanza(punti[0][0], punti[1][0])
                        if self._distanza_due_mani is not None:
                            delta = distanza - self._distanza_due_mani
                            if delta > 0.09:
                                self._emetti("zoom_avanti")
                            elif delta < -0.09:
                                self._emetti("zoom_indietro")
                        self._distanza_due_mani = distanza
                    else:
                        self._distanza_due_mani = None
        except Exception as errore:
            self._log(f"Controllo gestuale terminato per errore: {errore}")
        finally:
            cap.release()
            self.disponibile = False
            self._log("Controllo gestuale arrestato.")
