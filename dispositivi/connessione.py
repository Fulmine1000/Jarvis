import datetime





class ConnessioneDispositivi:


    def __init__(
        self,
        logger=None
    ):


        self.nome = "Connessione Dispositivi"


        self.logger = logger


        self.attivo = False


        self.dispositivi = {}



        self.base = None







    def avvia(self):


        self.attivo = True



        if self.logger:


            self.logger.info(

                "Connessione dispositivi avviata."

            )



        return "Connessione dispositivi attiva."









    def registra(
        self,
        nome,
        dispositivo
    ):


        self.dispositivi[nome] = {


            "oggetto":

                dispositivo,



            "connesso":

                False,



            "ultima_connessione":

                None

        }



        if getattr(

            dispositivo,

            "base",

            False

        ):


            self.base = nome



        return f"{nome} registrato."









    def connetti(
        self,
        nome
    ):


        dispositivo = self.dispositivi.get(

            nome

        )



        if not dispositivo:


            return "Dispositivo non trovato."





        oggetto = dispositivo["oggetto"]





        if hasattr(

            oggetto,

            "connetti"

        ):


            risultato = oggetto.connetti()



        else:


            risultato = f"{nome} collegato."






        dispositivo["connesso"] = True



        dispositivo["ultima_connessione"] = (

            datetime.datetime.now()

            .strftime(

                "%d/%m/%Y %H:%M:%S"

            )

        )



        return risultato









    def disconnetti(
        self,
        nome
    ):


        dispositivo = self.dispositivi.get(

            nome

        )



        if not dispositivo:


            return "Dispositivo non trovato."





        oggetto = dispositivo["oggetto"]





        if hasattr(

            oggetto,

            "disconnetti"

        ):


            risultato = oggetto.disconnetti()



        else:


            risultato = f"{nome} scollegato."






        dispositivo["connesso"] = False



        return risultato









    def sincronizza(
        self,
        nome
    ):


        dispositivo = self.dispositivi.get(

            nome

        )



        if not dispositivo:


            return "Dispositivo non trovato."





        oggetto = dispositivo["oggetto"]





        if hasattr(

            oggetto,

            "sincronizza"

        ):


            return oggetto.sincronizza()



        return "Sincronizzazione completata."









    def connetti_base(self):


        if not self.base:


            return "Base non trovata."



        return self.connetti(

            self.base

        )









    def stato(
        self
    ):


        risultato = {}





        for nome, dati in self.dispositivi.items():



            oggetto = dati["oggetto"]



            risultato[nome] = {


                "connesso":

                    dati["connesso"],



                "ultima_connessione":

                    dati["ultima_connessione"],



                "base":

                    getattr(

                        oggetto,

                        "base",

                        False

                    )

            }






        return {


            "nome":

                self.nome,



            "attivo":

                self.attivo,



            "base":

                self.base,



            "dispositivi":

                risultato

        }
