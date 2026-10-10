from __future__ import annotations

import threading

from voce.ascoltatore import AscoltatoreVoce
from voce.riconoscimento import RiconoscitoreVoce
from voce.sintesi import SintesiVocale
from voce.assistente_voce import AssistenteVoce
from voce.motore_ascolto import MotoreAscolto


class ModuloVoce:
    """Gestisce sintesi, microfono e riconoscimento senza bloccare Jarvis in modalita testo."""

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
        self.ultimo_errore_ascolto = None

    def avvia(self):
        if self.attivo:
            return True

        try:
            self.sintesi_attiva = bool(self.sintesi.avvia())

            # Prima verifica il microfono. Se non e disponibile non carichiamo
            # Vosk: in questo modo l'avvio solo-testo non tocca librerie native.
            microfono = self.ascoltatore.avvia()
            if not microfono:
                self.riconoscitore.ferma()
                self.ascoltatore.ferma()
                self.ascolto_attivo = False
                self.attivo = True
                if self.kernel and self.kernel.logger:
                    dettaglio = self.ascoltatore.ultimo_errore or "errore non specificato"
                    self.kernel.logger.warning(
                        f"Microfono non disponibile ({dettaglio}): modalita solo-testo attiva."
                    )
                return True

            modello = self.riconoscitore.avvia()
            if not modello:
                self.ascoltatore.ferma()
                self.riconoscitore.ferma()
                self.ascolto_attivo = False
                self.attivo = True
                if self.kernel and self.kernel.logger:
                    dettaglio = self.riconoscitore.ultimo_errore or "modello o backend non disponibile"
                    self.kernel.logger.warning(
                        f"Riconoscimento vocale non disponibile ({dettaglio}): modalita solo-testo attiva."
                    )
                return True

            self.ascolto_attivo = True
            if self.kernel and self.kernel.logger:
                stato = self.riconoscitore.stato()
                self.kernel.logger.info(
                    f"Riconoscimento vocale attivo: backend={stato.get('backend')}, "
                    f"sample_rate={stato.get('sample_rate')}, modello={stato.get('modello')}"
                )
            self.assistente.avvia()
            self.motore.avvia()
            self.attivo = True
            return True

        except Exception as errore:
            try:
                self.motore.ferma()
                self.assistente.ferma()
                self.ascoltatore.ferma()
                self.riconoscitore.ferma()
            except Exception:
                pass
            self.attivo = True
            self.ascolto_attivo = False
            if self.kernel and self.kernel.logger:
                self.kernel.logger.warning(f"Voce non disponibile: modalita solo-testo attiva ({errore})")
            return True

    def ascolta_comando(self):
        """Acquisisce audio senza modificare lo stato LISTENING dell'HUD.

        Il microfono resta aperto continuamente per poter rilevare la wake word.
        Per questo motivo ogni blocco audio NON deve essere rappresentato come
        un nuovo ingresso/uscita dalla modalita LISTENING: lo stato visuale
        viene gestito dal MotoreAscolto in base alla wake word.
        """
        if not self.ascolto_attivo:
            return None
        try:
            audio = self.ascoltatore.ascolta()
            if not audio:
                return None
            testo = self.riconoscitore.riconosci(audio)
            if testo:
                self.ultimo_errore_ascolto = None
            return testo
        except Exception as errore:
            messaggio = f"{type(errore).__name__}: {errore}"
            if messaggio != self.ultimo_errore_ascolto:
                self.ultimo_errore_ascolto = messaggio
                if self.kernel and self.kernel.logger:
                    self.kernel.logger.warning(
                        f"Errore durante l'ascolto/riconoscimento: {messaggio}"
                    )
                else:
                    print(f"Errore durante l'ascolto/riconoscimento: {messaggio}")
            return None

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
            if self.kernel and self.kernel.logger:
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
            "ultimo_errore_ascolto": self.ultimo_errore_ascolto,
        }
