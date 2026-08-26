from datetime import datetime

from core.logger import LoggerJarvis
from core.event_bus import EventBus
from core.manager import ModuleManager
from core.config import ConfigJarvis
from core.capacita import CapacitaJarvis
from core.dialogo import DialogoJarvis
from core.automazioni import AutomazioniJarvis, PianificatoreJarvis
from core.visione import VisioneJarvis
from core.diagnostica import DiagnosticaJarvis
from core.stato import StatoJarvis
from core.sicurezza import SicurezzaJarvis
from core.aggiornamenti import AggiornamentiJarvis
from memoria.memoria import MemoriaJarvis
from memoria.preferenze import PreferenzeJarvis
from memoria.contesto import ContestoJarvis
from personalita.personalita import PersonalitaJarvis
from moduli.comandi_modulo import ModuloComandi
from moduli.dispositivi_modulo import ModuloDispositivi
from moduli.voce_modulo import ModuloVoce
from plugin.plugin_manager import PluginManager


class KernelJarvis:
    """Orchestratore centrale di J.A.R.V.I.S. nella versione definitiva."""

    def __init__(self):
        self.config = ConfigJarvis()
        dati = self.config.sezione("jarvis")
        self.nome = dati.get("nome", "J.A.R.V.I.S.")
        self.versione = "definitiva"
        self.base = self.config.sezione("base").get("dispositivo", "computer")
        self.stato = "Spento"
        self.avvio = None
        self.arresto_richiesto = False
        self.hud = None
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
        self.dialogo = DialogoJarvis(self.logger)
        self.automazioni = AutomazioniJarvis(self.logger)
        self.pianificatore = PianificatoreJarvis(self.logger)
        self.visione = VisioneJarvis(self.logger)
        self.diagnostica = DiagnosticaJarvis(self)
        self.modulo_dispositivi = ModuloDispositivi(self)
        self.modulo_comandi = ModuloComandi(self)
        self.modulo_voce = ModuloVoce(self)
        self.voce_disponibile = False

    def avvia(self):
        if self.stato == "Operativo":
            return True
        self.logger.info("Avvio Kernel Jarvis...")
        self.stato = "Avvio"
        self.arresto_richiesto = False
        self.avvio = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.automazioni.avvia()
        self.pianificatore.avvia()
        moduli = {"Memoria": self.memoria, "Dispositivi": self.modulo_dispositivi, "Comandi": self.modulo_comandi, "Voce": self.modulo_voce}
        for nome, modulo in moduli.items():
            self.manager.registra(nome, modulo)
        for nome in moduli:
            self.manager.avvia(nome)
        self.voce_disponibile = bool(getattr(self.modulo_voce, "ascolto_attivo", False))
        try:
            self.plugin_manager.carica_plugin()
            self.plugin_manager.avvia_tutti()
        except Exception as errore:
            self.logger.warning(f"Plugin non completamente disponibili: {errore}")
        try:
            self.visione.rileva()
            self.diagnostica.esegui()
        except Exception as errore:
            self.logger.warning(f"Diagnostica non completata: {errore}")
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

    def richiedi_arresto(self):
        self.arresto_richiesto = True
        return True

    def stato_sistema(self):
        return {"nome": self.nome, "versione": self.versione, "stato": self.stato, "base": self.base, "avvio": self.avvio, "arresto_richiesto": self.arresto_richiesto, "voce_disponibile": self.voce_disponibile, "memoria": self.memoria.stato(), "voce": self.modulo_voce.stato(), "comandi": self.modulo_comandi.stato(), "dispositivi": self.modulo_dispositivi.stato(), "capacita": self.capacita.stato(), "dialogo_ai": self.dialogo.stato(), "automazioni": self.automazioni.stato(), "pianificatore": self.pianificatore.stato(), "visione": self.visione.stato(), "diagnostica": self.diagnostica.stato(), "plugin": self.plugin_manager.stato(), "moduli": self.manager.stato(), "personalita": self.personalita.stato_personalita(), "preferenze": self.preferenze.stato(), "sicurezza": self.sicurezza.stato(), "sistema": self.stato_sistema_modulo.completo()}

    def arresta(self):
        if self.stato == "Spento":
            return True
        self.logger.info("Arresto Jarvis...")
        self.arresto_richiesto = True
        self.automazioni.ferma()
        self.pianificatore.ferma()
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
