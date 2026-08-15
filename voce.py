import os
import platform
import time
import queue
import threading


class VoceJarvis:


    def __init__(self):

        self.sistema = platform.system()

        self.voce = "Alice"

        self.velocita = 170

        self.volume = 1.0

        self.silenzioso = False

        self.parlando = False

        self.coda = queue.Queue()

        self.avvia()



    def avvia(self):

        thread = threading.Thread(
            target=self.gestore_voce,
            daemon=True
        )

        thread.start()



    def gestore_voce(self):

        while True:

            testo = self.coda.get()

            self.esegui(
                testo
            )

            self.coda.task_done()



    def parla(self, testo):

        if self.silenzioso:

            return

        self.coda.put(
            testo
        )



    def esegui(self, testo):

        self.parlando = True


        print(
            "JARVIS:",
            testo
        )


        if self.sistema == "Darwin":


            comando = (
                f'say '
                f'-v {self.voce} '
                f'-r {self.velocita} '
                f'"{testo}"'
            )


            os.system(
                comando
            )


        elif self.sistema == "Linux":

            os.system(
                f'espeak "{testo}"'
            )


        elif self.sistema == "Windows":

            print(
                "Sintesi vocale Windows da configurare."
            )


        time.sleep(0.5)


        self.parlando = False



    def elenco_voci(self):

        if self.sistema == "Darwin":

            os.system(
                "say -v '?'"
            )

            return "Lista voci mostrata."


        return "Funzione disponibile solo su Mac."



    def cambia_voce(self, nome):

        self.voce = nome

        return (
            f"Voce impostata: {nome}"
        )



    def cambia_velocita(self, valore):

        self.velocita = valore

        return (
            f"Velocità impostata: {valore}"
        )



    def stato(self):

        return {

            "voce": self.voce,

            "velocita": self.velocita,

            "parlando": self.parlando,

            "silenzioso": self.silenzioso

        }




if __name__ == "__main__":


    jarvis = VoceJarvis()


    print(
        jarvis.stato()
    )


    jarvis.parla(
        "Salve Simone. Jarvis è operativo."
    )


    # lascia il tempo alla voce di terminare
    time.sleep(5)
