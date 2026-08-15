import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from wake_word import WakeWordJarvis


class AscoltoJarvis:


    def __init__(self):

        self.model = Model(
            "vosk-model-small-it-0.22"
        )

        self.rec = KaldiRecognizer(
            self.model,
            16000
        )

        self.wake = WakeWordJarvis()

        self.in_attesa = True



    def ascolta_microfono(self):

        print("🎤 Jarvis in ascolto...")


        try:

            with sd.RawInputStream(
                samplerate=16000,
                blocksize=8000,
                dtype="int16",
                channels=1
            ) as stream:


                while True:


                    dati, overflow = stream.read(4000)


                    if self.rec.AcceptWaveform(
                        bytes(dati)
                    ):


                        risultato = json.loads(
                            self.rec.Result()
                        )


                        testo = risultato.get(
                            "text",
                            ""
                        )


                        if testo:

                            print(
                                "Riconosciuto:",
                                testo
                            )


                            controllo = self.wake.controlla(
                                testo
                            )


                            if controllo["attivato"]:


                                comando = controllo["comando"]


                                if comando:

                                    return comando


                                else:

                                    print(
                                        "In ascolto del comando..."
                                    )



        except Exception as errore:

            return (
                f"Errore microfono: {errore}"
            )




if __name__ == "__main__":


    ascolto = AscoltoJarvis()


    while True:


        comando = ascolto.ascolta_microfono()


        print(
            "Comando ricevuto:",
            comando
        )
