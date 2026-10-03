"""
Configurazione globale di Jarvis.

Le impostazioni possono essere sovrascritte tramite variabili d'ambiente.
Il modulo è compatibile con la struttura reale della repository e non
richiede variabili d'ambiente obbligatorie.
"""

from __future__ import annotations

import os
from typing import Any, Dict

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


# Carica automaticamente il file .env quando python-dotenv è disponibile.
if load_dotenv is not None:
    load_dotenv()


def _env_bool(nome: str, default: bool) -> bool:
    """Legge un booleano dalle variabili d'ambiente in modo sicuro."""
    valore = os.getenv(nome)
    if valore is None:
        return default

    valore = valore.strip().lower()
    if valore in {"1", "true", "yes", "y", "on", "si", "s"}:
        return True
    if valore in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _env_int(nome: str, default: int, minimo: int = 1) -> int:
    """Legge un intero con fallback sicuro e limite minimo."""
    try:
        return max(minimo, int(os.getenv(nome, str(default))))
    except (TypeError, ValueError):
        return default


def _env_float(
    nome: str,
    default: float,
    minimo: float | None = None,
    massimo: float | None = None,
) -> float:
    """Legge un numero decimale con fallback e limiti opzionali."""
    try:
        valore = float(os.getenv(nome, str(default)))
    except (TypeError, ValueError):
        return default

    if minimo is not None:
        valore = max(minimo, valore)
    if massimo is not None:
        valore = min(massimo, valore)
    return valore


# Configurazione vocale.
VOICE_CONFIG: Dict[str, Any] = {
    "language": os.getenv("JARVIS_LANGUAGE", "it_IT").strip() or "it_IT",
    "speed": _env_float("JARVIS_VOICE_SPEED", 0.9, 0.5, 1.5),
    "pitch": _env_float("JARVIS_VOICE_PITCH", 0.8, 0.5, 1.5),
}


# Configurazione dell'intelligenza e della memoria conversazionale.
AI_CONFIG: Dict[str, Any] = {
    "enable_memory": _env_bool("JARVIS_MEMORY", True),
    "memory_size": _env_int("JARVIS_MEMORY_SIZE", 20, 1),
    "response_timeout": _env_int("JARVIS_TIMEOUT", 10, 1),
}


# Configurazione audio/STT.
AUDIO_CONFIG: Dict[str, Any] = {
    "sample_rate": _env_int("JARVIS_SAMPLE_RATE", 44100, 8000),
    "chunk_size": _env_int("JARVIS_CHUNK_SIZE", 1024, 1),
    "channels": _env_int("JARVIS_CHANNELS", 1, 1),
}


def get_config() -> Dict[str, Dict[str, Any]]:
    """Restituisce una copia completa della configurazione."""
    return {
        "voice": dict(VOICE_CONFIG),
        "ai": dict(AI_CONFIG),
        "audio": dict(AUDIO_CONFIG),
    }


__all__ = [
    "VOICE_CONFIG",
    "AI_CONFIG",
    "AUDIO_CONFIG",
    "get_config",
]
