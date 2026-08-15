import os
import json

from vosk import Model, KaldiRecognizer





class RiconoscitoreVoce:


    def __init__(
        self,
        config=None
    ):


        self.nome = "Riconoscitore Vocale"


        self.config = config


        self.attivo = False


        self.modello = None


        self.riconoscitore = None


        self.lingua = "it"



        base = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )



        self.percorso_modello = os.path.join(

            base,

            "vosk-model-small-it-0.22"

        )



        self.sample_rate = 16000





        if self.config:


            voce = self.config.sezione(
                "voce"
            )



            modello = voce.get(
                "modello_riconoscimento",
                None
            )



            if modello:


                self.percorso_modello = os.path.join(

                    base,

                    modello

                )



            self.sample_rate = voce.get(

                "sample_rate",

                16000

            )







    def avvia(self):


        try:


            if not os.path.exists(

                self.percorso_modello

            ):


                raise Exception(

                    "Modello Vosk non trovato: "

                    + self.percorso_modello

                )





            self.modello = Model(

                self.percorso_modello

            )





            self.riconoscitore = KaldiRecognizer(

                self.modello,

                self.sample_rate

            )





            self.attivo = True



            return True





        except Exception as errore:


            print(

                f"Errore riconoscimento vocale: {errore}"

            )


            self.attivo = False



            return False







    def riconosci(
        self,
        audio
    ):


        if not self.attivo:


            return None





        if not audio:


            return None





        try:


            if self.riconoscitore.AcceptWaveform(

                audio

            ):



                risultato = json.loads(

                    self.riconoscitore.Result()

                )



                testo = risultato.get(

                    "text",

                    ""

                )



                return testo.strip()





        except Exception as errore:


            print(

                f"Errore analisi voce: {errore}"

            )



        return None







    def reset(self):


        if self.modello:


            self.riconoscitore = KaldiRecognizer(

                self.modello,

                self.sample_rate

            )



    def ferma(self):


        self.attivo = False


        self.modello = None


        self.riconoscitore = None







    def stato(self):


        return {


            "nome":

                self.nome,


            "stato":

                "attivo"

                if self.attivo

                else

                "spento",



            "lingua":

                self.lingua,



            "modello":

                self.percorso_modello,


            "sample_rate":

                self.sample_rate

        }
