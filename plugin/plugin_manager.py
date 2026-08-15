import os
import importlib



class PluginManager:


    def __init__(self, kernel=None):

        self.kernel = kernel

        self.plugin = {}



    def registra(
        self,
        nome,
        plugin
    ):

        self.plugin[nome] = plugin



    def carica_plugin(self):

        cartella = "plugin"


        if not os.path.exists(cartella):

            os.makedirs(cartella)

            return



        for file in os.listdir(cartella):

            if (
                file.endswith(".py")
                and file not in [
                    "__init__.py",
                    "plugin_manager.py",
                    "plugin_base.py"
                ]
            ):


                nome = file[:-3]


                try:

                    modulo = importlib.import_module(
                        f"plugin.{nome}"
                    )


                    if hasattr(
                        modulo,
                        "crea_plugin"
                    ):


                        plugin = modulo.crea_plugin(
                            self.kernel
                        )


                        self.registra(
                            nome,
                            plugin
                        )


                        print(
                            f"Plugin caricato: {nome}"
                        )



                except Exception as errore:


                    print(
                        f"Errore caricamento plugin {nome}: {errore}"
                    )



    def avvia_tutti(self):


        for nome, plugin in self.plugin.items():

            try:


                plugin.avvia()


                plugin.attivo = True


                print(
                    f"Plugin attivo: {nome}"
                )



            except Exception as errore:


                print(
                    f"Errore avvio plugin {nome}: {errore}"
                )



    def ferma_tutti(self):


        for nome, plugin in self.plugin.items():

            try:


                plugin.ferma()


                plugin.attivo = False



            except Exception as errore:


                print(
                    f"Errore chiusura {nome}: {errore}"
                )



    def stato(self):


        risultato = {}


        for nome, plugin in self.plugin.items():

            risultato[nome] = plugin.stato()



        return risultato



    def elenco(self):

        return list(
            self.plugin.keys()
        )
