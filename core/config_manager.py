# DEPRECATO — mantenuto per riferimento storico.
# Usare il modulo ufficiale corrispondente (vedi analisi/README).
# Non usato dal kernel 3.0.
import json
import os



class ConfigManager:


    def __init__(
        self,
        percorso="config/config.json",
        logger=None
    ):

        self.percorso = percorso

        self.logger = logger

        self.config = {}



    def carica(self):


        try:

            if not os.path.exists(
                self.percorso
            ):

                return (
                    "File configurazione non trovato."
                )



            with open(
                self.percorso,
                "r",
                encoding="utf-8"
            ) as file:


                self.config = json.load(
                    file
                )



            if self.logger:

                self.logger.info(
                    "Configurazione caricata."
                )



            return (
                "Configurazione caricata."
            )



        except Exception as errore:


            if self.logger:

                self.logger.error(
                    str(errore)
                )


            return (
                f"Errore configurazione: {errore}"
            )







    def salva(self):


        try:


            with open(
                self.percorso,
                "w",
                encoding="utf-8"
            ) as file:


                json.dump(
                    self.config,
                    file,
                    indent=4,
                    ensure_ascii=False
                )



            return (
                "Configurazione salvata."
            )



        except Exception as errore:


            return (
                f"Errore salvataggio: {errore}"
            )







    def leggi(
        self,
        sezione,
        chiave,
        default=None
    ):


        try:

            return (
                self.config
                .get(sezione, {})
                .get(chiave, default)
            )


        except:


            return default







    def scrivi(
        self,
        sezione,
        chiave,
        valore
    ):


        if sezione not in self.config:

            self.config[sezione] = {}



        self.config[sezione][chiave] = valore



        return self.salva()







    def stato(self):


        return {


            "nome":

                "Config Manager",


            "stato":

                "attivo"
                if self.config
                else "vuoto",


            "file":

                self.percorso

        }