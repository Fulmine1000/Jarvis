from dispositivi.gestore import GestoreDispositivi

from dispositivi.computer import ComputerJarvis
from dispositivi.rete import Rete
from dispositivi.bluetooth import Bluetooth
from dispositivi.telefono import TelefonoJarvis
from dispositivi.connessione import ConnessioneDispositivi
from dispositivi.smart_home import SmartHomeJarvis





class ModuloDispositivi:


    def __init__(self, kernel):

        self.kernel = kernel

        self.nome = "Dispositivi"

        self.attivo = False

        self.gestore = None

        self.connessione = None







    def avvia(self):


        logger = self.kernel.logger



        # CONNESSIONE DISPOSITIVI

        self.connessione = ConnessioneDispositivi(

            logger

        )


        self.connessione.avvia()







        # GESTORE CENTRALE

        self.gestore = GestoreDispositivi(

            logger

        )


        self.gestore.collega_connessione(

            self.connessione

        )







        # COMPUTER

        computer = ComputerJarvis()


        self.gestore.registra(

            "computer",

            computer

        )







        # RETE

        rete = Rete()


        self.gestore.registra(

            "rete",

            rete

        )







        # BLUETOOTH

        bluetooth = Bluetooth()


        self.gestore.registra(

            "bluetooth",

            bluetooth

        )

        # SMART HOME

        smart_home = SmartHomeJarvis()


        self.gestore.registra(

            "smart_home",

            smart_home

        )







        # ==========================
        # BASE UFFICIALE MOTOROLA
        # ==========================


        motorola = TelefonoJarvis(

            nome="Motorola",

            modello="Motorola Base J.A.R.V.I.S.",

            base=True,

            logger=logger

        )



        self.gestore.registra(

            "motorola",

            motorola

        )



        self.connessione.connetti(

            "motorola"

        )







        # ==========================
        # TELEFONO SECONDARIO
        # ==========================


        telefono = TelefonoJarvis(

            nome="Telefono",

            modello="Dispositivo Android",

            base=False,

            logger=logger

        )



        self.gestore.registra(

            "telefono",

            telefono

        )



        self.connessione.connetti(

            "telefono"

        )







        self.attivo = True



        logger.info(

            "Modulo Dispositivi J.A.R.V.I.S. OS 3.0 attivo."

        )



        return True







    def get_gestore(self):

        return self.gestore







    def get_connessione(self):

        return self.connessione







    def stato(self):


        return {


            "nome":

                self.nome,


            "stato":

                "attivo"

                if self.attivo

                else "errore",



            "dispositivi":

                self.gestore.elenco()

                if self.gestore

                else [],



            "connessione":

                self.connessione.stato()

                if self.connessione

                else {}

        }
