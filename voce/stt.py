"""
Speech-to-Text (STT) di Jarvis.

Adattamento del modulo originale del Voice Pack italiano alla struttura
attuale della repository Jarvis.

Motori:
- SpeechRecognition + microfono come motore STT compatibile e semplice.
- Google Speech Recognition come riconoscimento remoto quando disponibile.

Il modulo è progettato per essere importabile anche quando SpeechRecognition
o PyAudio non sono installati: in quel caso Jarvis non va in crash e lo
stato del motore indica chiaramente che l'STT non è disponibile.

Nota:
Per il riconoscimento offline continuo/wake-word di Jarvis, il motore Vosk
presente nella repository rimane il componente dedicato. Questa classe è
un livello STT riutilizzabile per comandi vocali.
"""

from __future__ import annotations

import threading
from typing import Optional

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    sr = None
    HAS_SPEECH_RECOGNITION = False


class SpeechToText:
    """Converte l'audio del microfono in testo."""

    def __init__(
        self,
        language: str = "it_IT",
        ambient_noise_duration: float = 0.8,
        pause_threshold: float = 0.8,
        phrase_threshold: float = 0.2,
        non_speaking_duration: float = 0.5,
        energy_threshold: Optional[int] = None,
        auto_calibrate: bool = True,
    ) -> None:
        self.language = self._normalizza_lingua(language)
        self.ambient_noise_duration = max(0.0, float(ambient_noise_duration))
        self._lock = threading.RLock()
        self._busy = False
        self.last_error: Optional[str] = None
        self.last_text: Optional[str] = None
        self.microphone = None

        if not HAS_SPEECH_RECOGNITION:
            self.recognizer = None
            self.last_error = "SpeechRecognition non installato."
            return

        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.pause_threshold = max(0.1, float(pause_threshold))
            self.recognizer.phrase_threshold = max(0.0, float(phrase_threshold))
            self.recognizer.non_speaking_duration = max(
                0.0, float(non_speaking_duration)
            )

            if energy_threshold is not None:
                self.recognizer.energy_threshold = int(energy_threshold)
                self.recognizer.dynamic_energy_threshold = False
            else:
                self.recognizer.dynamic_energy_threshold = True

            self.microphone = sr.Microphone()

            if auto_calibrate:
                self.calibra_rumore()

        except Exception as errore:
            self.recognizer = None
            self.microphone = None
            self.last_error = str(errore)
            print(f"⚠️ STT non disponibile: {errore}")

    def calibra_rumore(self, duration: Optional[float] = None) -> bool:
        """Calibra il riconoscitore sul rumore ambientale."""
        if not self.disponibile:
            return False

        durata = (
            self.ambient_noise_duration
            if duration is None
            else max(0.0, float(duration))
        )

        try:
            with self._lock:
                with self.microphone as source:
                    print("🎧 Calibrazione del rumore ambientale...")
                    self.recognizer.adjust_for_ambient_noise(
                        source,
                        duration=durata,
                    )

            self.last_error = None
            print("✅ Calibrazione STT completata")
            return True

        except Exception as errore:
            self.last_error = str(errore)
            print(f"⚠️ Impossibile calibrare il microfono: {errore}")
            return False

    def recognize(
        self,
        timeout: Optional[float] = 10,
        phrase_time_limit: Optional[float] = None,
        prompt: bool = True,
    ) -> Optional[str]:
        """
        Ascolta il microfono e restituisce il testo riconosciuto.

        Args:
            timeout: secondi massimi da attendere prima che inizi una frase.
            phrase_time_limit: durata massima della frase.
            prompt: mostra il messaggio di ascolto nel terminale.

        Returns:
            Testo riconosciuto oppure None.
        """
        if not self.disponibile:
            return None

        with self._lock:
            if self._busy:
                self.last_error = "Il riconoscimento vocale è già in esecuzione."
                return None
            self._busy = True

        try:
            self.last_error = None

            with self.microphone as source:
                if prompt:
                    print("🎤 Parla ora...")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            try:
                text = self.recognizer.recognize_google(
                    audio,
                    language=self.language,
                )
            except sr.UnknownValueError:
                self.last_error = "Audio non comprensibile."
                print("❌ Non ho capito, puoi ripetere?")
                return None
            except sr.RequestError as errore:
                self.last_error = f"Servizio di riconoscimento non disponibile: {errore}"
                print(f"❌ Errore servizio STT: {errore}")
                return None

            testo = self._normalizza_testo(text)
            if not testo:
                self.last_error = "Nessun testo riconosciuto."
                return None

            self.last_text = testo
            return testo

        except sr.WaitTimeoutError:
            self.last_error = "Timeout: nessun audio rilevato."
            print("❌ Timeout - nessun audio rilevato")
            return None
        except OSError as errore:
            self.last_error = f"Errore dispositivo audio: {errore}"
            print(f"❌ Errore microfono/audio: {errore}")
            return None
        except Exception as errore:
            self.last_error = str(errore)
            print(f"❌ Errore riconoscimento: {errore}")
            return None
        finally:
            with self._lock:
                self._busy = False

    def riconosci(
        self,
        timeout: Optional[float] = 10,
        phrase_time_limit: Optional[float] = None,
        prompt: bool = True,
    ) -> Optional[str]:
        """Alias italiano di :meth:`recognize` per Jarvis."""
        return self.recognize(
            timeout=timeout,
            phrase_time_limit=phrase_time_limit,
            prompt=prompt,
        )

    @property
    def disponibile(self) -> bool:
        """True se SpeechRecognition e il microfono sono disponibili."""
        return bool(
            HAS_SPEECH_RECOGNITION
            and self.recognizer is not None
            and self.microphone is not None
        )

    @property
    def in_ascolto(self) -> bool:
        """True mentre il riconoscimento è in corso."""
        return self._busy

    def stato(self) -> dict:
        """Restituisce lo stato completo del motore STT."""
        return {
            "disponibile": self.disponibile,
            "motore": "speech-recognition-google" if self.disponibile else "nessuno",
            "lingua": self.language,
            "microfono_disponibile": self.microphone is not None,
            "in_ascolto": self.in_ascolto,
            "ultimo_testo": self.last_text,
            "ultimo_errore": self.last_error,
        }

    def ferma(self) -> bool:
        """
        Interrompe lo stato logico di ascolto.

        SpeechRecognition non espone un'interruzione affidabile di
        listen() già bloccante; il metodo quindi serve soprattutto come
        API comune per Jarvis e impedisce nuove sessioni concorrenti.
        """
        with self._lock:
            if self._busy:
                self.last_error = "Arresto richiesto durante l'ascolto."
            return True

    @staticmethod
    def _normalizza_lingua(language: str) -> str:
        lingua = str(language or "it_IT").strip()
        return lingua or "it_IT"

    @staticmethod
    def _normalizza_testo(text: object) -> str:
        return " ".join(str(text or "").strip().split())


__all__ = ["SpeechToText", "HAS_SPEECH_RECOGNITION"]
