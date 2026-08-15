import datetime

from dispositivi.identita import IdentitaDispositivo





class TelefonoJarvis:


    def __init__(
        self,
        nome,
        modello="Sconosciuto",
        base=False,
        logger=None
    ):


        self.nome = nome

        self.modello = modello

        self.base = base

        self.logger = logger



        # IDENTITÀ DISPOSITIVO

        self.identita = IdentitaDispositivo(

            nome,

            "base" if base else "telefono"

        )



        self.connesso = False

        self.sessione_attiva = False

        self.principale = False



        self.app_aperte = []

        self.ultima_sincronizzazione = None



        self.batteria = 100

        self.wifi = True

        self.bluetooth = True







    def connetti(self):


        self.connesso = True



        if self.logger:

            self.logger.info(

                f"{self.nome} collegato."

            )


        return f"{self.nome} collegato."









    def disconnetti(self):


        self.connesso = False

        self.sessione_attiva = False

        self.principale = False



        return f"{self.nome} scollegato."









    def attiva_sessione(self):


        if self.base:


            return (

                "La base non può essere trasferita."

            )



        if not self.connesso:

            self.connetti()



        self.sessione_attiva = True

        self.principale = True



        return (

            "Jarvis ora è attivo sul telefono."

        )









    def ritorna_alla_base(self):


        self.sincronizza()



        self.sessione_attiva = False

        self.principale = False



        return (

            "Jarvis è tornato alla base."

        )









    def apri_app(
        self,
        app
    ):


        if not self.sessione_attiva:


            return (

                "Telefono non attivo come dispositivo principale."

            )



        if app not in self.app_aperte:


            self.app_aperte.append(

                app

            )



        return f"Apertura applicazione: {app}"









    def chiudi_app(
        self,
        app
    ):


        if app in self.app_aperte:


            self.app_aperte.remove(

                app

            )


            return f"{app} chiusa."



        return "Applicazione non trovata."









    def sincronizza(self):


        self.ultima_sincronizzazione = (

            datetime.datetime.now()

            .strftime(

                "%d/%m/%Y %H:%M:%S"

            )

        )


        return "Sincronizzazione completata."









    def informazioni(self):


        return {


            "modello":

                self.modello,


            "base":

                self.base,


            "connesso":

                self.connesso,


            "identita":

                self.identita.informazioni()

        }









    def stato(self):


        return {


            "nome":

                self.nome,


            "modello":

                self.modello,


            "tipo":

                "base"

                if self.base

                else "telefono",



            "connesso":

                self.connesso,



            "dispositivo_principale":

                self.principale,



            "sessione":

                self.sessione_attiva,



            "app_aperte":

                self.app_aperte,



            "batteria":

                self.batteria,



            "wifi":

                self.wifi,



            "bluetooth":

                self.bluetooth,



            "ultima_sincronizzazione":

                self.ultima_sincronizzazione,



            "identita":

                self.identita.informazioni()

        }
