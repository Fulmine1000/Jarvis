import json
import os
import datetime


FILE_RICORDI = "memoria/ricordi.json"


class GestoreRicordi:


    def __init__(self):

        self.ricordi = {}

        self.carica()



    def crea_file(self):

        if not os.path.exists("memoria"):

            os.makedirs("memoria")


        if not os.path.exists(FILE_RICORDI):

            with open(
                FILE_RICORDI,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    {},
                    file,
                    indent=4
                )



    def carica(self):

        self.crea_file()


        try:

            with open(
                FILE_RICORDI,
                "r",
                encoding="utf-8"
            ) as file:

                self.ricordi = json.load(file)


        except:

            self.ricordi = {}



    def salva(self):

        with open(
            FILE_RICORDI,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.ricordi,
                file,
                indent=4,
                ensure_ascii=False
            )



    def aggiungi(
        self,
        titolo,
        contenuto,
        categoria="generale",
        importanza="normale"
    ):


        data = datetime.datetime.now().strftime(
            "%d/%m/%Y %H:%M"
        )


        self.ricordi[titolo] = {

            "contenuto": contenuto,

            "categoria": categoria,

            "importanza": importanza,

            "data": data

        }


        self.salva()


        return (
            f"Ricordo salvato: {titolo}"
        )



    def cerca(self, parola):

        risultati = []


        for titolo, dati in self.ricordi.items():

            testo = (
                titolo +
                " " +
                dati["contenuto"]
            ).lower()


            if parola.lower() in testo:

                risultati.append(
                    titolo
                )



        if risultati:

            return (
                "Ho trovato: "
                +
                ", ".join(risultati)
            )


        return (
            "Nessun ricordo trovato."
        )



    def tutti(self):

        if not self.ricordi:

            return (
                "Non ho ricordi salvati."
            )


        risposta = "Ricordi:\n"


        for titolo, dati in self.ricordi.items():

            risposta += (
                f"- {titolo}: "
                f"{dati['contenuto']} "
                f"[{dati['categoria']}]\n"
            )


        return risposta



    def elimina(self, titolo):

        if titolo in self.ricordi:

            del self.ricordi[titolo]

            self.salva()

            return (
                "Ricordo eliminato."
            )


        return (
            "Ricordo non trovato."
        )



    def ricordi_importanti(self):

        importanti = []


        for titolo, dati in self.ricordi.items():

            if dati["importanza"] == "alta":

                importanti.append(
                    titolo
                )


        if importanti:

            return (
                "Ricordi importanti: "
                +
                ", ".join(importanti)
            )


        return (
            "Nessun ricordo importante."
        )




if __name__ == "__main__":


    memoria = GestoreRicordi()


    print(
        memoria.aggiungi(
            "colore",
            "Il colore preferito di Simone è blu",
            "preferenze",
            "alta"
        )
    )


    print(
        memoria.tutti()
    )