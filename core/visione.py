from __future__ import annotations

import os
import platform
import subprocess


class VisioneJarvis:
    """Ponte opzionale per capacità visive locali.

    Non inventa risultati: se non è disponibile una camera o un motore di
    visione, espone lo stato e lascia Jarvis operativo in modalità normale.
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.attivo = False
        self.camera_disponibile = False
        self.motore = None

    def rileva(self):
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(["system_profiler", "SPCameraDataType"], capture_output=True, text=True, timeout=5)
                self.camera_disponibile = result.returncode == 0 and bool(result.stdout.strip())
            elif platform.system() == "Linux":
                self.camera_disponibile = any(os.path.exists(f"/dev/video{i}") for i in range(5))
            else:
                self.camera_disponibile = False
        except Exception:
            self.camera_disponibile = False
        self.attivo = True
        return self.camera_disponibile

    def analizza_immagine(self, percorso):
        if not os.path.isfile(os.path.expanduser(percorso)):
            return {"ok": False, "errore": "immagine_non_trovata"}
        return {
            "ok": False,
            "errore": "motore_visione_non_configurato",
            "percorso": os.path.abspath(os.path.expanduser(percorso)),
        }

    def stato(self):
        return {
            "attivo": self.attivo,
            "camera_disponibile": self.camera_disponibile,
            "motore": self.motore,
        }
