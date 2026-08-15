class ModuleManager:


    def __init__(

        self,

        logger

    ):


        self.logger = logger


        self.moduli = {}







    def registra(

        self,

        nome,

        modulo

    ):


        self.moduli[nome] = modulo


        self.logger.info(

            f"Modulo registrato: {nome}"

        )







    def avvia(

        self,

        nome

    ):


        modulo = self.moduli.get(

            nome

        )


        if not modulo:

            return False




        try:


            risultato = modulo.avvia()



            self.logger.info(

                f"Modulo avviato: {nome}"

            )


            return risultato





        except Exception as errore:


            self.logger.errore(

                f"Errore avvio {nome}: {errore}"

            )


            return False








    def ferma(

        self,

        nome

    ):


        modulo = self.moduli.get(

            nome

        )



        if modulo:


            try:


                modulo.ferma()



            except Exception:

                pass







    def stato(self):


        risultato = {}



        for nome, modulo in self.moduli.items():


            try:


                risultato[nome] = modulo.stato()



            except Exception:


                risultato[nome] = "errore"



        return risultato
