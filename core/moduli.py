import importlib
import os


class ModuloManager:


    def __init__(self, logger=None):

        self.logger = logger

        self.moduli = {}



    def registra(
        self,
        nome,
        percorso
    ):

        self.moduli[nome] = {

            "percorso": percorso,

            "stato": "registrato",

            "oggetto": None

        }


        if self.logger:

            self.logger.info(
                f"Modulo registrato: {nome}"
            )



    def carica(
        self,
        nome
    ):

        if nome not in self.moduli:

            return False


        try:

            percorso = self.moduli[nome]["percorso"]


            modulo = importlib.import_module(
                percorso
            )


            self.moduli[nome]["oggetto"] = modulo

            self.moduli[nome]["stato"] = "caricato"


            if self.logger:

                self.logger.info(
                    f"Modulo caricato: {nome}"
                )


            return True


        except Exception as errore:


            self.moduli[nome]["stato"] = "errore"


            if self.logger:

                self.logger.errore(
                    f"Errore caricamento {nome}: {errore}"
                )


            return False



    def avvia(
        self,
        nome
    ):


        if nome not in self.moduli:

            return False


        modulo = self.moduli[nome]["oggetto"]


        try:

            if hasattr(
                modulo,
                "avvia"
            ):

                modulo.avvia()


            self.moduli[nome]["stato"] = "attivo"


            return True


        except Exception as errore:


            self.moduli[nome]["stato"] = "errore"


            if self.logger:

                self.logger.errore(
                    str(errore)
                )


            return False



    def elenco(self):

        return self.moduli



if __name__ == "__main__":


    manager = ModuloManager()


    manager.registra(
        "test",
        "math"
    )


    print(
        manager.carica(
            "test"
        )
    )


    print(
        manager.elenco()
    )