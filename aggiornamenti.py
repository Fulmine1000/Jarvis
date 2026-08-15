import json
import os
import shutil
import datetime


FILE_VERSIONE = "versione_jarvis.json"


class AggiornamentiJarvis:


    def __init__(self):

        self.versione = "3.0.0"

        self.data = datetime.datetime.now().strftime("%d/%m/%Y")

        self.moduli = [

            "main.py",

            "core/kernel.py",
            "core/config.py",
            "core/logger.py",
            "core/event_bus.py",
            "core/manager.py",

            "memoria/memoria.py",
            "memoria/database.py",
            "memoria/profilo.py",
            "memoria/preferenze.py",
            "memoria/contesto.py",
            "memoria/conversazioni.py",
            "memoria/ricordi.py",
            "memoria/backup_memoria.py",

            "voce/ascoltatore.py",
            "voce/riconoscimento.py",
            "voce/sintesi.py",
            "voce/wake_word.py",
            "voce/motore_ascolto.py",
            "voce/assistente_voce.py",

            "comandi/gestore.py",

            "dispositivi/gestore.py",
            "dispositivi/connessione.py",
            "dispositivi/telefono.py",
            "dispositivi/computer.py",
            "dispositivi/rete.py",
            "dispositivi/bluetooth.py",
            "dispositivi/smart_home.py",
            "dispositivi/console.py",
            "dispositivi/identita.py",
            "dispositivi/telefono_controller.py",

            "moduli/voce_modulo.py",
            "moduli/dispositivi_modulo.py",
            "moduli/comandi_modulo.py",

            "plugin/plugin_base.py",
            "plugin/plugin_manager.py",
            "plugin/sistema.py",

            "interfaccia/hud.py",
            "personalita/personalita.py",
            "stato.py",
            "sicurezza.py",
            "aggiornamenti.py"
        ]

        # NB: salva_versione() non viene chiamato in __init__ per evitare
        # di sovrascrivere versione_jarvis.json a ogni avvio del kernel.
        # Usare salva_versione() esplicitamente quando si vuole persistere.


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