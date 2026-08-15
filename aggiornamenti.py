import json
import os
import shutil
import datetime


FILE_VERSIONE = "versione_jarvis.json"


class AggiornamentiJarvis:


    def __init__(self):

        self.versione = "1.0.0"

        self.data = datetime.datetime.now().strftime("%d/%m/%Y")

        self.moduli = [

            "jarvis.py",
            "voce.py",
            "ascolto.py",
            "wake_word.py",
            "personalita.py",
            "comandi.py",
            "configurazione.py",
            "gestore_memoria.py",
            "hud.py",
            "stato.py",
            "sicurezza.py",

            "dispositivi/computer.py",
            "dispositivi/telefono.py",
            "dispositivi/rete.py",
            "dispositivi/bluetooth.py",
            "dispositivi/smart_home.py",
            "dispositivi/console.py",
            "dispositivi/gestore.py"
        ]

        self.salva_versione()


    def salva_versione(self):

        dati = {

            "versione": self.versione,

            "data": self.data,

            "moduli": self.moduli

        }

        with open(
            FILE_VERSIONE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                dati,
                file,
                indent=4,
                ensure_ascii=False
            )


    def controlla_moduli(self):

        risultato = {}

        for modulo in self.moduli:

            risultato[modulo] = os.path.exists(modulo)

        return risultato


    def crea_backup(self):

        nome = "backup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        os.makedirs(nome, exist_ok=True)

        for modulo in self.moduli:

            if os.path.exists(modulo):

                destinazione = os.path.join(nome, modulo)

                os.makedirs(
                    os.path.dirname(destinazione),
                    exist_ok=True
                )

                shutil.copy2(
                    modulo,
                    destinazione
                )

        return nome


    def stato(self):

        return {

            "versione": self.versione,

            "data": self.data,

            "moduli": len(self.moduli)

        }



if __name__ == "__main__":

    aggiornamenti = AggiornamentiJarvis()

    print(
        aggiornamenti.stato()
    )

    print(
        aggiornamenti.controlla_moduli()
    )