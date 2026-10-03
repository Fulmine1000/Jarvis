"""Modulo di configurazione globale di Jarvis.

Espone le configurazioni vocali, AI e audio definite in settings.py.
"""

from .settings import AI_CONFIG, AUDIO_CONFIG, VOICE_CONFIG, get_config

__all__ = [
    "VOICE_CONFIG",
    "AI_CONFIG",
    "AUDIO_CONFIG",
    "get_config",
]
