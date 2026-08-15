import json
import os
import datetime


FILE_CONVERSAZIONI = "memoria/conversazioni.json"


class GestoreConversazioni:


    def __init__(self):

        self.conversazioni = []

        self.carica()



    def crea_file(self):

        if not os.path.exists("memoria"):

            os.makedirs("memoria")


        if not os.path.exists(FILE_CONVERSAZIONI):

            with open(
                FILE_CONVERSAZIONI,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    [],
                    file,
                    indent=4
                )



    def carica(self):

        self.crea_file()


        try:

            with open(
                FILE_CONVERSAZIONI,
                "r",
                encoding="utf-8"
            ) as file:

                self.conversazioni = json.load(file)


        except:

            self.conversazioni = []



    def salva(self):

        with open(
            FILE_CONVERSAZIONI,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.conversazioni,
                file,
                indent=4,
                ensure_ascii=False
            )



    def salva_messaggio(
        self,
        utente,
        jarvis
    ):


        data = datetime.datetime.now().strftime(
            "%d/%m/%Y %H:%M"
        )


        messaggio = {

            "data": data,

            "utente": utente,

            "jarvis": jarvis

        }


        self.conversazioni.append(
            messaggio
        )


        self.salva()


        return (
            "Conversazione salvata."
        )



    def ultimi_messaggi(
        self,
        numero=5
    ):


        ultimi = self.conversazioni[-numero:]


        if not ultimi:

            return (
                "Nessuna conversazione salvata."
            )


        risposta = "Ultime conversazioni:\n"


        for messaggio in ultimi:

            risposta += (
                f"\n[{messaggio['data']}]\n"
                f"Tu: {messaggio['utente']}\n"
                f"Jarvis: {messaggio['jarvis']}\n"
            )


        return risposta



    def cancella_storico(self):

        self.conversazioni = []

        self.salva()


        return (
            "Storico conversazioni cancellato."
        )




if __name__ == "__main__":


    chat = GestoreConversazioni()


    print(
        chat.salva_messaggio(
            "Ciao Jarvis",
            "Buongiorno Simone, come posso aiutarti?"
        )
    )


    print(
        chat.ultimi_messaggi()
    )