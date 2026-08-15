import random
from datetime import datetime





class PersonalitaJarvis:


    def __init__(self):


        self.nome = "Jarvis"


        self.stato = "attivo"








    def saluto(
        self
    ):


        ora = datetime.now().hour



        if ora < 12:


            return random.choice(

                [

                    "Buongiorno. Tutti i sistemi sono operativi.",

                    "Buongiorno. Sono pronto ad assisterti."

                ]

            )





        elif ora < 18:


            return random.choice(

                [

                    "Buon pomeriggio. Sono operativo.",

                    "Sono qui. Dimmi pure."

                ]

            )





        else:


            return random.choice(

                [

                    "Buonasera. Sistema pronto.",

                    "Sono attivo. Come posso aiutarti?"

                ]

            )








    def come_stai(
        self
    ):


        return random.choice(

            [

                "Tutti i sistemi funzionano correttamente.",

                "Sono operativo e pronto ad assisterti.",

                "I miei moduli sono attivi e funzionanti."

            ]

        )








    def aiuto(
        self
    ):


        return (

            "Posso aiutarti con il controllo dei dispositivi, "

            "la memoria, lo stato del sistema, "

            "l'orario, la data e i comandi disponibili."

        )








    def stato_personalita(
        self
    ):


        return {


            "nome":

                self.nome,


            "stato":

                self.stato

        }
