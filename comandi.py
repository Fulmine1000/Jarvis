# DEPRECATO — mantenuto per riferimento storico.
# Usare il modulo ufficiale corrispondente (vedi analisi/README).
# Non usato dal kernel 3.0.
import datetime



class GestoreComandi:


    def __init__(
        self,
        memoria=None,
        personalita=None,
        dispositivi=None,
        kernel=None,
        logger=None
    ):

        self.memoria = memoria

        self.personalita = personalita

        self.dispositivi = dispositivi

        self.kernel = kernel

        self.logger = logger

        self.attivo = False

        self.comandi_personalizzati = {}





    def avvia(self):


        self.attivo = True


        if self.logger:

            self.logger.info(
                "Gestore comandi avviato."
            )





    def esegui(
        self,
        comando
    ):


        comando = comando.lower().strip()



        if not comando:

            return "Comando vuoto."





        if comando == "stato sistema" or comando == "stato":


            if self.kernel:


                return str(
                    self.kernel.stato_sistema()
                )


            return "Kernel non collegato."





        if "che ore sono" in comando:


            ora = datetime.datetime.now().strftime(
                "%H:%M"
            )


            return f"Sono le {ora}."





        if "che giorno è" in comando or "data" in comando:


            oggi = datetime.datetime.now().strftime(
                "%d/%m/%Y"
            )


            return f"Oggi è il {oggi}."





        if "stato dispositivi" in comando:


            if self.dispositivi:


                return str(
                    self.dispositivi.stato_tutti()
                )


            return "Gestore dispositivi non collegato."





        if "quali dispositivi" in comando:


            if self.dispositivi:


                return str(
                    self.dispositivi.elenco()
                )


            return "Nessun dispositivo registrato."





        if comando.startswith("ricorda "):


            testo = comando.replace(
                "ricorda ",
                ""
            )



            parti = testo.split(
                " è ",
                1
            )



            if len(parti) == 2 and self.memoria:


                return self.memoria.ricorda(
                    parti[0],
                    parti[1]
                )



            return "Non riesco a salvare il ricordo."





        if "cosa ricordi di me" in comando:


            if self.memoria:


                return self.memoria.profilo.mostra_profilo()



            return "Memoria non disponibile."





        for nome, funzione in self.comandi_personalizzati.items():


            if nome in comando:


                return funzione()





        return "Non ho trovato un comando compatibile."





    def aggiungi_comando(
        self,
        nome,
        funzione
    ):


        self.comandi_personalizzati[nome] = funzione


        return f"Comando {nome} aggiunto."





    def stato(self):


        return {


            "nome":

                "Gestore Comandi",


            "stato":

                "attivo"
                if self.attivo
                else "spento"

        }
