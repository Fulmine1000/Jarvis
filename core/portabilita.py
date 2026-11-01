"""Portabilità del cervello di J.A.R.V.I.S.

Questo modulo separa l'intelligenza centrale dal dispositivo che la ospita.
Un dispositivo esterno può collegarsi a Jarvis tramite un adapter senza dover
replicare memoria, personalità e logica del kernel.

Gli adapter sono volutamente generici: un robot diventa compatibile quando
fornisce un adapter concreto per il proprio SDK/API. Nessun produttore o
modello specifico viene assunto come compatibile automaticamente.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ProfiloDispositivoIA:
    """Descrive un dispositivo capace di ospitare/interfacciarsi con Jarvis."""

    id: str
    nome: str
    tipo: str = "dispositivo_ia"
    modello: str = "generico"
    versione_adapter: str = "1.0"
    capacita: list[str] = field(default_factory=list)
    online: bool = False
    jarvis_attivo: bool = False
    ultimo_contatto: str | None = None

    def serializza(self) -> dict[str, Any]:
        return asdict(self)


class AdapterDispositivoIA:
    """Interfaccia base per robot e altri dispositivi IA esterni."""

    def __init__(self, profilo: ProfiloDispositivoIA, logger=None):
        self.profilo = profilo
        self.logger = logger
        self.kernel = None

    def collega_kernel(self, kernel) -> None:
        self.kernel = kernel

    def connetti(self) -> bool:
        self.profilo.online = True
        self.profilo.ultimo_contatto = datetime.now().isoformat(timespec="seconds")
        return True

    def disconnetti(self) -> bool:
        self.profilo.online = False
        self.profilo.jarvis_attivo = False
        return True

    def trasferisci_identita(self) -> dict[str, Any]:
        """Invia solo identità non sensibile; la memoria resta nel Core."""
        if not self.kernel:
            raise RuntimeError("Adapter non collegato al Kernel Jarvis")
        return {
            "nome": self.kernel.nome,
            "versione": self.kernel.versione,
            "profilo": self.kernel.personalita.stato_personalita(),
            "lingua": "it-IT",
            "modalita": "core_remoto",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def attiva_jarvis(self) -> bool:
        if not self.profilo.online:
            return False
        self.profilo.jarvis_attivo = True
        self.profilo.ultimo_contatto = datetime.now().isoformat(timespec="seconds")
        return True

    def disattiva_jarvis(self) -> bool:
        self.profilo.jarvis_attivo = False
        return True

    def invia_risposta(self, testo: str) -> str:
        """Hook per altoparlante/display/voce del dispositivo."""
        return testo

    def stato(self) -> dict[str, Any]:
        return self.profilo.serializza()


class GestorePortabilitaIA:
    """Registro centrale degli host IA collegabili a J.A.R.V.I.S."""

    def __init__(self, kernel, logger=None):
        self.kernel = kernel
        self.logger = logger
        self.adapter: dict[str, AdapterDispositivoIA] = {}
        self.host_attivo: str | None = None

    def registra(self, adapter: AdapterDispositivoIA) -> None:
        adapter.collega_kernel(self.kernel)
        self.adapter[adapter.profilo.id] = adapter
        if self.logger:
            self.logger.info(
                f"Host IA registrato: {adapter.profilo.nome} ({adapter.profilo.tipo})"
            )

    def rimuovi(self, device_id: str) -> bool:
        adapter = self.adapter.get(device_id)
        if adapter is None:
            return False
        if self.host_attivo == device_id:
            adapter.disattiva_jarvis()
            self.host_attivo = None
        self.adapter.pop(device_id, None)
        return True

    def connetti(self, device_id: str) -> bool:
        adapter = self.adapter.get(device_id)
        return bool(adapter and adapter.connetti())

    def attiva(self, device_id: str) -> bool:
        adapter = self.adapter.get(device_id)
        if adapter is None or not adapter.attiva_jarvis():
            return False
        precedente = self.host_attivo
        if precedente and precedente != device_id:
            vecchio = self.adapter.get(precedente)
            if vecchio:
                vecchio.disattiva_jarvis()
        self.host_attivo = device_id
        return True

    def disattiva(self, device_id: str | None = None) -> bool:
        device_id = device_id or self.host_attivo
        if not device_id:
            return False
        adapter = self.adapter.get(device_id)
        if not adapter:
            return False
        adapter.disattiva_jarvis()
        if self.host_attivo == device_id:
            self.host_attivo = None
        return True

    def trasferisci(self, device_id: str) -> dict[str, Any]:
        adapter = self.adapter.get(device_id)
        if not adapter:
            raise KeyError(f"Host IA non trovato: {device_id}")
        if not adapter.profilo.online:
            raise RuntimeError("Host IA non connesso")

        # Preparazione prima del cambio: se il nuovo host non accetta l'attivazione,
        # il terminale precedente resta attivo.
        identita = adapter.trasferisci_identita()
        if not adapter.attiva_jarvis():
            raise RuntimeError("Il nuovo host non ha accettato l'attivazione")

        precedente = self.host_attivo
        if precedente and precedente != device_id:
            vecchio = self.adapter.get(precedente)
            if vecchio:
                vecchio.disattiva_jarvis()
        self.host_attivo = device_id
        return identita

    def invia(self, testo: str) -> str:
        if not self.host_attivo:
            return testo
        adapter = self.adapter.get(self.host_attivo)
        if not adapter:
            self.host_attivo = None
            return testo
        return adapter.invia_risposta(testo)

    def stato(self) -> dict[str, Any]:
        return {
            "nome": "Portabilità IA",
            "stato": "attivo",
            "host_attivo": self.host_attivo,
            "host_registrati": list(self.adapter),
            "dispositivi": {
                key: value.stato() for key, value in self.adapter.items()
            },
        }
