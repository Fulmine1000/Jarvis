import os
import subprocess
import tempfile
import threading


class VoceJarvis:


    def __init__(
        self,
        modello="voce/modelli/voce.onnx",
        nome="J.A.R.V.I.S."
    ):

        self.nome = nome

        self.modello = modello

        self.attivo = False

        self.coda = []

        self.lock = threading.Lock()



    def avvia(self):

        if not os.path.exists(self.modello):

            print(
                "Modello vocale non trovato:",
                self.modello
            )

            return False


        self.attivo = True


        print(
            "Voce Jarvis avviata."
        )


        return True




    def parla(
        self,
        testo
    ):


        if not self.attivo:

            return False


        if not testo:

            return False



        with self.lock:

            self.coda.append(
                testo
            )



        self.esegui_coda()



        return True





    def esegui_coda(self):


        while self.coda:


            with self.lock:

                testo = self.coda.pop(0)



            try:


                file_audio = tempfile.NamedTemporaryFile(
                    suffix=".wav",
                    delete=False
                )


                file_audio.close()



                comando = [

                    "piper",

                    "--model",
                    self.modello,

                    "--output_file",
                    file_audio.name

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
                        file_audio.name
                    ]
                )



                os.remove(
                    file_audio.name
                )



            except Exception as errore:


                print(
                    "Errore voce Jarvis:",
                    errore
                )







    def ferma(self):


        self.attivo = False


        print(
            "Voce Jarvis fermata."
        )






    def stato(self):


        return {


            "nome":

                self.nome,


            "stato":

                "attiva"

                if self.attivo

                else

                "spenta",


            "modello":

                self.modello

        }