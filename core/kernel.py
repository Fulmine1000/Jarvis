from datetime import datetime

from core.logger import LoggerJarvis
from core.event_bus import EventBus
from core.manager import ModuleManager
from core.config import ConfigJarvis

from memoria.memoria import MemoriaJarvis
from memoria.preferenze import PreferenzeJarvis
from memoria.contesto import ContestoJarvis

from personalita.personalita import PersonalitaJarvis

from stato import StatoJarvis
from sicurezza import SicurezzaJarvis
from aggiornamenti import AggiornamentiJarvis

from moduli.comandi_modulo import ModuloComandi
from moduli.dispositivi_modulo import ModuloDispositivi
from moduli.voce_modulo import ModuloVoce

from plugin.plugin_manager import PluginManager


class KernelJarvis:
    """Kernel centrale di Jarvis 3.0.

    Coordina config, logger, event bus, moduli (memoria, dispositivi, comandi,
    voce), personalità, preferenze, contesto, stato, sicurezza, aggiornamenti e
    plugin. Tutte le dipendenze opzionali (audio, Vosk, psutil) sono gestite
    in modo che il kernel avvii comunque in modalità degradata.
    """

    def __init__(self):

        self.config = ConfigJarvis()

        dati = self.config.sezione("jarvis")

        self.nome = dati.get("nome", "Jarvis")

        self.versione = dati.get("versione", "3.0")

        self.base = self.config.sezione("base").get(
            "dispositivo",
            "Motorola"
        )

        self.stato = "Spento"
        self.avvio = None

        # --- CORE ---
        self.logger = LoggerJarvis()
        self.event_bus = EventBus()
        self.manager = ModuleManager(self.logger)
        self.plugin_manager = PluginManager(self)

        # --- SERVIZI TRASVERSALI ---
        self.memoria = MemoriaJarvis(self.logger)
        self.preferenze = PreferenzeJarvis()
        self.contesto = ContestoJarvis()
        self.personalita = PersonalitaJarvis()
        self.stato_sistema_modulo = StatoJarvis()
        self.sicurezza = SicurezzaJarvis()
        self.aggiornamenti = AggiornamentiJarvis()

        # --- MODULI ---
        self.modulo_dispositivi = ModuloDispositivi(self)
        self.modulo_comandi = ModuloComandi(self)
        self.modulo_voce = ModuloVoce(self)

        # Flag di disponibilità voce (valorizzato in avvia)
        self.voce_disponibile = False

    def avvia(self):

        self.logger.info("Avvio Kernel Jarvis...")

        self.stato = "Avvio"

        self.avvio = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        moduli = {
            "Memoria": self.memoria,
            "Dispositivi": self.modulo_dispositivi,
            "Comandi": self.modulo_comandi,
            "Voce": self.modulo_voce,
        }

        for nome, modulo in moduli.items():
            self.manager.registra(nome, modulo)

        for nome in moduli:
            self.manager.avvia(nome)

        # Esito modulo voce: determina la modalità operativa.
        self.voce_disponibile = bool(
            getattr(self.modulo_voce, "ascolto_attivo", False)
        )

        if not self.voce_disponibile:
            self.logger.warning(
                "Modulo voce non attivo — "
                "Jarvis operativo in modalità solo-testo."
            )

        # Plugin (non bloccanti)
        try:
            self.plugin_manager.carica_plugin()
            self.plugin_manager.avvia_tutti()
        except Exception:
            pass

        self.stato = "Operativo"

        self.logger.info("Jarvis operativo.")

        return True

    def parla(self, testo):
        return self.modulo_voce.rispondi(testo)

    def esegui_comando(self, comando):

        risposta = self.modulo_comandi.esegui(comando)

        if risposta:
            self.parla(risposta)

        return risposta

    def stato_sistema(self):

        return {
            "nome": self.nome,
            "versione": self.versione,
            "stato": self.stato,
            "base": self.base,
            "avvio": self.avvio,
            "voce_disponibile": self.voce_disponibile,
            "memoria": self.memoria.stato(),
            "voce": self.modulo_voce.stato(),
            "comandi": self.modulo_comandi.stato(),
            "dispositivi": self.modulo_dispositivi.stato(),
            "plugin": self.plugin_manager.stato(),
            "moduli": self.manager.stato(),
            "personalita": self.personalita.stato_personalita(),
            "sicurezza": self.sicurezza.stato(),
            "sistema": self.stato_sistema_modulo.completo(),
        }

    def arresta(self):

        self.logger.info("Arresto Jarvis...")

        try:
            self.plugin_manager.ferma_tutti()
        except Exception:
            pass

        try:
            self.modulo_voce.ferma()
        except Exception:
            pass

        self.stato = "Spento"

        self.logger.info("Jarvis arrestato.")
