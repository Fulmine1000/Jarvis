class EventBus:


    def __init__(self):

        self.eventi = {}





    def registra(

        self,

        evento,

        funzione

    ):


        if evento not in self.eventi:


            self.eventi[evento] = []



        self.eventi[evento].append(

            funzione

        )







    def emetti(

        self,

        evento,

        dati=None

    ):


        if evento not in self.eventi:

            return



        for funzione in self.eventi[evento]:


            try:


                funzione(dati)



            except Exception as errore:


                print(

                    f"Errore evento {evento}: {errore}"

                )







    def rimuovi(

        self,

        evento,

        funzione

    ):


        if evento in self.eventi:


            if funzione in self.eventi[evento]:


                self.eventi[evento].remove(

                    funzione

                )
