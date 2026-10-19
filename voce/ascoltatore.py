from __future__ import annotations

import importlib.util
import math
import os
import queue
import struct
import sys

from voce.filtro_rumore import FiltroRumore


class AscoltatoreVoce:
    """Acquisisce PCM dal microfono e riduce il rumore prima di inviarlo a Vosk."""

    def __init__(
        self,
        frequenza=16000,
        blocksize=1600,
        filtro_rumore=True,
        livello_filtro=2,
        soglia_rms_minima=12,
    ):
        self.nome = "Ascoltatore Voce"
        self.frequenza = int(frequenza)
        self.blocksize = int(blocksize)
        # JARVIS_AUDIO_DEVICE può essere un indice PortAudio o parte del nome.
        # Se non è impostato, viene usato il dispositivo predefinito e poi
        # provati gli altri ingressi disponibili in caso di errore.
        self.dispositivo_richiesto = os.environ.get("JARVIS_AUDIO_DEVICE", "").strip()
        self.dispositivo_attivo = None
        self.audio = queue.Queue(maxsize=12)
        self.blocchi_audio_scartati = 0
        self.attivo = False
        self.stream = None
        self.disponibile = self._sounddevice_disponibile()
        self.ultimo_errore = None
        self.ultimo_rms_ingresso = 0
        self.ultimo_rms_uscita = 0
        self.soglia_rms_minima = max(0, int(soglia_rms_minima))
        self.blocchi_sotto_soglia = 0
        self._sd = None
        self.filtro = (
            FiltroRumore(frequenza=self.frequenza, livello=livello_filtro)
            if filtro_rumore
            else None
        )

    @staticmethod
    def _sounddevice_disponibile():
        """Verifica sounddevice rispettando anche i test che bloccano il modulo."""
        if "sounddevice" in sys.modules and sys.modules["sounddevice"] is None:
            return False
        try:
            return importlib.util.find_spec("sounddevice") is not None
        except (ImportError, ModuleNotFoundError, OSError, ValueError):
            return False

    def _carica_sounddevice(self):
        if self._sd is not None:
            return True
        if not self._sounddevice_disponibile():
            self.disponibile = False
            self.ultimo_errore = "sounddevice/PortAudio non disponibile"
            return False
        try:
            import sounddevice as sd
        except (ImportError, ModuleNotFoundError, OSError, RuntimeError) as errore:
            self.disponibile = False
            self.ultimo_errore = str(errore)
            return False
        self._sd = sd
        self.disponibile = True
        return True

    def _candidati_dispositivo(self):
        """Ordina i dispositivi: scelta esplicita, default, poi ingressi validi."""
        sd = self._sd
        candidati = []

        def aggiungi(valore):
            if valore is None:
                return
            try:
                indice = int(valore)
            except (TypeError, ValueError):
                return
            if indice >= 0 and indice not in candidati:
                candidati.append(indice)

        richiesto = self.dispositivo_richiesto
        if richiesto:
            try:
                aggiungi(int(richiesto))
            except ValueError:
                try:
                    dispositivi = sd.query_devices()
                    for indice, dispositivo in enumerate(dispositivi):
                        nome = str(dispositivo.get("name", ""))
                        ingressi = int(dispositivo.get("max_input_channels", 0) or 0)
                        if ingressi > 0 and richiesto.lower() in nome.lower():
                            aggiungi(indice)
                except (OSError, RuntimeError, TypeError, ValueError):
                    pass

        try:
            predefinito = sd.default.device
            if isinstance(predefinito, (tuple, list)):
                predefinito = predefinito[0] if predefinito else None
            aggiungi(predefinito)
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
            pass

        try:
            for indice, dispositivo in enumerate(sd.query_devices()):
                if int(dispositivo.get("max_input_channels", 0) or 0) > 0:
                    aggiungi(indice)
        except (OSError, RuntimeError, TypeError, ValueError):
            pass

        return candidati

    def callback(self, ingresso, frames, tempo, stato):
        if stato:
            self.ultimo_errore = str(stato)

        audio = bytes(ingresso)
        self.ultimo_rms_ingresso = self._rms(audio)
        if self.filtro is not None:
            try:
                audio = self.filtro.processa(audio)
            except Exception as errore:
                self.ultimo_errore = f"Filtro rumore: {errore}"
                audio = bytes(ingresso)

        self.ultimo_rms_uscita = self._rms(audio)
        if self.soglia_rms_minima and self.ultimo_rms_uscita < self.soglia_rms_minima:
            audio = bytes(len(audio))
            self.blocchi_sotto_soglia += 1
        try:
            self.audio.put_nowait(audio)
        except queue.Full:
            try:
                self.audio.get_nowait()
                self.blocchi_audio_scartati += 1
                self.audio.put_nowait(audio)
            except queue.Empty:
                pass

    @staticmethod
    def _rms(audio):
        """Livello RMS PCM, usato solo per diagnosticare il segnale del microfono."""
        campioni = len(audio) // 2
        if campioni <= 0:
            return 0
        valori = struct.unpack("<" + "h" * campioni, audio[:campioni * 2])
        return int(math.sqrt(sum(valore * valore for valore in valori) / campioni))

    def avvia(self):
        if self.attivo:
            return True
        if not self.disponibile or not self._sounddevice_disponibile():
            self.attivo = False
            self.disponibile = False
            self.ultimo_errore = (
                "Il pacchetto Python 'sounddevice' non è installato "
                "nell'ambiente attivo. Per abilitarlo esegui: "
                "python -m pip install sounddevice"
            )
            return False
        if not self._carica_sounddevice():
            self.attivo = False
            return False

        self.pulisci_buffer()
        if self.filtro is not None:
            self.filtro.reset()
            self.filtro.avvia()

        errori = []
        candidati = self._candidati_dispositivo()
        if not candidati:
            candidati = [None]  # lascia scegliere a PortAudio se non può enumerare
        for dispositivo in candidati:
            stream = None
            try:
                stream = self._sd.RawInputStream(
                    samplerate=self.frequenza,
                    blocksize=self.blocksize,
                    dtype="int16",
                    channels=1,
                    device=dispositivo,
                    callback=self.callback,
                )
                stream.start()
                self.stream = stream
                self.dispositivo_attivo = dispositivo
                self.attivo = True
                self.ultimo_errore = None
                return True
            except (OSError, RuntimeError, ValueError) as errore:
                errori.append(f"dispositivo {dispositivo}: {errore}")
                if stream is not None:
                    try:
                        stream.close()
                    except (OSError, RuntimeError):
                        pass

        self.attivo = False
        self.stream = None
        self.dispositivo_attivo = None
        self.ultimo_errore = "Impossibile aprire un ingresso audio. " + " | ".join(errori)
        return False

    def ascolta(self, timeout=1):
        if not self.attivo:
            return None
        try:
            return self.audio.get(timeout=float(timeout))
        except queue.Empty:
            return None

    def pulisci_buffer(self):
        while True:
            try:
                self.audio.get_nowait()
            except queue.Empty:
                return

    def ferma(self):
        self.attivo = False
        if self.stream is not None:
            try:
                self.stream.stop()
            except (OSError, RuntimeError):
                pass
            try:
                self.stream.close()
            except (OSError, RuntimeError):
                pass
            self.stream = None
        self.dispositivo_attivo = None
        self.pulisci_buffer()
        if self.filtro is not None:
            self.filtro.reset()
        return True

    def riavvia(self):
        self.ferma()
        return self.avvia()

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo" if self.attivo else "spento",
            "frequenza": self.frequenza,
            "blocksize": self.blocksize,
            "stream": self.stream is not None,
            "disponibile": self.disponibile,
            "dispositivo_richiesto": self.dispositivo_richiesto or "predefinito",
            "dispositivo_attivo": self.dispositivo_attivo,
            "ultimo_errore": self.ultimo_errore,
            "rms_ingresso": self.ultimo_rms_ingresso,
            "rms_filtrato": self.ultimo_rms_uscita,
            "soglia_rms_minima": self.soglia_rms_minima,
            "blocchi_sotto_soglia": self.blocchi_sotto_soglia,
            "buffer": self.audio.qsize(),
            "buffer_massimo": self.audio.maxsize,
            "blocchi_audio_scartati": self.blocchi_audio_scartati,
            "filtro_rumore": self.filtro.stato() if self.filtro is not None else {
                "attivo": False,
                "modalita": "disattivato",
            },
        }
