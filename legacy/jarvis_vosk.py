"""Listener Vosk compatibile con il sistema vocale di Jarvis.

Modulo storico: il modulo voce ufficiale gestisce il normale ciclo di ascolto.
"""

import json

try:
    import sounddevice as sd
except (ImportError, OSError):
    sd = None

try:
    from vosk import Model, KaldiRecognizer
except (ImportError, OSError):
    Model = None
    KaldiRecognizer = None

MODEL_PATH = "vosk-model-small-it-0.22"


def crea_riconoscitore(model_path=MODEL_PATH):
    if Model is None or KaldiRecognizer is None:
        return None
    try:
        return KaldiRecognizer(Model(model_path), 16000)
    except (OSError, ValueError, RuntimeError):
        return None


def ascolta(rec=None, timeout=None):
    if sd is None:
        return None
    recognizer = rec or crea_riconoscitore()
    if recognizer is None:
        return None
    try:
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1) as stream:
            while True:
                dati, _ = stream.read(4000)
                if recognizer.AcceptWaveform(bytes(dati)):
                    risultato = json.loads(recognizer.Result())
                    testo = risultato.get("text", "").strip()
                    if testo:
                        return testo
    except (OSError, RuntimeError, ValueError):
        return None
