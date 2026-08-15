import time





class AssistenteVoce:


    def __init__(
        self,
        kernel
    ):


        self.kernel = kernel


        self.nome = "Assistente Vocale"


        self.attivo = False


        self.parola_attivazione = "jarvis"


        self.ultimo_comando = None


        self.ultima_risposta = None





        if self.kernel and self.kernel.config:


            voce = self.kernel.config.sezione(
                "voce"
            )


            self.parola_attivazione = voce.get(

                "wake_word",

                "jarvis"

            )







    def avvia(self):


        self.attivo = True



        self.log(

            "Assistente vocale avviato."

        )



        return True







    def elabora(
        self,
        comando
    ):


        if not self.attivo:


            return None




        if not comando:


            return None





        comando = comando.lower().strip()



        self.ultimo_comando = comando






        try:


            risposta = self.kernel.esegui_comando(

                comando

            )



            self.ultima_risposta = risposta



            return risposta





        except Exception as errore:



            self.log(

                f"Errore assistente: {errore}"

            )



            return "Errore durante l'esecuzione."









    def saluta(self):


        if self.kernel:


            self.kernel.parla(

                "Sono qui."

            )



        return "attivato"








    def cambia_wake_word(
        self,
        parola
    ):


        self.parola_attivazione = parola.lower()








    def log(
        self,
        messaggio
    ):


        try:


            if self.kernel and self.kernel.logger:


                self.kernel.logger.info(

                    messaggio

                )


            else:


                print(

                    messaggio

                )



        except Exception:


            print(

                messaggio

            )









    def ciclo(self):


        while self.attivo:


            time.sleep(

                0.1

            )









    def ferma(self):


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



            "wake_word":

                self.parola_attivazione,



            "ultimo_comando":

                self.ultimo_comando,



            "ultima_risposta":

                self.ultima_risposta

        }
