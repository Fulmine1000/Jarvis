"""Nucleo pubblico di Jarvis.

Il pacchetto espone la facciata JARVIS adattata dal Voice Pack italiano alla
struttura reale della repository. L'orchestrazione effettiva continua a
risiedere in KernelJarvis, utilizzato internamente da core.core.JARVIS.
"""

from .core import JARVIS

__all__ = ["JARVIS"]
