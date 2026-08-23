import threading

from voce.ascoltatore import AscoltatoreVoce
from voce.riconoscimento import RiconoscitoreVoce
from voce.sintesi import SintesiVocale
from voce.assistente_voce import AssistenteVoce
from voce.motore_ascolto import MotoreAscolto


class ModuloVoce:
    """Ascolto, wake word, riconoscimento e sintesi vocale di Jarvis."""

    def __init__(self, kernel):
        self.kernel = kernel
        self.nome = "Voce"
        self.attivo = False
        self.ascolto_attivo = False
        self.sintesi_attiva = False
        self.config = kernel.config if kernel else None
        self.ascoltatore = AscoltatoreVoce()
        self.riconoscitore = RiconoscitoreVoce(self.config)
        self.sintesi = SintesiVocale(self.config)
        self.voce_jarvis = self.sintesi
        self.assistente = AssistenteVoce(self.kernel)
        self.motore = MotoreAscolto(self)
        self._speech_lock = threading.RLock()

    def avvia(self):
        if self.attivo:
            return True
        try:
            self.sintesi_attiva = bool(self.sintesi.avvia())
            microfono = self.ascoltatore.avvia()
            modello = self.riconoscitore.avvia()
            if microfono and modello:
                self.ascolto_attivo = True
                self.assistente.avvia()
                self.motore.avvia()
            else:
                self.ascoltatore.ferma()
                self.ascolto_attivo = False
            self.attivo = True
            return True
        except Exception as errore:
            self.kernel.logger.warning(f"Errore avvio modulo voce: {errore}")
            self.attivo = False
            return False

    def ascolta_comando(self):
        if not self.ascolto_attivo:
            return None
        hud = getattr(self.kernel, "hud", None)
        if hud:
            hud.imposta_ascolto(True)
        try:
            audio = self.ascoltatore.ascolta()
            if not audio:
                return None
            return self.riconoscitore.riconosci(audio)
        finally:
            if hud:
                hud.imposta_ascolto(False)

    def elabora_voce(self, testo):
        return self.assistente.elabora(testo)

    def rispondi(self, testo):
        if not self.sintesi_attiva or not testo:
            return False
        hud = getattr(self.kernel, "hud", None)
        with self._speech_lock:
            if hud:
                hud.imposta_parlato(True)
            try:
                return bool(self.sintesi.parla(testo))
            finally:
                if hud:
                    hud.imposta_parlato(False)

    def ferma(self):
        try:
            self.motore.ferma()
            self.assistente.ferma()
            self.ascoltatore.ferma()
            self.riconoscitore.ferma()
            self.sintesi.ferma()
        except Exception as errore:
            self.kernel.logger.warning(f"Errore arresto modulo voce: {errore}")
        self.attivo = False
        self.ascolto_attivo = False
        self.sintesi_attiva = False
        return True

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo" if self.attivo else "spento",
            "ascolto": "attivo" if self.ascolto_attivo else "spento",
            "sintesi": self.sintesi.stato(),
            "riconoscimento": self.riconoscitore.stato(),
            "assistente": self.assistente.stato(),
            "motore_ascolto": self.motore.stato(),
        }
