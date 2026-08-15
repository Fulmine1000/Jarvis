# DEPRECATO — mantenuto per riferimento storico.
# Usare il modulo ufficiale corrispondente (vedi analisi/README).
# Non usato dal kernel 3.0.
from core.kernel import KernelJarvis
from interfaccia.hud import HUDJarvis
import time



class JarvisOS:


    def __init__(self):

        self.kernel = KernelJarvis()

        self.hud = HUDJarvis()



    def avvia(self):

        print("""
================================
        J.A.R.V.I.S. OS
================================
""")


        risultato = self.kernel.avvia()


        if risultato:


            self.hud.collega_kernel(
                self.kernel
            )


            self.hud.avvia()


            self.hud.aggiorna_kernel()


            self.hud.mostra()


            print(
                "J.A.R.V.I.S. operativo."
            )


        else:

            print(
                "Errore durante l'avvio."
            )



    def esegui(self):


        while True:


            try:


                comando = input(
                    "\nTu: "
                )


                if comando.lower() in [

                    "esci",
                    "chiudi",
                    "stop"

                ]:


                    self.hud.ferma()

                    self.kernel.arresta()


                    print(
                        "J.A.R.V.I.S. spento."
                    )


                    break



                # Invio al modulo comandi

                risposta = self.kernel.esegui_comando(
                    comando
                )


                print(
                    "\nJ.A.R.V.I.S.:",
                    risposta
                )



            except KeyboardInterrupt:


                self.hud.ferma()

                self.kernel.arresta()


                print(
                    "\nJ.A.R.V.I.S. arrestato."
                )


                break





if __name__ == "__main__":


    jarvis = JarvisOS()


    jarvis.avvia()


    time.sleep(1)


    jarvis.esegui()
