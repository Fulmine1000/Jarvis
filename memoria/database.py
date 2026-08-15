import json
import os
from datetime import datetime



FILE_DATABASE = "memoria/database.json"




class DatabaseMemoria:



    def __init__(self):

        self.crea_cartella()

        self.dati = {}

        self.carica()





    def crea_cartella(self):

        if not os.path.exists("memoria"):

            os.makedirs("memoria")





    def carica(self):


        if os.path.exists(FILE_DATABASE):


            try:


                with open(
                    FILE_DATABASE,
                    "r",
                    encoding="utf-8"
                ) as file:


                    self.dati = json.load(file)



            except:


                self.dati = {}



        else:


            self.salva()





    def salva(self):


        with open(
            FILE_DATABASE,
            "w",
            encoding="utf-8"
        ) as file:


            json.dump(

                self.dati,

                file,

                indent=4,

                ensure_ascii=False

            )





    def aggiungi(
        self,
        categoria,
        chiave,
        valore
    ):


        if categoria not in self.dati:


            self.dati[categoria] = {}



        self.dati[categoria][chiave] = {


            "valore":

                valore,


            "data":

                datetime.now().strftime(

                    "%d/%m/%Y %H:%M:%S"

                )

        }



        self.salva()





    def leggi(
        self,
        categoria,
        chiave
    ):


        try:


            return self.dati[categoria][chiave]



        except:


            return None





    def elimina(
        self,
        categoria,
        chiave
    ):


        if categoria in self.dati:


            if chiave in self.dati[categoria]:


                del self.dati[categoria][chiave]


                self.salva()


                return True



        return False





    def lista(
        self,
        categoria
    ):


        if categoria in self.dati:


            return self.dati[categoria]



        return {}





    def tutto(self):


        return self.dati





    def numero_ricordi(self):


        totale = 0



        for categoria in self.dati:


            totale += len(
                self.dati[categoria]
            )



        return totale





if __name__ == "__main__":


    memoria = DatabaseMemoria()



    memoria.aggiungi(

        "test",

        "stato",

        "Jarvis operativo"

    )



    print(

        memoria.leggi(

            "test",

            "stato"

        )

    )



    print(

        "Ricordi:",

        memoria.numero_ricordi()

    )
