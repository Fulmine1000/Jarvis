import sounddevice as sd
import queue





class AscoltatoreVoce:


    def __init__(
        self,
        frequenza=16000
    ):


        self.nome = "Ascoltatore Voce"


        self.frequenza = frequenza


        self.audio = queue.Queue(
            maxsize=20
        )


        self.attivo = False


        self.stream = None







    def callback(
        self,
        ingresso,
        frames,
        tempo,
        stato
    ):


        if stato:


            print(

                f"Errore audio: {stato}"

            )



        try:


            self.audio.put_nowait(

                bytes(ingresso)

            )



        except queue.Full:


            pass







    def avvia(self):


        try:



            self.pulisci_buffer()





            self.stream = sd.RawInputStream(


                samplerate=self.frequenza,


                blocksize=8000,


                dtype="int16",


                channels=1,


                callback=self.callback


            )



            self.stream.start()



            self.attivo = True



            return True






        except Exception as errore:



            print(

                f"Errore avvio microfono: {errore}"

            )



            self.attivo = False



            return False







    def ascolta(self):


        if not self.attivo:


            return None





        try:


            return self.audio.get(

                timeout=1

            )



        except queue.Empty:


            return None







    def pulisci_buffer(self):


        while not self.audio.empty():


            try:


                self.audio.get_nowait()



            except queue.Empty:


                break







    def ferma(self):


        self.attivo = False





        if self.stream:


            try:


                self.stream.stop()


                self.stream.close()



            except Exception:


                pass



            self.stream = None





        self.pulisci_buffer()







    def riavvia(self):


        self.ferma()



        return self.avvia()







    def stato(self):


        return {


            "nome":

                self.nome,


            "stato":

                "attivo"

                if self.attivo

                else

                "spento",



            "frequenza":

                self.frequenza,


            "stream":

                self.stream is not None

        }
