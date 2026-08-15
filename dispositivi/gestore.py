import datetime





class GestoreDispositivi:


    def __init__(
        self,
        logger=None
    ):


        self.nome = "Gestore Dispositivi"


        self.logger = logger


        self.dispositivi = {}


        self.connessione = None


        self.base = None







    def collega_connessione(
        self,
        connessione
    ):


        self.connessione = connessione


        return "Connessione dispositivi collegata."









    def registra(
        self,
        nome,
        dispositivo
    ):


        self.dispositivi[nome] = dispositivo





        if getattr(

            dispositivo,

            "base",

            False

        ):


            self.base = nome






        if self.connessione:


            self.connessione.registra(

                nome,

                dispositivo

            )





        if self.logger:


            self.logger.info(

                f"Dispositivo registrato: {nome}"

            )



        return f"{nome} registrato."









    def rimuovi(
        self,
        nome
    ):


        if nome in self.dispositivi:


            del self.dispositivi[nome]



            if self.base == nome:


                self.base = None



            return f"{nome} rimosso."



        return "Dispositivo non trovato."









    def cerca(
        self,
        nome
    ):


        return self.dispositivi.get(

            nome

        )









    def cerca_base(
        self
    ):


        if self.base:


            return self.dispositivi.get(

                self.base

            )



        return None







    def elenco(self):


        return list(

            self.dispositivi.keys()

        )









    def stato_tutti(self):


        risultato = {}




        for nome, dispositivo in self.dispositivi.items():



            try:



                if hasattr(

                    dispositivo,

                    "stato"

                ):


                    risultato[nome] = dispositivo.stato()



                else:


                    risultato[nome] = {

                        "stato":

                            "disponibile"

                    }




            except Exception as errore:



                risultato[nome] = {

                    "errore":

                        str(errore)

                }



        return risultato







    def connetti(
        self,
        nome
    ):


        if self.connessione:


            return self.connessione.connetti(

                nome

            )



        dispositivo = self.cerca(

            nome

        )



        if dispositivo and hasattr(

            dispositivo,

            "connetti"

        ):


            return dispositivo.connetti()



        return "Dispositivo non disponibile."









    def disconnetti(
        self,
        nome
    ):


        if self.connessione:


            return self.connessione.disconnetti(

                nome

            )



        dispositivo = self.cerca(

            nome

        )



        if dispositivo and hasattr(

            dispositivo,

            "disconnetti"

        ):


            return dispositivo.disconnetti()



        return "Dispositivo non disponibile."









    def sincronizza(
        self,
        nome
    ):


        if self.connessione:


            return self.connessione.sincronizza(

                nome

            )



        dispositivo = self.cerca(

            nome

        )



        if dispositivo and hasattr(

            dispositivo,

            "sincronizza"

        ):


            return dispositivo.sincronizza()



        return "Sincronizzazione non disponibile."









    def sincronizza_base(
        self
    ):


        if not self.base:


            return "Base non trovata."



        return self.sincronizza(

            self.base

        )









    def rapporto(self):


        return {


            "nome":

                self.nome,


            "ora":

                datetime.datetime.now()

                .strftime("%H:%M:%S"),



            "base":

                self.base,



            "dispositivi":

                self.elenco()

        }









    def stato(self):


        return {


            "nome":

                self.nome,



            "stato":

                "attivo",



            "base":

                self.base,



            "numero_dispositivi":

                len(self.dispositivi),



            "dispositivi":

                self.elenco()

        }
