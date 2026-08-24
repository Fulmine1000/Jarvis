import datetime
import json
import os
import shutil

FILE_VERSIONE = "versione_jarvis.json"


class AggiornamentiJarvis:
    """Gestisce inventario dei moduli, versione e backup locali di Jarvis."""

    def __init__(self):
        self.versione = "definitiva"
        self.data = datetime.datetime.now().strftime("%d/%m/%Y")
        self.moduli = [
            "main.py", "core/kernel.py", "core/config.py", "core/logger.py",
            "core/event_bus.py", "core/manager.py", "memoria/memoria.py",
            "memoria/database.py", "memoria/profilo.py", "memoria/preferenze.py",
            "memoria/contesto.py", "memoria/conversazioni.py", "memoria/ricordi.py",
            "memoria/backup_memoria.py", "voce/ascoltatore.py", "voce/riconoscimento.py",
            "voce/sintesi.py", "voce/wake_word.py", "voce/motore_ascolto.py",
            "voce/assistente_voce.py", "comandi/gestore.py", "dispositivi/gestore.py",
            "dispositivi/connessione.py", "dispositivi/telefono.py", "dispositivi/computer.py",
            "dispositivi/rete.py", "dispositivi/bluetooth.py", "dispositivi/smart_home.py",
            "dispositivi/console.py", "dispositivi/identita.py", "dispositivi/telefono_controller.py",
            "moduli/voce_modulo.py", "moduli/dispositivi_modulo.py", "moduli/comandi_modulo.py",
            "plugin/plugin_base.py", "plugin/plugin_manager.py", "plugin/sistema.py",
            "interfaccia/hud.py", "personalita/personalita.py", "stato.py",
            "sicurezza.py", "aggiornamenti.py"
        ]

    def salva_versione(self):
        dati = {"versione": self.versione, "data": self.data, "moduli": self.moduli}
        with open(FILE_VERSIONE, "w", encoding="utf-8") as file:
            json.dump(dati, file, indent=4, ensure_ascii=False)
        return True

    def controlla_moduli(self):
        return {modulo: os.path.isfile(modulo) for modulo in self.moduli}

    def moduli_mancanti(self):
        return [modulo for modulo, presente in self.controlla_moduli().items() if not presente]

    def crea_backup(self, destinazione=None):
        nome = destinazione or "backup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(nome, exist_ok=True)
        for modulo, presente in self.controlla_moduli().items():
            if not presente:
                continue
            percorso = os.path.join(nome, modulo)
            os.makedirs(os.path.dirname(percorso), exist_ok=True)
            shutil.copy2(modulo, percorso)
        return nome

    def stato(self):
        controllo = self.controlla_moduli()
        return {
            "versione": self.versione,
            "data": self.data,
            "moduli": len(self.moduli),
            "presenti": sum(controllo.values()),
            "mancanti": len(self.moduli_mancanti()),
        }
