import json
import os
import shutil


BASE_JARVIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERCORSO_CONFIG = os.path.join(BASE_JARVIS, "config", "config.json")


class ConfigJarvis:
    """Gestisce la configurazione persistente di Jarvis senza perdere dati corrotti."""

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
        self.ultimo_errore_caricamento = None
        self._config_non_valida = False
        self.carica()

    def carica(self):
        """Carica la configurazione; non sovrascrive file esistenti non leggibili."""
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
            if not isinstance(dati, dict):
                raise ValueError("La radice di config.json deve essere un oggetto JSON.")
            self.config = self._completa(dati)
            self.ultimo_errore_caricamento = None
        except (OSError, ValueError, TypeError) as errore:
            # Mantieni i valori predefiniti in memoria, ma conserva il file
            # originale: riscriverlo qui potrebbe cancellare le impostazioni
            # dell'utente e rendere impossibile recuperarle.
            self.config = json.loads(json.dumps(self.default))
            self.ultimo_errore_caricamento = str(errore)
            self._config_non_valida = True

    def _completa(self, dati):
        """Completa configurazioni precedenti ignorando sezioni malformate."""
        configurazione = json.loads(json.dumps(self.default))
        if not isinstance(dati, dict):
            return configurazione

        for sezione, valori in dati.items():
            valore_predefinito = configurazione.get(sezione)
            if isinstance(valore_predefinito, dict):
                # Una sezione nota deve restare un dizionario: un valore di
                # tipo stringa/lista non deve rompere le chiamate a sezione().get().
                if isinstance(valori, dict):
                    valore_predefinito.update(valori)
                continue

            # Le sezioni aggiuntive sono ammesse solo come dizionari.
            if isinstance(valori, dict):
                configurazione[sezione] = valori

        configurazione.setdefault("jarvis", {})["versione"] = "definitiva"
        return configurazione

    def salva(self):
        # Se una configurazione corrotta viene poi modificata, conserva una
        # copia del file originale prima di scrivere i valori recuperati.
        if self._config_non_valida and os.path.isfile(PERCORSO_CONFIG):
            backup = PERCORSO_CONFIG + ".corrotto"
            indice = 1
            while os.path.exists(backup):
                backup = PERCORSO_CONFIG + f".corrotto.{indice}"
                indice += 1
            shutil.copy2(PERCORSO_CONFIG, backup)

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
        self._config_non_valida = False
        self.ultimo_errore_caricamento = None

    def ottieni(self, chiave, default=None):
        return self.config.get(chiave, default)

    def sezione(self, nome):
        valore = self.config.get(nome, {})
        return valore if isinstance(valore, dict) else {}

    def modifica(self, sezione, chiave, valore):
        valori = self.config.get(sezione)
        if not isinstance(valori, dict):
            valori = {}
            self.config[sezione] = valori
        valori[chiave] = valore
        self.salva()

    def tutto(self):
        return self.config
