from voce.ascoltatore import AscoltatoreVoce
from voce.riconoscimento import RiconoscitoreVoce
from voce.sintesi import SintesiVocale
from voce.assistente_voce import AssistenteVoce
from voce.motore_ascolto import MotoreAscolto





class ModuloVoce:


    def __init__(
        self,
        kernel
    ):


        self.kernel = kernel


        self.nome = "Voce"


        self.attivo = False



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





            microfono = self.ascoltatore.avvia()


            modello = self.riconoscitore.avvia()





            if not microfono or not modello:


                self.ascoltatore.ferma()


                self.attivo = False


                return False






            self.attivo = True





            self.assistente.avvia()


            self.motore.avvia()





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


        if not self.attivo:


            return None





        audio = self.ascoltatore.ascolta()



        if not audio:


            return None





        return self.riconoscitore.riconosci(

            audio

        )








    def elabora_voce(
        self,
        testo
    ):


        return self.assistente.elabora(

            testo

        )








    def rispondi(
        self,
        testo
    ):


        if not self.attivo:


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



        return True







    def stato(self):


        return {


            "nome":

                self.nome,



            "stato":

                "attivo"

                if self.attivo

                else

                "spento",



            "sintesi":

                self.sintesi.stato(),



            "riconoscimento":

                self.riconoscitore.stato(),



            "assistente":

                self.assistente.stato(),



            "motore_ascolto":

                self.motore.stato()

        }
