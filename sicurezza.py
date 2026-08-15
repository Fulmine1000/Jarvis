import datetime
import json
import os


FILE_LOG = "sicurezza_log.json"


class SicurezzaJarvis:


    def __init__(self):

        self.nome = "Sicurezza Jarvis"

        self.protezione = True

        self.utenti_autorizzati = [

            "Simone"

        ]

        self.log = []

        self.carica_log()



    def carica_log(self):

        if os.path.exists(FILE_LOG):

            try:

                with open(
                    FILE_LOG,
                    "r",
                    encoding="utf-8"
                ) as file:

                    self.log = json.load(file)


            except:

                self.log = []



    def salva_log(self):

        with open(
            FILE_LOG,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.log,
                file,
                indent=4,
                ensure_ascii=False
            )



    def registra(
        self,
        azione,
        risultato
    ):

        evento = {

            "ora":
                datetime.datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S"
                ),

            "azione":
                azione,

            "risultato":
                risultato

        }


        self.log.append(
            evento
        )


        self.salva_log()



    def autorizza(
        self,
        utente
    ):

        if utente in self.utenti_autorizzati:

            return True


        return False



    def richiede_conferma(
        self,
        comando
    ):

        comandi_protetti = [

            "elimina",

            "formatta",

            "spegni computer",

            "modifica sistema"

        ]


        for parola in comandi_protetti:

            if parola in comando.lower():

                return True


        return False



    def stato(self):

        return {

            "protezione":
                self.protezione,

            "utenti":
                self.utenti_autorizzati,

            "eventi_registrati":
                len(self.log)

        }



if __name__ == "__main__":


    sicurezza = SicurezzaJarvis()


    sicurezza.registra(
        "Avvio Jarvis",
        "Consentito"
    )


    print(
        sicurezza.stato()
    )