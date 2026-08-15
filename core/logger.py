import os
from datetime import datetime


class LoggerJarvis:


    def __init__(self):

        self.cartella = "logs"

        if not os.path.exists(self.cartella):

            os.makedirs(self.cartella)



    def scrivi(
        self,
        livello,
        messaggio
    ):

        ora = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )


        testo = f"[{ora}] [{livello}] {messaggio}"


        print(testo)


        file = os.path.join(

            self.cartella,

            "jarvis.log"

        )


        with open(

            file,

            "a",

            encoding="utf-8"

        ) as log:


            log.write(

                testo + "\n"

            )





    def info(
        self,
        messaggio
    ):

        self.scrivi(

            "INFO",

            messaggio

        )





    def errore(
        self,
        messaggio
    ):

        self.scrivi(

            "ERRORE",

            messaggio

        )





    def warning(
        self,
        messaggio
    ):

        self.scrivi(

            "WARNING",

            messaggio

        )

    # Alias per coerenza con la convenzione standard Python (logging).
    # Mantenuti i nomi italiani per retrocompatibilità con il codice esistente.
    error = errore

    warn = warning
