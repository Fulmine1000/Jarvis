from voce.ascoltatore import AscoltatoreVoce
from voce.riconoscimento import RiconoscitoreVoce
from voce.sintesi import SintesiVocale
from voce.assistente_voce import AssistenteVoce
from voce.motore_ascolto import MotoreAscolto


class ModuloVoce:
    """Modulo voce di Jarvis.

    L'ascolto (microfono + Vosk) è opzionale: se le dipendenze audio o il
    modello Vosk mancano, il modulo resta attivo per la sola sintesi vocale e
    l'assistente può comunque parlare e accettare comandi testuali.
    """

    def __init__(self, kernel):

        self.kernel = kernel

        self.nome = "Voce"

        # attivo = modulo avviato (almeno la sintesi è disponibile)
        self.attivo = False

        # ascolto_attivo = microfono + riconoscimento operativi
        self.ascolto_attivo = False

        # sintesi_attiva = sintesi vocale disponibile
        self.sintesi_attiva = False

        self.config = (
            kernel.config
            if kernel
            else None
        )

        # MICROFONO
        self.ascoltatore = AscoltatoreVoce()

        # RICONOSCIMENTO VOCALE VOSK
        self.riconoscitore = RiconoscitoreVoce(
            self.config
        )

        # SINTESI VOCALE JARVIS
        self.sintesi = SintesiVocale(
            self.config
        )

        self.voce_jarvis = self.sintesi

        # LOGICA ASSISTENTE
        self.assistente = AssistenteVoce(
            self.kernel
        )

        # CICLO ASCOLTO
        self.motore = MotoreAscolto(
            self
        )

    def avvia(self):

        try:

            if self.attivo:
                return True

            # La sintesi non dipende dal microfono: viene sempre avviata.
            self.sintesi_attiva = self.sintesi.avvia()

            # Ascolto: microfono + modello Vosk. Entrambi opzionali.
            microfono = self.ascoltatore.avvia()
            modello = self.riconoscitore.avvia()

            if microfono and modello:

                self.ascolto_attivo = True

                self.assistente.avvia()
                self.motore.avvia()

            else:

                # Nessun ascolto vocale: modalità solo-testo.
                self.ascoltatore.ferma()

                self.ascolto_attivo = False

            # Il modulo è "attivo" se almeno la sintesi è disponibile.
            self.attivo = True

            if self.sintesi_attiva and self.ascolto_attivo:

                self.rispondi(
                    "Sistema vocale Jarvis attivo."
                )

            return True

        except Exception as errore:

            print(
                f"Errore avvio modulo voce: {errore}"
            )

            self.attivo = False

            return False

    def ascolta_comando(self):

        if not self.ascolto_attivo:
            return None

        audio = self.ascoltatore.ascolta()

        if not audio:
            return None

        return self.riconoscitore.riconosci(
            audio
        )

    def elabora_voce(self, testo):

        return self.assistente.elabora(
            testo
        )

    def rispondi(self, testo):

        if not self.sintesi_attiva:
            return False

        if not testo:
            return False

        return self.sintesi.parla(
            testo
        )

    def ferma(self):

        try:

            self.motore.ferma()
            self.assistente.ferma()
            self.ascoltatore.ferma()
            self.riconoscitore.ferma()

        except Exception as errore:

            print(
                f"Errore arresto modulo voce: {errore}"
            )

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
