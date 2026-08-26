"""Adapter generico per robot dotati di intelligenza artificiale."""

from __future__ import annotations

from core.portabilita import AdapterDispositivoIA, ProfiloDispositivoIA


class RobotIA(AdapterDispositivoIA):
    """Base pronta per integrare un robot reale tramite il suo SDK/API.

    Non tenta di controllare direttamente hardware sconosciuto: le operazioni
    specifiche del robot vengono implementate in una sottoclasse o plugin.
    """

    def __init__(self, nome="Robot IA", modello="Generico", device_id="robot-ia", logger=None):
        profilo = ProfiloDispositivoIA(
            id=device_id,
            nome=nome,
            tipo="robot_ia",
            modello=modello,
            capacita=["voce", "risposta_ia", "identita_jarvis"],
        )
        super().__init__(profilo, logger)

    def invia_risposta(self, testo: str) -> str:
        # Punto di estensione per TTS, display o API del robot.
        return testo
