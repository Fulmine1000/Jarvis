from datetime import datetime

from core.logger import LoggerJarvis
from core.event_bus import EventBus
from core.manager import ModuleManager
from core.config import ConfigJarvis
from core.capacita import CapacitaJarvis

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
    """Orchestratore centrale e definitivo di J.A.R.V.I.S."""

    def __init__(self):
        self.config = ConfigJarvis()
        dati = self.config.sezione("jarvis")
        self.nome = dati.get("nome", "J.A.R.V.I.S.")
        self.versione = dati.get("versione", "definitiva")
        self.base = self.config.sezione("base").get("dispositivo", "computer")
        self.stato = "Spento"
        self.avvio = None
        self.logger = LoggerJarvis()
        self.event_bus = EventBus()
        self.manager = ModuleManager(self.logger)
        self.plugin_manager = PluginManager(self)
        self.memoria = MemoriaJarvis(self.logger)
        self.preferenze = PreferenzeJarvis()
        self.contesto = ContestoJarvis()
        self.personalita = PersonalitaJarvis()
        self.stato_sistema_modulo = StatoJarvis()
        self.sicurezza = SicurezzaJarvis()
        self.aggiornamenti = AggiornamentiJarvis()
        self.capacita = CapacitaJarvis(self.logger)
        self.modulo_dispositivi = ModuloDispositivi(self)
        self.modulo_comandi = ModuloComandi(self)
        self.modulo_voce = ModuloVoce(self)
        self.voce_disponibile = False

    def avvia(self):
        if self.stato == "Operativo":
            return True
        self.logger.info("Avvio Kernel Jarvis...")
        self.stato = "Avvio"
        self.avvio = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        moduli = {"Memoria": self.memoria, "Dispositivi": self.modulo_dispositivi,
                  "Comandi": self.modulo_comandi, "Voce": self.modulo_voce}
        for nome, modulo in moduli.items():
            self.manager.registra(nome, modulo)
        for nome in moduli:
            try:
                self.manager.avvia(nome)
            except Exception as errore:
                self.logger.warning(f"Modulo {nome} non avviato: {errore}")
        self.voce_disponibile = bool(getattr(self.modulo_voce, "ascolto_attivo", False))
        try:
            self.plugin_manager.carica_plugin()
            self.plugin_manager.avvia_tutti()
        except Exception as errore:
            self.logger.warning(f"Plugin non completamente disponibili: {errore}")
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
            "nome": self.nome, "versione": self.versione, "stato": self.stato,
            "base": self.base, "avvio": self.avvio,
            "voce_disponibile": self.voce_disponibile,
            "memoria": self.memoria.stato(), "voce": self.modulo_voce.stato(),
            "comandi": self.modulo_comandi.stato(),
            "dispositivi": self.modulo_dispositivi.stato(),
            "capacita": self.capacita.stato(), "plugin": self.plugin_manager.stato(),
            "moduli": self.manager.stato(), "personalita": self.personalita.stato_personalita(),
            "sicurezza": self.sicurezza.stato(), "sistema": self.stato_sistema_modulo.completo(),
        }

    def arresta(self):
        if self.stato == "Spento":
            return True
        self.logger.info("Arresto Jarvis...")
        try:
            self.plugin_manager.ferma_tutti()
        except Exception as errore:
            self.logger.warning(f"Errore arresto plugin: {errore}")
        try:
            self.manager.ferma_tutti()
        except Exception as errore:
            self.logger.warning(f"Errore arresto moduli: {errore}")
        self.voce_disponibile = False
        self.stato = "Spento"
        self.logger.info("Jarvis arrestato.")
        return True
