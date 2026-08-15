import datetime





class GestoreComandi:


    def __init__(
        self,
        memoria=None,
        personalita=None,
        dispositivi=None,
        kernel=None,
        logger=None
    ):

        self.memoria = memoria

        self.personalita = personalita

        self.dispositivi = dispositivi

        self.kernel = kernel

        self.logger = logger

        self.attivo = False

        self.comandi_personalizzati = {}







    def avvia(self):

        self.attivo = True


        if self.logger:

            self.logger.info(
                "Gestore comandi J.A.R.V.I.S. OS 3.0 avviato."
            )


        return True







    def esegui(
        self,
        comando
    ):


        if not comando:

            return "Comando vuoto."



        comando = comando.lower().strip()







        # ==========================
        # DISPOSITIVI
        # ==========================



        if "stato dispositivi" in comando:


            if self.dispositivi:

                return str(
                    self.dispositivi.stato_tutti()
                )


            return "Gestore dispositivi non disponibile."







        if "quali dispositivi" in comando:


            if self.dispositivi:

                return str(
                    self.dispositivi.elenco()
                )


            return "Nessun dispositivo registrato."







        # ==========================
        # MOTOROLA BASE
        # ==========================



        if "stato motorola" in comando:


            motorola = self.prendi(
                "motorola"
            )


            if motorola:

                return str(
                    motorola.stato()
                )


            return "Motorola non disponibile."







        if "identifica motorola" in comando:


            motorola = self.prendi(
                "motorola"
            )


            if motorola:


                return (

                    "La base principale è "
                    f"{motorola.nome}. "
                    f"Modello: {motorola.modello}."

                )


            return "Base Motorola non disponibile."







        if "sincronizza motorola" in comando:


            if self.dispositivi:


                return self.dispositivi.sincronizza(

                    "motorola"

                )


            return "Connessione non disponibile."







        if "torna al motorola" in comando or "ritorna alla base" in comando:


            motorola = self.prendi(
                "motorola"
            )


            if motorola:


                motorola.principale = True

                motorola.sessione_attiva = False


                return (

                    "Jarvis è tornato alla base Motorola."

                )


            return "Base Motorola non disponibile."







        # ==========================
        # TELEFONO
        # ==========================



        if "trasferisciti sul telefono" in comando:


            telefono = self.prendi(
                "telefono"
            )


            if telefono:


                return telefono.attiva_sessione()



            return "Telefono non disponibile."







        if "stato telefono" in comando:


            telefono = self.prendi(
                "telefono"
            )


            if telefono:


                return str(
                    telefono.stato()
                )


            return "Telefono non disponibile."







        # ==========================
        # PERSONALITÀ
        # ==========================


        if "buongiorno" in comando or "buonasera" in comando:


            if self.personalita:

                return self.personalita.saluto()


            return "Sistema pronto."





        if "come stai" in comando:


            if self.personalita:

                return self.personalita.come_stai()


            return "Tutti i sistemi sono operativi."





        if "aiutami" in comando:


            if self.personalita:

                return self.personalita.aiuto()


            return (
                "Posso gestire sistema, "
                "dispositivi e memoria."
            )







        # ==========================
        # ORA E DATA
        # ==========================


        if "che ore sono" in comando:


            ora = datetime.datetime.now().strftime(
                "%H:%M"
            )


            return f"Sono le {ora}."







        if "che giorno è" in comando or "che data è" in comando:


            data = datetime.datetime.now().strftime(
                "%d/%m/%Y"
            )


            return f"Oggi è il {data}."







        # ==========================
        # MEMORIA
        # ==========================


        if comando.startswith(
            "ricorda "
        ):


            ricordo = comando.replace(
                "ricorda ",
                ""
            )


            if self.memoria:


                parti = ricordo.split(
                    " è ",
                    1
                )


                if len(parti) == 2:


                    return self.memoria.ricorda(

                        parti[0],

                        parti[1]

                    )



            return "Non riesco a salvare il ricordo."







        if "cosa ricordi di me" in comando:


            if self.memoria:


                return self.memoria.profilo.mostra_profilo()



            return "Memoria non disponibile."







        # ==========================
        # NOME UTENTE
        # ==========================


        if comando.startswith(
            "chiamami "
        ):


            nome = comando.replace(
                "chiamami ",
                ""
            )



            if self.kernel and hasattr(
                self.kernel,
                "preferenze"
            ):


                return self.kernel.preferenze.imposta(

                    "nome_utente",

                    nome

                )



            return f"Va bene, ti chiamerò {nome}."







        if "come mi chiamo" in comando:


            if self.kernel and hasattr(
                self.kernel,
                "preferenze"
            ):


                nome = self.kernel.preferenze.leggi(

                    "nome_utente"

                )


                if nome:

                    return f"Ti chiami {nome}."



            return "Non conosco ancora il tuo nome."







        # ==========================
        # APPLICAZIONI TELEFONO
        # ==========================


        if comando.startswith("apri "):


            app = comando.replace(
                "apri ",
                ""
            )


            telefono = self.prendi(
                "telefono"
            )


            if telefono:

                return telefono.apri_app(
                    app
                )



        if comando.startswith("chiudi "):


            app = comando.replace(
                "chiudi ",
                ""
            )


            telefono = self.prendi(
                "telefono"
            )


            if telefono:

                return telefono.chiudi_app(
                    app
                )







        # ==========================
        # STATO TELEFONO
        # ==========================


        if "batteria telefono" in comando:


            telefono = self.prendi(
                "telefono"
            )


            if telefono:

                return (
                    f"Batteria telefono: "
                    f"{telefono.batteria}%"
                )





        if "wifi telefono" in comando:


            telefono = self.prendi(
                "telefono"
            )


            if telefono:

                return (
                    "Wi-Fi telefono attivo."
                    if telefono.wifi
                    else
                    "Wi-Fi telefono spento."
                )





        if "bluetooth telefono" in comando:


            telefono = self.prendi(
                "telefono"
            )


            if telefono:

                return (
                    "Bluetooth telefono attivo."
                    if telefono.bluetooth
                    else
                    "Bluetooth telefono spento."
                )







        # ==========================
        # SMART HOME
        # ==========================


        if comando.startswith(
            "accendi "
        ):


            nome = comando.replace(
                "accendi ",
                ""
            )


            casa = self.prendi(
                "smart_home"
            )


            if casa:

                return casa.accendi(
                    nome
                )





        if comando.startswith(
            "spegni "
        ):


            nome = comando.replace(
                "spegni ",
                ""
            )


            casa = self.prendi(
                "smart_home"
            )


            if casa:

                return casa.spegni(
                    nome
                )







        # ==========================
        # COMANDI PERSONALIZZATI
        # ==========================


        for nome, funzione in self.comandi_personalizzati.items():


            if nome in comando:

                return funzione()







        return (
            "Non ho trovato un comando compatibile."
        )







    def prendi(
        self,
        nome
    ):


        if self.dispositivi:


            return self.dispositivi.cerca(
                nome
            )


        return None







    def get_connessione(self):


        if self.kernel and self.kernel.modulo_dispositivi:


            return (
                self.kernel.modulo_dispositivi
                .get_connessione()
            )


        return None







    def aggiungi_comando(
        self,
        nome,
        funzione
    ):


        self.comandi_personalizzati[nome] = funzione


        return (
            f"Comando {nome} aggiunto."
        )







    def stato(self):


        return {


            "nome":

                "Gestore Comandi",


            "stato":

                "attivo"
                if self.attivo
                else
                "spento"

        }
