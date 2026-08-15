import subprocess


class Bluetooth:


    def __init__(self):

        self.nome = "Bluetooth"

        self.attivo = True



    def avvia(self):

        self.attivo = True



    def ferma(self):

        self.attivo = False



    def stato(self):

        return {

            "nome":
                self.nome,

            "stato":
                "attivo"
                if self.attivo
                else "spento"

        }
