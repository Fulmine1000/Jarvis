import datetime
import json
import os

FILE_LOG = "sicurezza_log.json"


class SicurezzaJarvis:
    """Controlli di base, autorizzazioni e audit locale di Jarvis."""

    def __init__(self, file_log=FILE_LOG):
        self.nome = "Sicurezza Jarvis"
        self.protezione = True
        self.utenti_autorizzati = ["Simone"]
        self.log = []
        self.file_log = file_log
        self.carica_log()

    def carica_log(self):
        if not os.path.exists(self.file_log):
            return
        try:
            with open(self.file_log, "r", encoding="utf-8") as file:
                dati = json.load(file)
            self.log = dati if isinstance(dati, list) else []
        except (OSError, ValueError, TypeError):
            self.log = []

    def salva_log(self):
        cartella = os.path.dirname(self.file_log)
        if cartella:
            os.makedirs(cartella, exist_ok=True)
        try:
            with open(self.file_log, "w", encoding="utf-8") as file:
                json.dump(self.log, file, indent=4, ensure_ascii=False)
            return True
        except OSError:
            return False

    def registra(self, azione, risultato):
        evento = {
            "ora": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "azione": str(azione),
            "risultato": str(risultato),
        }
        self.log.append(evento)
        return self.salva_log()

    def autorizza(self, utente):
        return str(utente).strip().casefold() in {
            nome.casefold() for nome in self.utenti_autorizzati
        }

    def richiede_conferma(self, comando):
        testo = str(comando or "").casefold()
        comandi_protetti = (
            "elimina",
            "formatta",
            "spegni computer",
            "modifica sistema",
            "resetta",
            "ripristina configurazione",
        )
        return any(parola in testo for parola in comandi_protetti)

    def stato(self):
        return {
            "protezione": self.protezione,
            "utenti": list(self.utenti_autorizzati),
            "eventi_registrati": len(self.log),
        }
