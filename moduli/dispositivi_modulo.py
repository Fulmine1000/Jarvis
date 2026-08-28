from dispositivi.gestore import GestoreDispositivi
from dispositivi.computer import ComputerJarvis
from dispositivi.rete import Rete
from dispositivi.bluetooth import Bluetooth
from dispositivi.telefono import TelefonoJarvis
from dispositivi.connessione import ConnessioneDispositivi
from dispositivi.smart_home import SmartHomeJarvis
from dispositivi.tv_lg import LgWebOSTv
from dispositivi.trasferimento import TrasferimentoJarvis


class ModuloDispositivi:
    """Registra e coordina i dispositivi e il livello multi-dispositivo di Jarvis."""

    def __init__(self, kernel):
        self.kernel = kernel
        self.nome = "Dispositivi"
        self.attivo = False
        self.gestore = None
        self.connessione = None
        self.trasferimento = None

    def avvia(self):
        logger = self.kernel.logger
        self.connessione = ConnessioneDispositivi(logger)
        self.connessione.avvia()
        self.gestore = GestoreDispositivi(logger)
        self.gestore.collega_connessione(self.connessione)
        self.trasferimento = TrasferimentoJarvis(logger)

        for nome, dispositivo in (
            ("computer", ComputerJarvis()),
            ("rete", Rete()),
            ("bluetooth", Bluetooth()),
            ("smart_home", SmartHomeJarvis()),
        ):
            self.gestore.registra(nome, dispositivo)

        tv_cfg = self.kernel.config.sezione("tv_lg")
        tv = LgWebOSTv(
            name=tv_cfg.get("nome", "tv"),
            ip=tv_cfg.get("ip") or None,
            client_key=tv_cfg.get("client_key") or None,
            timeout=int(tv_cfg.get("timeout", 4)),
            logger=logger,
        )
        self.gestore.registra("tv", tv)

        motorola = TelefonoJarvis(
            nome="Motorola", modello="Motorola Base J.A.R.V.I.S.", base=True, logger=logger
        )
        self.gestore.registra("motorola", motorola)
        self.connessione.connetti("motorola")

        telefono = TelefonoJarvis(
            nome="Telefono", modello="Dispositivo Android", base=False, logger=logger
        )
        self.gestore.registra("telefono", telefono)
        # Il telefono non viene più considerato realmente collegato solo
        # perché Jarvis è stato avviato: lo stato fisico viene rilevato da ADB.

        self.trasferimento.avvia_monitor_usb()
        self.attivo = True
        logger.info("Modulo Dispositivi J.A.R.V.I.S. definitivo attivo.")
        return True

    def get_gestore(self):
        return self.gestore

    def get_connessione(self):
        return self.connessione

    def get_trasferimento(self):
        return self.trasferimento

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo" if self.attivo else "errore",
            "dispositivi": self.gestore.elenco() if self.gestore else [],
            "connessione": self.connessione.stato() if self.connessione else {},
            "trasferimento": self.trasferimento.stato() if self.trasferimento else {},
        }
