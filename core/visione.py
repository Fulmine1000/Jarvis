from __future__ import annotations

import base64
import json
import os
import platform
import subprocess
import urllib.error
import urllib.parse
import urllib.request


class VisioneJarvis:
    """Visione opzionale e locale: diagnostica webcam e analisi immagini via Ollama.

    Le immagini non vengono inviate a servizi remoti: l'endpoint è limitato
    a localhost. Il modello deve supportare immagini ed essere già installato.
    """

    ESTENSIONI_IMMAGINE = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    LIMITE_IMMAGINE = 10 * 1024 * 1024

    def __init__(self, logger=None):
        self.logger = logger
        self.attivo = False
        self.camera_disponibile = False
        self.motore = None
        self.ultimo_errore = None

    def rileva(self):
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["system_profiler", "SPCameraDataType"],
                    capture_output=True, text=True, timeout=5,
                )
                self.camera_disponibile = result.returncode == 0 and bool(result.stdout.strip())
            elif platform.system() == "Linux":
                self.camera_disponibile = any(os.path.exists(f"/dev/video{i}") for i in range(5))
            elif platform.system() == "Windows":
                # Evita di aprire la webcam automaticamente all'avvio.
                self.camera_disponibile = False
            else:
                self.camera_disponibile = False
        except Exception:
            self.camera_disponibile = False
        self.attivo = True
        return self.camera_disponibile

    @staticmethod
    def _endpoint_locale():
        raw = os.environ.get("JARVIS_OLLAMA_URL", "http://127.0.0.1:11434").strip()
        parsed = urllib.parse.urlparse(raw)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "http" or host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Per privacy, la visione accetta solo Ollama locale su localhost.")
        return raw.rstrip("/") + "/api/chat"

    def analizza_immagine(self, percorso, domanda=None):
        path = os.path.abspath(os.path.expanduser(str(percorso or "").strip().strip('"').strip("'")))
        if not os.path.isfile(path):
            return {"ok": False, "errore": "Immagine non trovata: " + path}
        if os.path.splitext(path)[1].lower() not in self.ESTENSIONI_IMMAGINE:
            return {"ok": False, "errore": "Formato non supportato. Usa PNG, JPG, JPEG, WEBP o BMP."}
        try:
            size = os.path.getsize(path)
            if size <= 0 or size > self.LIMITE_IMMAGINE:
                return {"ok": False, "errore": "L'immagine deve essere non vuota e inferiore a 10 MB."}
            with open(path, "rb") as file:
                image = base64.b64encode(file.read()).decode("ascii")
            endpoint = self._endpoint_locale()
            model = os.environ.get("JARVIS_VISION_MODEL", "moondream").strip() or "moondream"
            prompt = str(domanda or "Descrivi in italiano gli oggetti chiaramente visibili. Distingui ciò che osservi dalle ipotesi e non inventare dettagli.").strip()
            payload = {
                "model": model,
                "stream": False,
                "messages": [{"role": "user", "content": prompt, "images": [image]}],
                "options": {"temperature": 0.1},
            }
            request = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
            answer = str(result.get("message", {}).get("content", "")).strip()
            if not answer:
                return {"ok": False, "errore": "Il modello locale non ha restituito una descrizione."}
            self.motore = "Ollama locale: " + model
            self.ultimo_errore = None
            return {"ok": True, "risposta": answer, "motore": self.motore, "percorso": path}
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:300]
            message = f"Ollama ha risposto HTTP {error.code}: {detail}"
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as error:
            message = str(error)
        except Exception as error:
            message = f"Errore analisi immagine: {error}"
        self.ultimo_errore = message
        if self.logger:
            try:
                self.logger.warning("Visione immagine non disponibile: " + message)
            except Exception:
                pass
        return {"ok": False, "errore": message}

    def stato(self):
        return {
            "attivo": self.attivo,
            "camera_disponibile": self.camera_disponibile,
            "motore": self.motore,
            "ultimo_errore": self.ultimo_errore,
            "modello_configurato": os.environ.get("JARVIS_VISION_MODEL", "moondream"),
            "privacy": "analisi immagine solo su Ollama localhost; nessun upload remoto",
        }
