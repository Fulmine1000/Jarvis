import time





class WakeWordJarvis:


    def __init__(self):


        self.nome = "Wake Word Jarvis"


        self.parole_attivazione = [

            "jarvis",

            "hey jarvis",

            "ehi jarvis"

        ]


        self.attivo = False


        self.ultimo_rilevamento = None


        self.tempo_attivo = 10


        self.ultimo_comando = ""







    def pulisci_testo(
        self,
        testo
    ):


        if not testo:


            return ""



        testo = testo.lower().strip()



        sostituzioni = {


            "jervis":
                "jarvis",


            "gervis":
                "jarvis",


            "jarvis.":
                "jarvis"


        }



        for vecchio, nuovo in sostituzioni.items():


            testo = testo.replace(

                vecchio,

                nuovo

            )



        return testo







    def controlla(
        self,
        frase
    ):


        frase = self.pulisci_testo(
            frase
        )



        if self.verifica_timeout():


            return {


                "attivato":

                    True,


                "comando":

                    frase

            }





        for parola in self.parole_attivazione:


            if parola in frase:


                self.attiva()



                comando = frase.replace(

                    parola,

                    "",

                    1

                ).strip()



                self.ultimo_comando = comando



                return {


                    "attivato":

                        True,


                    "comando":

                        comando

                }






        return {


            "attivato":

                False,


            "comando":

                ""

        }







    def attiva(self):


        self.attivo = True


        self.ultimo_rilevamento = time.time()







    def verifica_timeout(self):


        if not self.attivo:


            return False





        if (

            time.time()

            -

            self.ultimo_rilevamento

        ) > self.tempo_attivo:



            self.disattiva()



            return False





        return True







    def disattiva(self):


        self.attivo = False







    def cambia_timeout(
        self,
        secondi
    ):


        self.tempo_attivo = secondi







    def aggiungi_parola(
        self,
        parola
    ):


        parola = parola.lower().strip()



        if parola not in self.parole_attivazione:


            self.parole_attivazione.append(

                parola

            )


            return f"Parola aggiunta: {parola}"





        return "Parola già presente."







    def rimuovi_parola(
        self,
        parola
    ):


        parola = parola.lower().strip()



        if parola in self.parole_attivazione:


            self.parole_attivazione.remove(

                parola

            )


            return f"Parola rimossa: {parola}"





        return "Parola non trovata."







    def stato(self):


        return {


            "nome":

                self.nome,


            "attivo":

                self.attivo,


            "timeout":

                self.tempo_attivo,


            "parole":

                self.parole_attivazione,


            "ultimo_comando":

                self.ultimo_comando

        }
