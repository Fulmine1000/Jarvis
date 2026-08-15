class ContestoJarvis:


    def __init__(self):

        self.ultimo_comando = None

        self.ultima_risposta = None

        self.argomento = None

        self.storico = []





    def aggiorna(
        self,
        comando,
        risposta
    ):

        self.ultimo_comando = comando

        self.ultima_risposta = risposta


        self.storico.append({

            "comando": comando,

            "risposta": risposta

        })


        if len(self.storico) > 50:

            self.storico.pop(0)





    def ultimo(
        self
    ):

        return {

            "comando":
                self.ultimo_comando,

            "risposta":
                self.ultima_risposta

        }





    def cronologia(
        self
    ):

        return self.storico





    def stato(
        self
    ):

        return {

            "nome":
                "Contesto Jarvis",

            "comandi_memorizzati":
                len(self.storico)

        }