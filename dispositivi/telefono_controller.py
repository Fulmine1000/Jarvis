import subprocess
import datetime



class ControllerTelefono:


    def __init__(
        self,
        logger=None
    ):

        self.logger = logger

        self.connesso = False

        self.ultimo_controllo = None







    def verifica_connessione(self):


        try:

            risultato = subprocess.check_output(
                [
                    "adb",
                    "devices"
                ],
                text=True
            )


            if "\tdevice" in risultato:

                self.connesso = True

            else:

                self.connesso = False



        except:

            self.connesso = False



        self.ultimo_controllo = (
            datetime.datetime.now()
            .strftime("%d/%m/%Y %H:%M:%S")
        )



        return self.connesso







    def batteria(self):


        if not self.connesso:

            return "Telefono non collegato."



        try:

            risultato = subprocess.check_output(
                [
                    "adb",
                    "shell",
                    "dumpsys",
                    "battery"
                ],
                text=True
            )


            for riga in risultato.split("\n"):


                if "level:" in riga:


                    percentuale = (
                        riga
                        .split(":")[1]
                        .strip()
                    )


                    return (
                        f"Batteria telefono: {percentuale}%"
                    )



        except:

            return "Errore lettura batteria."



        return "Batteria non disponibile."







    def apri_app(
        self,
        pacchetto
    ):


        if not self.connesso:

            return "Telefono non collegato."



        try:

            subprocess.run(
                [
                    "adb",
                    "shell",
                    "monkey",
                    "-p",
                    pacchetto,
                    "1"
                ]
            )


            return (
                f"Applicazione {pacchetto} aperta."
            )



        except:

            return (
                "Errore apertura applicazione."
            )







    def stato(self):


        return {


            "nome":

                "Controller Telefono",


            "connesso":

                self.connesso,


            "ultimo_controllo":

                self.ultimo_controllo

        }