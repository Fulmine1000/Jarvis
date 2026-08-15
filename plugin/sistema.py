from plugin.plugin_base import PluginBase



class SistemaPlugin(PluginBase):


    def __init__(self, kernel):

        super().__init__(kernel)

        self.nome = "Sistema"

        self.versione = "1.0"



    def avvia(self):

        self.attivo = True


        print(
            "Plugin Sistema avviato."
        )



    def ferma(self):

        self.attivo = False


        print(
            "Plugin Sistema fermato."
        )



    def stato(self):

        return {

            "nome":
                self.nome,

            "versione":
                self.versione,

            "stato":
                "attivo"
                if self.attivo
                else "spento"

        }



def crea_plugin(kernel):

    return SistemaPlugin(
        kernel
    )