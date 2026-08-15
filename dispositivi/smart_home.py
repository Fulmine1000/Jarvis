import json
import os


FILE_DISPOSITIVI = "smart_devices.json"


class SmartHomeJarvis:


    def __init__(self):

        self.nome = "Smart Home"

        self.dispositivi = []

        self.carica()



    def carica(self):

        if os.path.exists(FILE_DISPOSITIVI):

            try:

                with open(
                    FILE_DISPOSITIVI,
                    "r",
                    encoding="utf-8"
                ) as file:

                    self.dispositivi = json.load(file)


            except:

                self.dispositivi = []



    def salva(self):

        with open(
            FILE_DISPOSITIVI,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.dispositivi,
                file,
                indent=4,
                ensure_ascii=False
            )



    def aggiungi_dispositivo(
        self,
        nome,
        tipo
    ):

        dispositivo = {

            "nome": nome,

            "tipo": tipo,

            "stato": "spento"

        }


        self.dispositivi.append(
            dispositivo
        )

        self.salva()


        return (
            f"{nome} aggiunto."
        )



    def accendi(
        self,
        nome
    ):

        for dispositivo in self.dispositivi:

            if dispositivo["nome"].lower() == nome.lower():

                dispositivo["stato"] = "acceso"

                self.salva()

                return (
                    f"{nome} acceso."
                )


        return (
            "Dispositivo non trovato."
        )



    def spegni(
        self,
        nome
    ):

        for dispositivo in self.dispositivi:

            if dispositivo["nome"].lower() == nome.lower():

                dispositivo["stato"] = "spento"

                self.salva()

                return (
                    f"{nome} spento."
                )


        return (
            "Dispositivo non trovato."
        )



    def lista(self):

        return self.dispositivi



    def stato(self):

        return {

            "sistema": self.nome,

            "dispositivi": self.dispositivi

        }




if __name__ == "__main__":


    casa = SmartHomeJarvis()


    print(
        casa.aggiungi_dispositivo(
            "Luce soggiorno",
            "lampada"
        )
    )


    print(
        casa.accendi(
            "Luce soggiorno"
        )
    )


    print(
        casa.stato()
    )
