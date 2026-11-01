from datetime import datetime
import os

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
from cybersecurity.modulo import CybersecurityJarvis
from core.aggiornamenti import AggiornamentiJarvis
from core.portabilita import GestorePortabilitaIA
from core.gateway_remoto import GatewayJarvis
from intelligenza.cervello import CervelloJarvis
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
        nome_utente = self.config.sezione("utente").get("nome")
        if nome_utente:
            self.preferenze.imposta("nome_utente", nome_utente)
        self.contesto = ContestoJarvis()
        self.personalita = PersonalitaJarvis()
        self.stato_sistema_modulo = StatoJarvis()
        self.sicurezza = SicurezzaJarvis()
        self.cybersecurity = CybersecurityJarvis(self.logger)
        self.aggiornamenti = AggiornamentiJarvis()
        self.capacita = CapacitaJarvis(self.logger)
        self.dialogo = DialogoJarvis(self.logger)
        self.intelligenza = CervelloJarvis(self)
        self.automazioni = AutomazioniJarvis(self.logger)
        self.pianificatore = PianificatoreJarvis(self.logger)
        self.visione = VisioneJarvis(self.logger)
        self.diagnostica = DiagnosticaJarvis(self)
        self.modulo_dispositivi = ModuloDispositivi(self)
        self.modulo_comandi = ModuloComandi(self)
        self.modulo_voce = ModuloVoce(self)
        self.portabilita_ia = GestorePortabilitaIA(self, self.logger)
        self.gateway_remoto = None
        self.trasferimento = None
        self.voce_disponibile = False
        self.notifiche_email_telegram = None

    def avvia(self):
        if self.stato == "Operativo":
            return True
        self.logger.info("Avvio Kernel Jarvis...")
        self.stato = "Avvio"
        self.arresto_richiesto = False
        self.avvio = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.intelligenza.avvia()
        self.automazioni.avvia()
        self.pianificatore.avvia()
        moduli = {"Memoria": self.memoria, "Dispositivi": self.modulo_dispositivi, "Comandi": self.modulo_comandi, "Voce": self.modulo_voce}
        for nome, modulo in moduli.items():
            self.manager.registra(nome, modulo)
        for nome in moduli:
            self.manager.avvia(nome)

        self.trasferimento = self.modulo_dispositivi.get_trasferimento()
        self.voce_disponibile = bool(getattr(self.modulo_voce, "ascolto_attivo", False))
        try:
            self.plugin_manager.carica_plugin()
            self.plugin_manager.avvia_tutti()
        except Exception as errore:
            self.logger.warning(f"Plugin non completamente disponibili: {errore}")

        # Le notifiche sono opt-in: i segreti arrivano solo dall'ambiente.
        # IMAP opera in sola lettura e Telegram riceve solo mittente/oggetto.
        if os.environ.get("JARVIS_NOTIFICHE_EMAIL_TELEGRAM") == "1":
            try:
                from moduli.notifiche_email_telegram import NotificheEmailTelegram
                self.notifiche_email_telegram = NotificheEmailTelegram(logger=self.logger)
                self.notifiche_email_telegram.avvia()
            except Exception as errore:
                self.notifiche_email_telegram = None
                self.logger.warning(f"Notifiche email/Telegram non avviate: {errore}")

        try:
            self.visione.rileva()
            self.diagnostica.esegui()
        except Exception as errore:
            self.logger.warning(f"Diagnostica non completata: {errore}")
        self.stato = "Operativo"
        if os.environ.get("JARVIS_GATEWAY_ENABLED") == "1":
            try:
                self.gateway_remoto = GatewayJarvis(self)
                self.gateway_remoto.avvia()
                self.logger.info("Gateway remoto autenticato avviato.")
            except Exception as errore:
                self.gateway_remoto = None
                self.logger.warning(f"Gateway remoto non avviato: {errore}")
        self.logger.info("Jarvis operativo.")
        return True

    def parla(self, testo):
        risposta = self.modulo_voce.rispondi(testo)
        if risposta:
            self.portabilita_ia.invia(risposta)
        return risposta

    def esegui_comando(self, comando):
        risposta = self.modulo_comandi.esegui(comando)
        if risposta:
            self.parla(risposta)
        return risposta

    def registra_host_ia(self, adapter):
        self.portabilita_ia.registra(adapter)
        return True

    def trasferisci_su_host_ia(self, device_id):
        return self.portabilita_ia.trasferisci(device_id)

    def richiedi_arresto(self):
        self.arresto_richiesto = True
        return True

    def stato_sistema(self):
        return {"nome": self.nome, "versione": self.versione, "stato": self.stato, "base": self.base, "avvio": self.avvio, "arresto_richiesto": self.arresto_richiesto, "voce_disponibile": self.voce_disponibile, "memoria": self.memoria.stato(), "voce": self.modulo_voce.stato(), "comandi": self.modulo_comandi.stato(), "dispositivi": self.modulo_dispositivi.stato(), "capacita": self.capacita.stato(), "dialogo_ai": self.dialogo.stato(), "intelligenza": self.intelligenza.stato(), "portabilita_ia": self.portabilita_ia.stato(), "trasferimento": self.trasferimento.stato() if self.trasferimento else {}, "automazioni": self.automazioni.stato(), "pianificatore": self.pianificatore.stato(), "visione": self.visione.stato(), "diagnostica": self.diagnostica.stato(), "plugin": self.plugin_manager.stato(), "moduli": self.manager.stato(), "personalita": self.personalita.stato_personalita(), "preferenze": self.preferenze.stato(), "sicurezza": self.sicurezza.stato(), "cybersecurity": self.cybersecurity.stato(), "notifiche_email_telegram": bool(self.notifiche_email_telegram), "gateway_remoto": self.gateway_remoto.stato() if self.gateway_remoto else {"attivo": False}, "sistema": self.stato_sistema_modulo.completo()}

    def arresta(self):
        if self.stato == "Spento":
            return True
        self.logger.info("Arresto Jarvis...")
        self.arresto_richiesto = True
        if self.notifiche_email_telegram:
            try:
                self.notifiche_email_telegram.ferma()
            except Exception as errore:
                self.logger.warning(f"Errore arresto notifiche email/Telegram: {errore}")
            self.notifiche_email_telegram = None
        self.intelligenza.ferma()
        try:
            self.dialogo.ferma()
        except Exception as errore:
            self.logger.warning(f"Errore arresto motore IA locale: {errore}")
        if self.gateway_remoto:
            self.gateway_remoto.ferma()
            self.gateway_remoto = None
        self.portabilita_ia.disattiva()
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
        self.trasferimento = None
        self.voce_disponibile = False
        self.stato = "Spento"
        self.logger.info("Jarvis arrestato.")
        return True
