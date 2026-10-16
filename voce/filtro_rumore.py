"""Filtro antirumore fail-safe per l'audio di Jarvis.

Usa la soppressione spettrale WebRTC quando disponibile. Se la libreria manca
o genera un errore, il fallback applica soltanto un passa-alto leggero: non
usa un noise gate basato sul volume, perché potrebbe tagliare parole pronunciate
a bassa voce. In caso di errore del DSP il blocco corrente passa invariato.

Formato: PCM signed int16, mono, little-endian, alla frequenza configurata.
Il filtro non salva e non registra audio su disco.
"""
from __future__ import annotations

import array
import importlib.util
import math
import sys


class FiltroRumore:
    """Riduce il rumore senza sopprimere blocchi vocali silenziosi."""

    def __init__(self, frequenza: int = 16000, livello: int = 1):
        self.frequenza = max(8000, int(frequenza))
        self.livello = max(1, min(3, int(livello)))
        self._processor = None
        self._numpy = None
        self._errore = None
        self._attivo = True
        self._ingresso_precedente = 0.0
        self._uscita_precedente = 0.0
        self._blocchi_protetti = 0
        self._ultimo_rms_ingresso = 0.0
        self._ultimo_rms_uscita = 0.0
        # Passa-alto molto leggero: rimuove DC/ronzii bassi senza fare gating.
        self._alpha = 0.985
        self.modalita = "passa-alto-sicuro"

    @staticmethod
    def _rms_pcm(audio: bytes) -> float:
        """RMS PCM senza dipendenze esterne, per rilevare output quasi azzerati."""
        campioni = array.array("h")
        campioni.frombytes(audio[: len(audio) - (len(audio) % 2)])
        if not campioni:
            return 0.0
        if sys.byteorder != "little":
            campioni.byteswap()
        return math.sqrt(sum(int(c) * int(c) for c in campioni) / len(campioni))

    def avvia(self) -> bool:
        """Inizializza WebRTC; il microfono resta utilizzabile anche se fallisce."""
        try:
            if importlib.util.find_spec("pywebrtc_audio") is None:
                self._processor = None
                self._numpy = None
                self.modalita = "passa-alto-sicuro"
                self._errore = "pywebrtc-audio non installato; uso passa-alto sicuro"
                return True

            import numpy as np
            from pywebrtc_audio import AudioProcessor

            processor = AudioProcessor(
                sample_rate=self.frequenza,
                num_channels=1,
                noise_suppression=True,
                high_pass_filter=True,
                auto_gain_control=False,
                ns_level=self.livello,
            )
            self._numpy = np
            self._processor = processor
            self.modalita = "webrtc"
            self._errore = None
        except Exception as errore:
            # La riduzione del rumore è opzionale: mai bloccare l'ascolto.
            self._processor = None
            self._numpy = None
            self.modalita = "passa-alto-sicuro"
            self._errore = f"WebRTC non disponibile ({errore}); uso passa-alto sicuro"
        return True

    def processa(self, audio: bytes) -> bytes:
        """Elabora PCM int16 e restituisce sempre un blocco della stessa lunghezza."""
        if not audio:
            return audio

        # RawInputStream usa PCM int16. Gestiamo anche un eventuale byte finale
        # incompleto senza far fallire NumPy né perdere dati.
        parte_intera = audio[: len(audio) - (len(audio) % 2)]
        byte_finale = audio[len(parte_intera):]
        if not parte_intera:
            return audio

        if self._processor is not None and self._numpy is not None:
            try:
                campioni = self._numpy.frombuffer(parte_intera, dtype=self._numpy.int16)
                puliti = self._processor.process(campioni)
                puliti = self._numpy.asarray(puliti, dtype=self._numpy.int16)
                if puliti.size != campioni.size:
                    raise ValueError(
                        f"lunghezza WebRTC inattesa: {puliti.size} campioni, "
                        f"attesi {campioni.size}"
                    )
                risultato = puliti.tobytes() + byte_finale
                if len(risultato) != len(audio):
                    raise ValueError("lunghezza del blocco WebRTC non valida")

                # Fail-safe aggiuntivo: se il DSP cancella quasi tutto un blocco
                # che aveva energia udibile, preserviamo il PCM originale.
                # La riduzione del rumore non deve trasformarsi in un mute.
                rms_ingresso = self._rms_pcm(parte_intera)
                rms_uscita = self._rms_pcm(risultato)
                if rms_ingresso >= 120 and rms_uscita < rms_ingresso * 0.04:
                    self._blocchi_protetti = getattr(self, "_blocchi_protetti", 0) + 1
                    self._ultimo_rms_ingresso = rms_ingresso
                    self._ultimo_rms_uscita = rms_uscita
                    return audio

                self._ultimo_rms_ingresso = rms_ingresso
                self._ultimo_rms_uscita = rms_uscita
                return risultato
            except Exception as errore:
                # Fail-open: il blocco che ha causato l'errore arriva a Vosk
                # originale, senza attenuazioni o perdita di parole.
                self._errore = f"Errore WebRTC ({errore}); blocco passato invariato"
                self._processor = None
                self._numpy = None
                self.modalita = "passa-alto-sicuro"
                return audio

        try:
            campioni = array.array("h")
            campioni.frombytes(parte_intera)
            if sys.byteorder != "little":
                campioni.byteswap()

            filtrati = array.array("h")
            ingresso_precedente = self._ingresso_precedente
            uscita_precedente = self._uscita_precedente
            for campione in campioni:
                valore = float(campione)
                uscita = self._alpha * (uscita_precedente + valore - ingresso_precedente)
                ingresso_precedente = valore
                uscita_precedente = uscita
                filtrati.append(max(-32768, min(32767, int(round(uscita)))))

            self._ingresso_precedente = ingresso_precedente
            self._uscita_precedente = uscita_precedente
            if sys.byteorder != "little":
                filtrati.byteswap()
            risultato = filtrati.tobytes() + byte_finale
            return risultato if len(risultato) == len(audio) else audio
        except Exception as errore:
            # Qualunque problema nel fallback deve preservare l'audio originale.
            self._errore = f"Errore passa-alto ({errore}); blocco passato invariato"
            return audio

    def stato(self) -> dict:
        return {
            "attivo": self._attivo,
            "modalita": self.modalita,
            "frequenza": self.frequenza,
            "livello": self.livello,
            "webrtc_disponibile": self._processor is not None,
            "ultimo_errore": self._errore,
            "blocchi_protetti_da_silenziamento": self._blocchi_protetti,
            "rms_ingresso": round(self._ultimo_rms_ingresso, 1),
            "rms_uscita": round(self._ultimo_rms_uscita, 1),
            "noise_gate": False,
        }

    def reset(self) -> None:
        """Azzera lo stato DSP mantenendo la configurazione."""
        self._ingresso_precedente = 0.0
        self._uscita_precedente = 0.0
        if self._processor is not None:
            try:
                self._processor.reset()
            except Exception as errore:
                self._errore = f"Reset WebRTC non riuscito: {errore}"
                self._processor = None
                self._numpy = None
                self.modalita = "passa-alto-sicuro"
