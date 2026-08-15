import datetime



class HUDJarvis:


    def __init__(self):

        self.nome = "J.A.R.V.I.S. HUD"

        self.attivo = False

        self.dati = {}

        self.eventi = []

        self.kernel = None



    def avvia(self):

        self.attivo = True

        self.registra_evento(
            "HUD avviato"
        )



    def ferma(self):

        self.attivo = False

        self.registra_evento(
            "HUD spento"
        )



    def collega_kernel(self, kernel):

        self.kernel = kernel

        self.registra_evento(
            "Kernel collegato"
        )



    def aggiorna(self, dati):

        self.dati = dati



    def aggiorna_kernel(self):

        if self.kernel:

            self.dati = self.kernel.stato_sistema()



    def registra_evento(self, messaggio):

        self.eventi.append(

            {
                "ora":
                    datetime.datetime.now().strftime(
                        "%H:%M:%S"
                    ),

                "evento":
                    messaggio
            }

        )



    def mostra(self):

        print()

        print("╔════════════════════════════╗")
        print("║       J.A.R.V.I.S. HUD     ║")
        print("╚════════════════════════════╝")

        print()


        print(
            "Sistema:",
            self.dati.get(
                "nome",
                "N/D"
            )
        )


        print(
            "Versione:",
            self.dati.get(
                "versione",
                "N/D"
            )
        )


        print(
            "Stato:",
            self.dati.get(
                "stato",
                "N/D"
            )
        )


        print()



        # MEMORIA

        memoria = self.dati.get(
            "memoria",
            {}
        )


        print(
            "Memoria:",
            "Attiva 🧠"
            if memoria.get("stato") == "attiva"
            else "Spenta 🧠"
        )



        # COMANDI

        comandi = self.dati.get(
            "comandi",
            {}
        )


        print(
            "Comandi:",
            "Attivo 💬"
            if comandi.get("stato") == "attivo"
            else "Spento 💬"
        )



        print()


        # MODULI

        print(
            "Moduli:"
        )


        moduli = self.dati.get(
            "moduli",
            {}
        )


        if moduli:

            for nome, stato in moduli.items():

                if isinstance(stato, dict):

                    stato = stato.get(
                        "stato",
                        "N/D"
                    )

                print(
                    f" - {nome}: {stato}"
                )

        else:

            print(
                " Nessun modulo attivo"
            )



        print()



        # DISPOSITIVI

        print(
            "Dispositivi:"
        )


        dispositivi = self.dati.get(
            "dispositivi",
            {}
        )


        if isinstance(dispositivi, dict) and dispositivi:


            for nome, stato in dispositivi.items():

                if isinstance(stato, dict):

                    valore = stato.get(
                        "stato",
                        "N/D"
                    )

                else:

                    valore = stato


                print(
                    f" - {nome}: {valore}"
                )


        else:

            print(
                " Nessun dispositivo"
            )



        print()


        print(
            "Ultimi eventi:"
        )


        for evento in self.eventi[-5:]:

            print(
                f" [{evento['ora']}] {evento['evento']}"
            )


        print()



    def stato(self):

        return {

            "attivo":
                self.attivo,

            "dati":
                self.dati,

            "eventi":
                self.eventi

        }



if __name__ == "__main__":


    hud = HUDJarvis()

    hud.avvia()


    hud.aggiorna(

        {

            "nome":
                "J.A.R.V.I.S. OS",

            "versione":
                "2.0.0",

            "stato":
                "Operativo",


            "memoria":
                {
                    "stato":
                        "attiva"
                },


            "comandi":
                {
                    "stato":
                        "attivo"
                },


            "moduli":
                {

                    "Memoria":
                        "attivo",

                    "Dispositivi":
                        "attivo",

                    "Comandi":
                        "attivo"

                },


            "dispositivi":
                {

                    "computer":
                        {
                            "stato":
                                "acceso"
                        },

                    "rete":
                        {
                            "stato":
                                "online"
                        },

                    "bluetooth":
                        {
                            "stato":
                                "attivo"
                        }

                }

        }

    )


    hud.mostra()
