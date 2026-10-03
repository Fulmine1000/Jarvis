"""Componenti cognitivi e conversazionali di Jarvis.

Il pacchetto mantiene il CervelloJarvis esistente e rende disponibili anche
il motore conversazionale locale e la memoria conversazionale riutilizzabile
provenienti dal Voice Pack, adattati alla struttura reale della repository.
"""

from .cervello import CervelloJarvis
from .conversazione import ConversationEngine
from memoria.memory import Memory

__all__ = [
    "CervelloJarvis",
    "ConversationEngine",
    "Memory",
]
