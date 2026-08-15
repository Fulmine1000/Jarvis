import platform


class ConsoleJarvis:


    def __init__(self):

        self.nome = "Console"

        self.console = []



    def aggiungi_console(
        self,
        nome,
        tipo
    ):

        nuova = {

            "nome": nome,

            "tipo": tipo,

            "stato": "non collegata"

        }


        self.console.append(
            nuova
        )


        return (
            f"{nome} aggiunta."
        )



    def collega(
        self,
        nome
    ):

        for console in self.console:

            if console["nome"].lower() == nome.lower():

                console["stato"] = "collegata"

                return (
                    f"{nome} collegata."
                )


        return (
            "Console non trovata."
        )



    def scollega(
        self,
        nome
    ):

        for console in self.console:

            if console["nome"].lower() == nome.lower():

                console["stato"] = "non collegata"

                return (
                    f"{nome} scollegata."
                )


        return (
            "Console non trovata."
        )



    def lista(self):

        return self.console



    def informazioni(self):

        return {

            "modulo": self.nome,

            "sistema": platform.system(),

            "console": self.console

        }



    def stato(self):

        return self.informazioni()




if __name__ == "__main__":


    console = ConsoleJarvis()


    print(
        console.aggiungi_console(
            "PlayStation",
            "PS"
        )
    )


    print(
        console.stato()
    )
