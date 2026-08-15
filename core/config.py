import os
import json


PERCORSO_CONFIG = "config/config.json"



class ConfigJarvis:


    def __init__(self):

        self.default = {

            "jarvis": {

                "nome": "Jarvis",

                "versione": "3.0"

            },


            "utente": {

                "nome": "Simone"

            },


            "voce": {

                "wake_word": "jarvis",

                "lingua": "it-IT",

                "motore": "piper",

                "modello": "jarvis_it.onnx",

                "velocita": 1.0

            },


            "memoria": {

                "attiva": True,

                "salvataggio": True

            },


            "sistema": {

                "log": True,

                "modalita": "normale"

            },


            "dispositivi": {

                "telefono": True,

                "computer": True,

                "rete": True,

                "bluetooth": True

            }

        }


        self.config = {}


        self.carica()





    def carica(self):


        cartella = os.path.dirname(
            PERCORSO_CONFIG
        )


        if not os.path.exists(cartella):

            os.makedirs(cartella)



        if os.path.exists(PERCORSO_CONFIG):


            try:


                with open(

                    PERCORSO_CONFIG,

                    "r",

                    encoding="utf-8"

                ) as file:


                    self.config = json.load(file)



            except Exception:


                self.config = self.default


                self.salva()



        else:


            self.config = self.default


            self.salva()





    def salva(self):


        with open(

            PERCORSO_CONFIG,

            "w",

            encoding="utf-8"

        ) as file:


            json.dump(

                self.config,

                file,

                indent=4,

                ensure_ascii=False

            )





    def ottieni(

        self,

        chiave,

        default=None

    ):


        return self.config.get(

            chiave,

            default

        )





    def sezione(

        self,

        nome

    ):


        return self.config.get(

            nome,

            {}

        )





    def modifica(

        self,

        sezione,

        chiave,

        valore

    ):


        if sezione not in self.config:


            self.config[sezione] = {}



        self.config[sezione][chiave] = valore


        self.salva()





    def tutto(self):


        return self.config
