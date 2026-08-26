from __future__ import annotations

import importlib.util
import queue
import sys


class AscoltatoreVoce:
    """Acquisisce audio dal microfono senza inizializzare PortAudio in modalita testo."""

    def __init__(self, frequenza=16000, blocksize=8000):
        self.nome = "Ascoltatore Voce"
        self.frequenza = int(frequenza)
        self.blocksize = int(blocksize)
        self.audio = queue.Queue(maxsize=40)
        self.attivo = False
        self.stream = None
        self.disponibile = self._sounddevice_disponibile()
        self.ultimo_errore = None
        self._sd = None

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

    def callback(self, ingresso, frames, tempo, stato):
        if stato:
            self.ultimo_errore = str(stato)
        try:
            self.audio.put_nowait(bytes(ingresso))
        except queue.Full:
            try:
                self.audio.get_nowait()
                self.audio.put_nowait(bytes(ingresso))
            except queue.Empty:
                pass

    def avvia(self):
        if self.attivo:
            return True
        if not self.disponibile or not self._sounddevice_disponibile():
            self.attivo = False
            self.disponibile = False
            self.ultimo_errore = "sounddevice/PortAudio non disponibile"
            return False
        if not self._carica_sounddevice():
            self.attivo = False
            return False

        try:
            self.pulisci_buffer()
            self.stream = self._sd.RawInputStream(
                samplerate=self.frequenza,
                blocksize=self.blocksize,
                dtype="int16",
                channels=1,
                callback=self.callback,
            )
            self.stream.start()
            self.attivo = True
            self.ultimo_errore = None
            return True
        except (OSError, RuntimeError, ValueError) as errore:
            self.attivo = False
            self.ultimo_errore = str(errore)
            if self.stream is not None:
                try:
                    self.stream.close()
                except (OSError, RuntimeError):
                    pass
                self.stream = None
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
        self.pulisci_buffer()
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
            "ultimo_errore": self.ultimo_errore,
            "buffer": self.audio.qsize(),
        }
