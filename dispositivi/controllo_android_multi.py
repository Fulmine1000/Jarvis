"""Controllo multi-dispositivo Android via ADB, senza aggirare blocchi.

Consente di risvegliare lo schermo e aprire URL/app su tutti i dispositivi
ADB già autorizzati. Non rimuove PIN/biometria e non esegue chiamate.
"""
from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
from urllib.parse import urlparse


APP_PACKAGES = {
    "youtube": "com.google.android.youtube",
    "spotify": "com.spotify.music",
    "chrome": "com.android.chrome",
    "whatsapp": "com.whatsapp",
    "telegram": "org.telegram.messenger",
}


class ControlloAndroidMulti:
    """Esegue azioni esplicite su tutti i telefoni ADB autorizzati."""

    def __init__(self, logger=None, timeout: float = 8.0, adb: str | None = None):
        self.logger = logger
        self.timeout = max(2.0, float(timeout))
        self.adb = adb or shutil.which("adb")

    def _run(self, args: list[str]):
        if not self.adb:
            return None, "ADB non trovato. Installa Android Platform Tools e verifica il PATH."
        try:
            result = subprocess.run(
                [self.adb, *args], capture_output=True, text=True,
                timeout=self.timeout, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return None, f"Comunicazione ADB non riuscita: {exc}"
        if result.returncode:
            return None, (result.stderr or result.stdout).strip() or "Comando ADB non riuscito."
        return result.stdout.strip(), None

    def dispositivi(self):
        """Restituisce soltanto seriali con stato ADB 'device' (autorizzati)."""
        output, error = self._run(["devices"])
        if error:
            return [], error
        seriali = []
        for line in output.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                seriali.append(parts[0])
        return seriali, None if seriali else "Nessun telefono Android autorizzato via ADB."

    def _per_tutti(self, azione):
        seriali, error = self.dispositivi()
        if error:
            return error
        risultati = []
        for serial in seriali:
            _, errore = azione(serial)
            risultati.append((serial, errore))
        riusciti = [serial for serial, errore in risultati if errore is None]
        falliti = [f"{serial}: {errore}" for serial, errore in risultati if errore]
        testo = f"Azione completata su {len(riusciti)}/{len(seriali)} dispositivi."
        if falliti:
            testo += " Errori: " + "; ".join(falliti)
        if self.logger:
            try:
                self.logger.info(testo)
            except Exception:
                pass
        return testo

    def risveglia_tutti(self):
        """Accende gli schermi; l'autenticazione resta sempre manuale."""
        result = self._per_tutti(
            lambda serial: self._run(["-s", serial, "shell", "input", "keyevent", "224"])
        )
        return result + " PIN, password o biometria non vengono aggirati."

    @staticmethod
    def _url_valido(url: str) -> bool:
        try:
            parsed = urlparse(url.strip())
            return parsed.scheme in ("http", "https") and bool(parsed.netloc)
        except Exception:
            return False

    def apri_url_su_tutti(self, url: str):
        url = str(url or "").strip()
        if not self._url_valido(url):
            return "URL non valido: usa un indirizzo completo http:// o https://."
        return self._per_tutti(
            lambda serial: self._run([
                "-s", serial, "shell", "am", "start",
                "-a", "android.intent.action.VIEW", "-d", shlex.quote(url),
            ])
        )

    def apri_app_su_tutti(self, nome: str):
        nome = str(nome or "").strip().lower()
        pacchetto = APP_PACKAGES.get(nome)
        if not pacchetto:
            return "App non supportata per il controllo multi-telefono. Usa YouTube, Spotify, Chrome, WhatsApp o Telegram."
        return self._per_tutti(
            lambda serial: self._run([
                "-s", serial, "shell", "monkey", "-p", pacchetto, "1",
            ])
        )

    def gestisci_comando(self, comando: str):
        testo = re.sub(r"\\s+", " ", str(comando or "").strip().lower())
        testo = re.sub(r"^(?:hey jarvis|ehi jarvis|jarvis)[, ]+", "", testo)
        if re.fullmatch(r"(?:accendi|risveglia) (?:gli schermi|tutti i telefoni|tutti i dispositivi)(?: android)?", testo):
            return self.risveglia_tutti()
        match = re.fullmatch(r"(?:apri|avvia|lancia) (youtube|spotify|chrome|whatsapp|telegram) su tutti i telefoni", testo)
        if match:
            return self.apri_app_su_tutti(match.group(1))
        match = re.fullmatch(r"(?:apri|riproduci) (https?://\\S+) su tutti i telefoni", testo)
        if match:
            return self.apri_url_su_tutti(match.group(1))
        if re.fullmatch(r"(?:riproduci|avvia) (?:la mia )?(?:canzone|musica) preferita su tutti i telefoni", testo):
            url = os.environ.get("JARVIS_MEDIA_PREFERITA_URL", "").strip()
            if not url:
                return "Configura JARVIS_MEDIA_PREFERITA_URL con il link della musica preferita prima di usarlo."
            return self.apri_url_su_tutti(url)
        return None


__all__ = ["ControlloAndroidMulti"]
