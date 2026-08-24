import queue

try:
    import sounddevice as sd
except (ImportError, OSError):
    sd = None


class AscoltatoreVoce:
    """Acquisisce audio dal microfono con fallback sicuro in modalità testo."""

    def __init__(self, frequenza=16000, blocksize=8000):
        self.nome = "Ascoltatore Voce"
        self.frequenza = int(frequenza)
        self.blocksize = int(blocksize)
        self.audio = queue.Queue(maxsize=40)
        self.attivo = False
        self.stream = None
        self.disponibile = sd is not None
        self.ultimo_errore = None

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
        if not self.disponibile:
            self.attivo = False
            self.ultimo_errore = "sounddevice/PortAudio non disponibile"
            return False
        try:
            self.pulisci_buffer()
            self.stream = sd.RawInputStream(
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
