from voce.ascoltatore import AscoltatoreVoce
from voce.riconoscimento import RiconoscitoreVoce
from voce.sintesi import SintesiVocale
from voce.assistente_voce import AssistenteVoce
from voce.motore_ascolto import MotoreAscolto


class ModuloVoce:
    """
    Modulo voce di Jarvis.

    La sintesi vocale è indipendente dal microfono.
    Quindi Jarvis può parlare anche se il riconoscimento
    vocale non è disponibile.
    """

    def __init__(self, kernel):

        self.kernel = kernel

        self.nome = "Voce"

        self.attivo = False
        self.ascolto_attivo = False
        self.sintesi_attiva = False

        self.config = (
            kernel.config
            if kernel
            else None
        )

        # =========================================================
        # MICROFONO
        # =========================================================

        self.ascoltatore = AscoltatoreVoce()

        # =========================================================
        # RICONOSCIMENTO VOSK
        # =========================================================

        self.riconoscitore = RiconoscitoreVoce(
            self.config
        )

        # =========================================================
        # SINTESI VOCALE
        # =========================================================

        # Passiamo il modulo voce, non la configurazione.
        self.sintesi = SintesiVocale(
            self
        )

        self.voce_jarvis = self.sintesi

        # =========================================================
        # ASSISTENTE
        # =========================================================

        self.assistente = AssistenteVoce(
            self.kernel
        )

        # =========================================================
        # MOTORE ASCOLTO
        # =========================================================

        self.motore = MotoreAscolto(
            self
        )

    def avvia(self):

        try:

            if self.attivo:
                return True

            # -----------------------------------------------------
            # SINTESI VOCALE
            # -----------------------------------------------------

            self.sintesi_attiva = (
                self.sintesi.avvia()
            )

            # -----------------------------------------------------
            # ASCOLTO
            # -----------------------------------------------------

            microfono = False
            modello = False

            try:
                microfono = bool(
                    self.ascoltatore.avvia()
                )
            except Exception as errore:
                print(
                    f"Microfono non disponibile: {errore}"
                )

            try:
                modello = bool(
                    self.riconoscitore.avvia()
                )
            except Exception as errore:
                print(
                    f"Riconoscimento vocale non disponibile: {errore}"
                )

            # -----------------------------------------------------
            # MOTORE VOCALE
            # -----------------------------------------------------

            if microfono and modello:

                self.ascolto_attivo = True

                try:
                    self.assistente.avvia()
                except Exception:
                    pass

                self.motore.avvia()

            else:

                self.ascolto_attivo = False

                try:
                    self.ascoltatore.ferma()
                except Exception:
                    pass

                try:
                    self.riconoscitore.ferma()
                except Exception:
                    pass

            # -----------------------------------------------------
            # MODULO ATTIVO
            # -----------------------------------------------------

            self.attivo = (
                self.sintesi_attiva
                or self.ascolto_attivo
            )

            # -----------------------------------------------------
            # MESSAGGIO DI AVVIO
            # -----------------------------------------------------

            if self.sintesi_attiva:

                if self.ascolto_attivo:

                    self.rispondi(
                        "Sistema vocale Jarvis attivo."
                    )

                else:

                    self.rispondi(
                        "Sistema vocale Jarvis attivo. "
                        "Il riconoscimento vocale non è disponibile."
                    )

            return True

        except Exception as errore:

            print(
                f"Errore avvio modulo voce: {errore}"
            )

            self.attivo = False
            self.sintesi_attiva = False
            self.ascolto_attivo = False

            return False

    def ascolta_comando(self):

        if not self.ascolto_attivo:
            return None

        try:

            audio = self.ascoltatore.ascolta()

            if not audio:
                return None

            return self.riconoscitore.riconosci(
                audio
            )

        except Exception as errore:

            print(
                f"Errore ascolto comando: {errore}"
            )

            return None

    def elabora_voce(self, testo):

        try:

            return self.assistente.elabora(
                testo
            )

        except Exception as errore:

            print(
                f"Errore elaborazione voce: {errore}"
            )

            return None

    def rispondi(self, testo):

        if not self.sintesi_attiva:
            return False

        if testo is None:
            return False

        testo = str(testo).strip()

        if not testo:
            return False

        try:

            return self.sintesi.parla(
                testo
            )

        except Exception as errore:

            print(
                f"Errore sintesi vocale: {errore}"
            )

            return False

    def ferma(self):

        try:

            self.motore.ferma()

        except Exception:
            pass

        try:

            self.assistente.ferma()

        except Exception:
            pass

        try:

            self.ascoltatore.ferma()

        except Exception:
            pass

        try:

            self.riconoscitore.ferma()

        except Exception:
            pass

        try:

            self.sintesi.ferma()

        except Exception:
            pass

        self.attivo = False
        self.ascolto_attivo = False
        self.sintesi_attiva = False

        return True

    def stato(self):

        return {
            "nome":
                self.nome,

            "stato":
                "attivo"
                if self.attivo
                else "spento",

            "ascolto":
                "attivo"
                if self.ascolto_attivo
                else "spento",

            "sintesi":
                self.sintesi.stato(),

            "riconoscimento":
                self.riconoscitore.stato(),

            "assistente":
                self.assistente.stato(),

            "motore_ascolto":
                self.motore.stato()
        }
