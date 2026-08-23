from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import sys
from datetime import datetime


class DiagnosticaJarvis:
    """Controllo salute del sistema Jarvis e delle integrazioni opzionali."""

    def __init__(self, kernel=None):
        self.kernel = kernel
        self.avviata = False
        self.ultima = None
        self.risultato = {}

    def esegui(self):
        controlli = {
            "python": sys.version.split()[0],
            "sistema": platform.platform(),
            "cartella_progetto": os.path.isdir(os.getcwd()),
            "browser": bool(shutil.which("open") or shutil.which("xdg-open") or platform.system() == "Windows"),
            "vosk": bool(importlib.util.find_spec("vosk")),
            "sounddevice": bool(importlib.util.find_spec("sounddevice")),
            "psutil": bool(importlib.util.find_spec("psutil")),
            "websocket": bool(importlib.util.find_spec("websocket")),
            "piper": bool(shutil.which("piper")),
            "ollama": bool(shutil.which("ollama")),
        }
        self.risultato = controlli
        self.ultima = datetime.now().isoformat(timespec="seconds")
        self.avviata = True
        return controlli

    def riepilogo(self):
        dati = self.esegui()
        disponibili = [nome for nome, valore in dati.items() if valore is True]
        return f"Diagnostica completata. Integrazioni disponibili: {', '.join(disponibili) or 'nessuna'}."

    def stato(self):
        return {"attiva": self.avviata, "ultima": self.ultima, "controlli": self.risultato}
