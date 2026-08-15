import uuid
import json
import os





FILE_IDENTITA = "identita_jarvis.json"





class IdentitaDispositivo:


    def __init__(
        self,
        nome,
        tipo="dispositivo"
    ):


        self.nome = nome

        self.tipo = tipo

        self.id = None

        self.carica()







    def crea_id(self):


        self.id = str(
            uuid.uuid4()
        )


        self.salva()


        return self.id







    def carica(self):


        if os.path.exists(
            FILE_IDENTITA
        ):


            try:


                with open(
                    FILE_IDENTITA,
                    "r",
                    encoding="utf-8"
                ) as file:


                    dati = json.load(
                        file
                    )


                    self.id = dati.get(
                        "id"
                    )



            except:


                self.crea_id()



        else:


            self.crea_id()







    def salva(self):


        dati = {


            "id":

                self.id,


            "nome":

                self.nome,


            "tipo":

                self.tipo


        }



        with open(
            FILE_IDENTITA,
            "w",
            encoding="utf-8"
        ) as file:


            json.dump(

                dati,

                file,

                indent=4,

                ensure_ascii=False

            )







    def informazioni(self):


        return {


            "id":

                self.id,


            "nome":

                self.nome,


            "tipo":

                self.tipo


        }