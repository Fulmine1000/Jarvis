from datetime import datetime

from .database import DatabaseMemoria
from .profilo import ProfiloJarvis



class MemoriaJarvis:


    def __init__(
        self,
        logger=None
    ):

        self.nome = "Memoria Jarvis"

        self.attiva = False

        self.logger = logger


        self.database = DatabaseMemoria()

        self.profilo = ProfiloJarvis(
            logger
        )





    def avvia(self):


        self.attiva = True


        self.profilo.avvia()



        if self.logger:

            self.logger.info(
                "Memoria Jarvis avviata."
            )





    def ricorda(
        self,
        chiave,
        valore
    ):


        memoria = {


            "valore":

                valore,


            "data":

                datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S"
                )

        }



        self.database.aggiungi(
            "ricordi",
            chiave,
            memoria
        )



        return (
            f"Ricorderò: {chiave}"
        )





    def cerca(
        self,
        chiave
    ):


        dato = self.database.leggi(
            "ricordi",
            chiave
        )



        if dato:


            if isinstance(
                dato["valore"],
                dict
            ):

                return dato["valore"]["valore"]


            return dato["valore"]



        return None





    def elenco_ricordi(
        self
    ):


        return self.database.lista(
            "ricordi"
        )





    def dimentica(
        self,
        chiave
    ):


        if self.database.elimina(
            "ricordi",
            chiave
        ):


            return "Ricordo eliminato."



        return "Ricordo non trovato."





    def stato(self):


        return {


            "nome":

                self.nome,


            "stato":

                "attiva"
                if self.attiva
                else "spenta",


            "profilo":

                self.profilo.stato()

        }
