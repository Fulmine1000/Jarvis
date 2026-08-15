import socket



class Rete:


    def __init__(self):

        self.nome = "Rete"

        self.attiva = True



    def avvia(self):

        self.attiva = True



    def ferma(self):

        self.attiva = False



    def stato(self):

        try:

            host = socket.gethostname()

            ip = socket.gethostbyname(
                host
            )


        except:

            ip = "non disponibile"



        return {

            "nome":
                self.nome,

            "stato":
                "online"
                if self.attiva
                else "offline",

            "ip":
                ip

        }
