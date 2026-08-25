import json
import os
import tempfile
from datetime import datetime

FILE_DATABASE = "memoria/database.json"


class DatabaseMemoria:
    """Persistenza JSON della memoria di Jarvis con salvataggio atomico."""

    def __init__(self, percorso=FILE_DATABASE):
        self.file_database = percorso
        self.crea_cartella()
        self.dati = {}
        self.carica()

    def crea_cartella(self):
        cartella = os.path.dirname(self.file_database)
        if cartella:
            os.makedirs(cartella, exist_ok=True)

    def carica(self):
        if not os.path.exists(self.file_database):
            self.salva()
            return
        try:
            with open(self.file_database, "r", encoding="utf-8") as file:
                dati = json.load(file)
            self.dati = dati if isinstance(dati, dict) else {}
        except (OSError, ValueError, TypeError):
            self.dati = {}

    def salva(self):
        self.crea_cartella()
        cartella = os.path.dirname(os.path.abspath(self.file_database)) or "."
        fd, temporaneo = tempfile.mkstemp(prefix=".jarvis_memoria_", suffix=".json", dir=cartella)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(self.dati, file, indent=4, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporaneo, self.file_database)
            return True
        except (OSError, TypeError, ValueError):
            try:
                os.remove(temporaneo)
            except OSError:
                pass
            return False

    def aggiungi(self, categoria, chiave, valore):
        categoria = str(categoria)
        chiave = str(chiave)
        self.dati.setdefault(categoria, {})[chiave] = {
            "valore": valore,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }
        return self.salva()

    def leggi(self, categoria, chiave):
        return self.dati.get(str(categoria), {}).get(str(chiave))

    def elimina(self, categoria, chiave):
        categoria = str(categoria)
        chiave = str(chiave)
        dati_categoria = self.dati.get(categoria)
        if not isinstance(dati_categoria, dict) or chiave not in dati_categoria:
            return False
        del dati_categoria[chiave]
        if not dati_categoria:
            self.dati.pop(categoria, None)
        self.salva()
        return True

    def lista(self, categoria):
        dati = self.dati.get(str(categoria), {})
        return dict(dati) if isinstance(dati, dict) else {}

    def tutto(self):
        return dict(self.dati)

    def numero_ricordi(self):
        return sum(len(valore) for valore in self.dati.values() if isinstance(valore, dict))
