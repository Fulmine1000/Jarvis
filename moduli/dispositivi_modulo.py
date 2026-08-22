from dispositivi.gestore import GestoreDispositivi
from dispositivi.computer import ComputerJarvis
from dispositivi.rete import Rete
from dispositivi.bluetooth import Bluetooth
from dispositivi.telefono import TelefonoJarvis
from dispositivi.connessione import ConnessioneDispositivi
from dispositivi.smart_home import SmartHomeJarvis
from dispositivi.tv_lg import LgWebOSTv


class ModuloDispositivi:
    """Registra e coordina tutti i dispositivi conosciuti da Jarvis."""

    def __init__(self, kernel):
        self.kernel = kernel
        self.nome = "Dispositivi"
        self.attivo = False
        self.gestore = None
        self.connessione = None

    def avvia(self):
        logger = self.kernel.logger
        self.connessione = ConnessioneDispositivi(logger)
        self.connessione.avvia()
        self.gestore = GestoreDispositivi(logger)
        self.gestore.collega_connessione(self.connessione)

        for nome, dispositivo in (
            ("computer", ComputerJarvis()),
            ("rete", Rete()),
            ("bluetooth", Bluetooth()),
            ("smart_home", SmartHomeJarvis()),
        ):
            self.gestore.registra(nome, dispositivo)

        # TV LG webOS: integrazione reale solo se configurata; mai bloccare Jarvis.
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
        self.connessione.connetti("telefono")

        self.attivo = True
        logger.info("Modulo Dispositivi J.A.R.V.I.S. 3.1 attivo.")
        return True

    def get_gestore(self):
        return self.gestore

    def get_connessione(self):
        return self.connessione

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo" if self.attivo else "errore",
            "dispositivi": self.gestore.elenco() if self.gestore else [],
            "connessione": self.connessione.stato() if self.connessione else {},
        }
