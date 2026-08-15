import time





class WakeWordJarvis:


    def __init__(self):


        self.nome = "Wake Word Jarvis"

        # Parole di attivazione complete: la virgola viene normalizzata
        # da pulisci_testo, quindi "Ehi, Jarvis" diventa "ehi jarvis".
        self.parole_attivazione = [

            "jarvis",

            "hey jarvis",

            "ehi jarvis"

        ]

        # Prefissi di attivazione: quando Vosk trascrive parzialmente
        # "Hey Jarvis" come solo "ehi" o "hey", questi vengono riconosciuti
        # come inizio di wake word e attivano l'ascolto SENZA passare
        # il testo al GestoreComandi (comando vuoto -> "Sono qui").
        self.prefissi_attivazione = [

            "ehi",

            "hey"

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



        # Normalizza virgole e spazi: "Ehi, Jarvis" -> "ehi jarvis".
        testo = testo.replace(",", " ")

        # Collassa spazi multipli in uno solo.
        testo = " ".join(testo.split())

        return testo







    def controlla(
        self,
        frase
    ):


        frase = self.pulisci_testo(
            frase
        )



        # Se la wake word era gia attiva (entro timeout), il testo
        # corrente viene trattato come comando. Ma se e un prefisso
        # ("ehi"/"hey") o una parola di attivazione completa ("jarvis",
        # "ehi jarvis"), non passarlo al GestoreComandi: rinnova
        # l'attivazione e attende il comando reale.
        if self.verifica_timeout():


            parole_attivazione_tutte = (
                self.prefissi_attivazione
                + self.parole_attivazione
            )

            if frase in parole_attivazione_tutte:

                self.attiva()

                return {

                    "attivato": True,

                    "comando": ""

                }

            return {

                "attivato": True,

                "comando": frase

            }






        # Prefisso di attivazione: Vosk ha trascrito solo "ehi" o "hey"
        # (parziale di "Hey Jarvis"). Attiva senza comando -> "Sono qui".
        if frase in self.prefissi_attivazione:

            self.attiva()

            self.ultimo_comando = ""

            return {

                "attivato": True,

                "comando": ""

            }




        # Parole di attivazione complete, dalla piu lunga alla piu corta,
        # per evitare che "jarvis" matchi prima di "ehi jarvis" lasciando
        # "ehi" come comando residuo.
        parole_ordinate = sorted(
            self.parole_attivazione,
            key=len,
            reverse=True
        )

        for parola in parole_ordinate:

            if parola in frase:

                self.attiva()

                comando = frase.replace(

                    parola,

                    "",

                    1

                ).strip()

                self.ultimo_comando = comando

                return {

                    "attivato": True,

                    "comando": comando

                }




        return {

            "attivato": False,

            "comando": ""

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
