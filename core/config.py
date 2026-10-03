import json
import os


BASE_JARVIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERCORSO_CONFIG = os.path.join(BASE_JARVIS, "config", "config.json")


class ConfigJarvis:
    """Gestisce la configurazione persistente di Jarvis."""

    def __init__(self):
        self.default = {
            "jarvis": {
                "nome": "J.A.R.V.I.S.",
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
                "motore": "voicepack",
                "modello": "voce/modelli/it_IT-riccardo-x_low.onnx",
                "velocita": 0.92,
                "volume": 100,
                "stile": "Jarvis Cinematico PS3",
                "pausa_cinematica": True,
                "rate_cinematico": 156,
                "sample_rate": 16000,
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
                "hud": True,
            },
        }
        self.config = {}
        self.carica()

    def carica(self):
        cartella = os.path.dirname(PERCORSO_CONFIG)
        if cartella and not os.path.exists(cartella):
            os.makedirs(cartella)

        if not os.path.exists(PERCORSO_CONFIG):
            self.config = json.loads(json.dumps(self.default))
            self.salva()
            return

        try:
            with open(PERCORSO_CONFIG, "r", encoding="utf-8") as file:
                dati = json.load(file)
            self.config = self._completa(dati)
        except (OSError, ValueError, TypeError):
            self.config = json.loads(json.dumps(self.default))
            self.salva()

    def _completa(self, dati):
        """Completa configurazioni precedenti senza perdere valori esistenti."""
        configurazione = json.loads(json.dumps(self.default))
        if not isinstance(dati, dict):
            return configurazione

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
        temporaneo = PERCORSO_CONFIG + ".tmp"
        with open(temporaneo, "w", encoding="utf-8") as file:
            json.dump(self.config, file, indent=4, ensure_ascii=False)
            file.flush()
            try:
                os.fsync(file.fileno())
            except OSError:
                pass
        os.replace(temporaneo, PERCORSO_CONFIG)

    def ottieni(self, chiave, default=None):
        return self.config.get(chiave, default)

    def sezione(self, nome):
        return self.config.get(nome, {})

    def modifica(self, sezione, chiave, valore):
        self.config.setdefault(sezione, {})[chiave] = valore
        self.salva()

    def tutto(self):
        return self.config
