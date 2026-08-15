from comandi.gestore import GestoreComandi





class ModuloComandi:


    def __init__(
        self,
        kernel
    ):


        self.kernel = kernel


        self.nome = "Comandi"


        self.attivo = False


        self.gestore = None







    def avvia(self):


        self.gestore = GestoreComandi(


            memoria=self.kernel.memoria,


            personalita=getattr(

                self.kernel,

                "personalita",

                None

            ),


            dispositivi=(

                self.kernel.modulo_dispositivi.gestore

                if self.kernel.modulo_dispositivi

                else None

            ),


            kernel=self.kernel,


            logger=self.kernel.logger


        )



        self.attivo = True



        self.gestore.avvia()



        self.kernel.logger.info(

            "Modulo comandi attivo."

        )



        return True







    def esegui(
        self,
        comando
    ):


        if not self.gestore:


            return "Gestore comandi non avviato."



        return self.gestore.esegui(

            comando

        )









    def stato(self):


        return {


            "nome":

                self.nome,



            "stato":

                "attivo"

                if self.attivo

                else "spento",



            "gestore":

                self.gestore.stato()

                if self.gestore

                else {}

        }
