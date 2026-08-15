import subprocess
import os





class SintesiVocale:


    def __init__(
        self,
        config=None
    ):


        self.nome = "Sintesi Vocale"


        self.attivo = True


        self.config = config



        # MOTORE VOCE

        self.motore = "piper"



        # MODELLO VOCALE

        self.modello = (

            "voce/modelli/it_IT-jarvis.onnx"

        )



        # IMPOSTAZIONI

        self.voce = "Jarvis"


        self.velocita = 1.0


        self.volume = 100


        self.stile = "Jarvis"





        if self.config:


            voce_config = (

                self.config

                .sezione("voce")

            )



            self.modello = voce_config.get(

                "modello",

                self.modello

            )



            self.velocita = voce_config.get(

                "velocita",

                1.0

            )



            self.volume = voce_config.get(

                "volume",

                100

            )



            self.stile = voce_config.get(

                "stile",

                "Jarvis"

            )







    def parla(
        self,
        testo
    ):


        if not self.attivo:


            return False



        if not testo:


            return False




        try:


            # CONTROLLO MODELLO


            if os.path.exists(
                self.modello
            ):



                file_audio = (

                    "jarvis_voce.wav"

                )



                comando = [

                    "piper",

                    "--model",

                    self.modello,

                    "--output_file",

                    file_audio

                ]



                processo = subprocess.Popen(

                    comando,

                    stdin=subprocess.PIPE,

                    text=True

                )



                processo.communicate(

                    testo

                )



                subprocess.run(

                    [

                        "afplay",

                        file_audio

                    ]

                )



                os.remove(

                    file_audio

                )



            else:


                # FALLBACK MACOS

                subprocess.run(

                    [

                        "say",

                        testo

                    ]

                )



            return True





        except Exception as errore:



            print(

                f"Errore sintesi vocale: {errore}"

            )


            return False







    def cambia_modello(
        self,
        modello
    ):


        self.modello = modello







    def cambia_velocita(
        self,
        velocita
    ):


        self.velocita = velocita







    def cambia_stile(
        self,
        stile
    ):


        self.stile = stile







    def ferma(self):


        self.attivo = False







    def avvia(self):


        self.attivo = True


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



            "motore":

                self.motore,



            "modello":

                self.modello,



            "velocita":

                self.velocita,



            "stile":

                self.stile

        }
