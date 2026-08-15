from abc import ABC, abstractmethod



class PluginBase(ABC):


    def __init__(self, kernel):

        self.kernel = kernel

        self.nome = "Plugin"

        self.versione = "1.0"

        self.attivo = False



    @abstractmethod
    def avvia(self):

        pass



    @abstractmethod
    def ferma(self):

        pass



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