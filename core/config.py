import json
import os


PERCORSO_CONFIG = "config/config.json"


class ConfigJarvis:
    """Gestisce la configurazione persistente di Jarvis."""

    def __init__(self):
        self.default = {
            "jarvis": {
                "nome": "Jarvis",
                "versione": "definitiva",
                "stato": "operativo",
            },
            "utente": {"nome": "Simone"},
            "base": {
                "dispositivo": "Motorola",
                "tipo": "Android",
                "principale": True,
            },
            "voce": {
                "wake_word": "jarvis",
                "wake_words": ["jarvis", "ehi jarvis", "hey jarvis"],
                "lingua": "it-IT",
                "motore": "piper",
                "modello": "voce/modelli/it_IT-jarvis.onnx",
                "velocita": 1.0,
                "volume": 100,
            },
            "memoria": {
                "attiva": True,
                "salvataggio": True,
                "percorso": "memoria",
            },
            "dispositivi": {
                "telefono": True,
                "computer": True,
                "rete": True,
                "bluetooth": True,
                "smart_home": True,
                "tv_lg": True,
            },
            "tv_lg": {
                "nome": "TV LG",
                "ip": "",
                "client_key": "",
                "timeout": 4,
            },
            "sistema": {
                "log": True,
                "avvio_automatico": False,
                "modalita_debug": False,
                "fallback_testuale": True,
            },
        }
        self.config = {}
        self.carica()

    def carica(self):
        cartella = os.path.dirname(PERCORSO_CONFIG)
        if cartella and not os.path.exists(cartella):
            os.makedirs(cartella)

        if not os.path.exists(PERCORSO_CONFIG):
            self.config = self.default.copy()
            self.salva()
            return

        try:
            with open(PERCORSO_CONFIG, "r", encoding="utf-8") as file:
                dati = json.load(file)
            self.config = self._completa(dati)
        except (OSError, ValueError, TypeError):
            self.config = self.default.copy()
            self.salva()

    def _completa(self, dati):
        """Completa configurazioni precedenti senza perdere valori esistenti."""
        configurazione = json.loads(json.dumps(self.default))
        for sezione, valori in dati.items():
            if isinstance(valori, dict) and isinstance(configurazione.get(sezione), dict):
                configurazione[sezione].update(valori)
            else:
                configurazione[sezione] = valori
        configurazione.setdefault("jarvis", {})["versione"] = "definitiva"
        return configurazione

    def salva(self):
        cartella = os.path.dirname(PERCORSO_CONFIG)
        if cartella and not os.path.exists(cartella):
            os.makedirs(cartella)
        with open(PERCORSO_CONFIG, "w", encoding="utf-8") as file:
            json.dump(self.config, file, indent=4, ensure_ascii=False)

    def ottieni(self, chiave, default=None):
        return self.config.get(chiave, default)

    def sezione(self, nome):
        return self.config.get(nome, {})

    def modifica(self, sezione, chiave, valore):
        self.config.setdefault(sezione, {})[chiave] = valore
        self.salva()

    def tutto(self):
        return self.config
