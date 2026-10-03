"""
Pacchetto voce di Jarvis.

Espone sia i componenti vocali già presenti nella repository sia i nuovi
motori STT/TTS riutilizzabili del Voice Pack italiano.
"""

from .ascoltatore import AscoltatoreVoce
from .riconoscimento import RiconoscitoreVoce
from .sintesi import SintesiVocale
from .assistente_voce import AssistenteVoce
from .stt import SpeechToText
from .tts import TextToSpeech

__all__ = [
    "AscoltatoreVoce",
    "RiconoscitoreVoce",
    "SintesiVocale",
    "AssistenteVoce",
    "SpeechToText",
    "TextToSpeech",
]
