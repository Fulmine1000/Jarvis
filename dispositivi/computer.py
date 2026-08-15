import platform
import datetime



class ComputerJarvis:


    def __init__(self):

        self.nome = "Computer"

        self.attivo = True



    def avvia(self):

        self.attivo = True

        return "Computer avviato."



    def ferma(self):

        self.attivo = False

        return "Computer fermato."



    def stato(self):

        return {

            "nome":
                self.nome,

            "stato":
                "attivo"
                if self.attivo
                else "spento",

            "sistema":
                platform.system(),

            "computer":
                platform.node()

        }



    def informazioni(self):

        return {

            "sistema":
                platform.platform(),

            "ora":
                datetime.datetime.now().strftime(
                    "%H:%M:%S"
                )

        }
