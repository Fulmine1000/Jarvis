"""Filtro audio leggero per Jarvis.

Priorita:
1. Soppressione WebRTC (pywebrtc-audio), se installata e compatibile.
2. Filtro di ripiego senza dipendenze: passa-alto contro i rombi bassi e
   attenuazione adattiva dei blocchi a basso livello.

Il filtro non registra né salva audio su disco.
"""
from __future__ import annotations

import array
import importlib.util
import math
import sys


class FiltroRumore:
    """Riduce rumori ambientali prima che l'audio arrivi a Vosk."""

    def __init__(self, frequenza: int = 16000, livello: int = 2):
        self.frequenza = int(frequenza)
        self.livello = max(1, min(3, int(livello)))
        self._processor = None
        self._numpy = None
        self._errore = None
        self._attivo = True
        self._rumore_rms = 100.0
        self._ingresso_precedente = 0.0
        self._uscita_precedente = 0.0
        self._alpha = 0.97
        self.modalita = "filtro-adattivo"

    def avvia(self) -> bool:
        """Prova ad attivare WebRTC; se manca, usa il filtro integrato."""
        try:
            if importlib.util.find_spec("pywebrtc_audio") is None:
                self._errore = "pywebrtc-audio non installato; uso filtro adattivo"
                return True
            import numpy as np
            from pywebrtc_audio import AudioProcessor

            self._numpy = np
            self._processor = AudioProcessor(
                sample_rate=self.frequenza,
                num_channels=1,
                noise_suppression=True,
                high_pass_filter=True,
                auto_gain_control=False,
                ns_level=self.livello,
            )
            self.modalita = "webrtc"
            self._errore = None
            return True
        except (ImportError, ModuleNotFoundError, OSError, RuntimeError, TypeError, ValueError) as errore:
            self._processor = None
            self._numpy = None
            self.modalita = "filtro-adattivo"
            self._errore = (
                f"WebRTC non disponibile ({errore}); uso filtro adattivo"
            )
            return True

    def processa(self, audio: bytes) -> bytes:
        """Filtra un blocco PCM mono int16, mantenendo il formato atteso da Vosk."""
        if not audio:
            return audio

        # WebRTC è preferito: sopprime il rumore in modo più selettivo di un gate.
        if self._processor is not None and self._numpy is not None:
            try:
                campioni = self._numpy.frombuffer(audio, dtype=self._numpy.int16)
                if campioni.size == 0:
                    return audio
                puliti = self._processor.process(campioni)
                return self._numpy.asarray(puliti, dtype=self._numpy.int16).tobytes()
            except (BufferError, OSError, RuntimeError, TypeError, ValueError) as errore:
                # Un errore del filtro non deve mai bloccare il microfono.
                self._errore = f"Errore WebRTC ({errore}); uso filtro adattivo"
                self._processor = None
                self._numpy = None
                self.modalita = "filtro-adattivo"

        campioni = array.array("h")
        campioni.frombytes(audio[: len(audio) - (len(audio) % 2)])
        if not campioni:
            return audio

        if sys.byteorder != "little":
            campioni.byteswap()

        filtrati = array.array("h")
        somma_quadrati = 0.0

        # Passa-alto IIR: attenua ronzii e vibrazioni a bassa frequenza.
        for campione in campioni:
            uscita = self._alpha * (
                self._uscita_precedente + float(campione) - self._ingresso_precedente
            )
            self._ingresso_precedente = float(campione)
            self._uscita_precedente = uscita
            limitato = max(-32768, min(32767, int(uscita)))
            filtrati.append(limitato)
            somma_quadrati += limitato * limitato

        rms = math.sqrt(somma_quadrati / len(filtrati))
        soglia_aggiornamento = max(self._rumore_rms * 4.0, 600.0)

        # Il livello di fondo si aggiorna soprattutto sui blocchi non forti;
        # una voce più alta non alza immediatamente la soglia del filtro.
        if rms <= soglia_aggiornamento:
            self._rumore_rms = (0.94 * self._rumore_rms) + (0.06 * rms)

        soglia = max(180.0, self._rumore_rms * (1.8 + (0.15 * (self.livello - 1))))
        if rms < soglia and rms > 0:
            rapporto = max(0.18, min(1.0, rms / soglia))
            attenuazione = 0.25 + (0.35 * rapporto)
            for indice, valore in enumerate(filtrati):
                filtrati[indice] = int(valore * attenuazione)

        if sys.byteorder != "little":
            filtrati.byteswap()
        risultato = filtrati.tobytes()
        # Conserva eventuale byte finale incompleto, anche se i blocchi normali
        # di sounddevice sono sempre allineati a campioni PCM.
        if len(audio) % 2:
            risultato += audio[-1:]
        return risultato

    def stato(self) -> dict:
        return {
            "attivo": self._attivo,
            "modalita": self.modalita,
            "frequenza": self.frequenza,
            "livello": self.livello,
            "webrtc_disponibile": self._processor is not None,
            "ultimo_errore": self._errore,
        }

    def reset(self) -> None:
        """Azzera la stima del rumore e lo stato del passa-alto."""
        self._rumore_rms = 100.0
        self._ingresso_precedente = 0.0
        self._uscita_precedente = 0.0
        if self._processor is not None:
            try:
                self._processor.reset()
            except (AttributeError, OSError, RuntimeError):
                pass
