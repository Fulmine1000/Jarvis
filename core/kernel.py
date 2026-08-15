from datetime import datetime

from core.logger import LoggerJarvis
from core.event_bus import EventBus
from core.manager import ModuleManager
from core.config import ConfigJarvis

from memoria.memoria import MemoriaJarvis

from moduli.comandi_modulo import ModuloComandi
from moduli.dispositivi_modulo import ModuloDispositivi
from moduli.voce_modulo import ModuloVoce

from plugin.plugin_manager import PluginManager





class KernelJarvis:


    def __init__(self):


        self.config = ConfigJarvis()


        dati = self.config.sezione("jarvis")


        self.nome = dati.get(

            "nome",

            "Jarvis"

        )


        self.versione = dati.get(

            "versione",

            "3.0"

        )


        self.base = self.config.sezione(

            "base"

        ).get(

            "dispositivo",

            "Motorola"

        )


        self.stato = "Spento"


        self.avvio = None






        self.logger = LoggerJarvis()


        self.event_bus = EventBus()


        self.manager = ModuleManager(

            self.logger

        )


        self.plugin_manager = PluginManager(

            self

        )






        self.memoria = MemoriaJarvis(

            self.logger

        )


        self.modulo_dispositivi = ModuloDispositivi(

            self

        )


        self.modulo_comandi = ModuloComandi(

            self

        )


        self.modulo_voce = ModuloVoce(

            self

        )








    def avvia(self):


        self.logger.info(

            "Avvio Kernel Jarvis..."

        )


        self.stato = "Avvio"


        self.avvio = datetime.now().strftime(

            "%d/%m/%Y %H:%M:%S"

        )






        moduli = {


            "Memoria":

                self.memoria,


            "Dispositivi":

                self.modulo_dispositivi,


            "Comandi":

                self.modulo_comandi,


            "Voce":

                self.modulo_voce

        }





        for nome, modulo in moduli.items():

            self.manager.registra(

                nome,

                modulo

            )





        for nome in moduli:

            self.manager.avvia(

                nome

            )






        try:

            self.plugin_manager.carica_plugin()

            self.plugin_manager.avvia_tutti()

        except Exception:

            pass






        self.stato = "Operativo"


        self.logger.info(

            "Jarvis operativo."

        )


        return True








    def parla(

        self,

        testo

    ):


        return self.modulo_voce.rispondi(

            testo

        )








    def esegui_comando(

        self,

        comando

    ):


        risposta = self.modulo_comandi.esegui(

            comando

        )


        if risposta:

            self.parla(

                risposta

            )


        return risposta








    def stato_sistema(self):


        return {


            "nome":

                self.nome,


            "versione":

                self.versione,


            "stato":

                self.stato,


            "base":

                self.base,


            "avvio":

                self.avvio,


            "memoria":

                self.memoria.stato(),


            "voce":

                self.modulo_voce.stato(),


            "comandi":

                self.modulo_comandi.stato(),


            "dispositivi":

                self.modulo_dispositivi.stato(),


            "plugin":

                self.plugin_manager.stato(),


            "moduli":

                self.manager.stato()

        }








    def arresta(self):


        self.logger.info(

            "Arresto Jarvis..."

        )


        try:

            self.plugin_manager.ferma_tutti()

        except Exception:

            pass





        try:

            self.modulo_voce.ferma()

        except Exception:

            pass





        self.stato = "Spento"


        self.logger.info(

            "Jarvis arrestato."

        )
