"""Controllo esplicito di un telefono Android collegato via ADB.

Le operazioni sono volutamente limitate: risveglia lo schermo senza aggirare
PIN/biometria, apre app installate e apre il dialer/contatti senza avviare
chiamate in modo silenzioso. Non raccoglie né salva dati personali.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from typing import Optional


ALIAS_APP = {
    "youtube": ("com.google.android.youtube",),
    "whatsapp": ("com.whatsapp",),
    "chrome": ("com.android.chrome",),
    "google chrome": ("com.android.chrome",),
    "spotify": ("com.spotify.music",),
    "netflix": ("com.netflix.mediaclient",),
    "instagram": ("com.instagram.android",),
    "telegram": ("org.telegram.messenger",),
    "hotstar": ("in.startv.hotstar", "com.jio.hotstar"),
    "jiohotstar": ("in.startv.hotstar", "com.jio.hotstar"),
    "jio hotstar": ("in.startv.hotstar", "com.jio.hotstar"),
    "impostazioni": ("com.android.settings",),
    "fotocamera": ("com.android.camera2", "com.google.android.GoogleCamera"),
    "telefono": ("com.google.android.dialer", "com.android.dialer"),
    "contatti": ("com.google.android.contacts", "com.android.contacts"),
}


class ControlloAndroidVideo:
    """Esegue comandi ADB su un solo dispositivo Android autorizzato."""

    def __init__(self, logger=None, timeout: float = 8.0):
        self.logger = logger
        self.timeout = max(2.0, float(timeout))
        self.adb = shutil.which("adb")

    def _log(self, message: str) -> None:
        try:
            if self.logger:
                self.logger.info(message)
        except Exception:
            pass

    def _esegui(self, args: list[str], timeout: Optional[float] = None):
        if not self.adb:
            return None, "ADB non trovato. Installa Android Platform Tools e verifica il PATH."
        try:
            result = subprocess.run(
                [self.adb] + args,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return None, "Comunicazione ADB non riuscita: " + str(exc)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            return None, detail or "Il comando ADB è fallito."
        return result.stdout.strip(), None

    def _dispositivo(self):
        output, error = self._esegui(["devices"])
        if error:
            return None, error
        devices = []
        for line in output.splitlines()[1:]:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
        if not devices:
            return None, "Nessun telefono Android autorizzato. Collega il telefono via USB e accetta il debug USB."
        if len(devices) > 1:
            return None, "Sono collegati più dispositivi Android: lascia collegato solo il telefono da controllare."
        return devices[0], None

    def _shell(self, serial: str, *args: str):
        return self._esegui(["-s", serial, "shell", *args])

    def risveglia_schermo(self) -> str:
        serial, error = self._dispositivo()
        if error:
            return error
        _, error = self._shell(serial, "input", "keyevent", "224")
        if error:
            return "Non sono riuscito ad accendere lo schermo: " + error
        self._log("Schermo Android risvegliato tramite ADB.")
        return "Schermo del telefono acceso. Per motivi di sicurezza, PIN, password o biometria devono essere inseriti manualmente."

    def apri_app(self, nome: str) -> str:
        nome = str(nome or "").strip().lower()
        if not nome:
            return "Dimmi quale applicazione vuoi aprire sul telefono."
        serial, error = self._dispositivo()
        if error:
            return error
        packages, error = self._shell(serial, "pm", "list", "packages")
        if error:
            return "Non riesco a leggere le app installate: " + error
        installati = {line.strip().removeprefix("package:") for line in packages.splitlines() if line.strip().startswith("package:")}
        candidati = list(ALIAS_APP.get(nome, ()))
        if not candidati:
            normalizzato = re.sub(r"[^a-z0-9]", "", nome)
            candidati = [p for p in sorted(installati) if normalizzato and normalizzato in re.sub(r"[^a-z0-9]", "", p)]
        pacchetto = next((p for p in candidati if p in installati), None)
        if not pacchetto:
            return "Non ho trovato un'app installata corrispondente a '" + nome + "'. Controlla il nome dell'app sul telefono."
        _, error = self._shell(serial, "monkey", "-p", pacchetto, "1")
        if error:
            return "Apertura dell'app non riuscita: " + error
        self._log("App Android aperta: " + pacchetto)
        return "Ho aperto " + nome + " sul telefono."

    def chiama(self, destinazione: str) -> str:
        destinazione = str(destinazione or "").strip()
        if not destinazione:
            return "Dimmi il numero o il nome del contatto da chiamare."
        serial, error = self._dispositivo()
        if error:
            return error
        if re.fullmatch(r"[+0-9*#() .-]{3,32}", destinazione):
            numero = re.sub(r"[^+0-9*#]", "", destinazione)
            _, error = self._shell(serial, "am", "start", "-a", "android.intent.action.DIAL", "-d", "tel:" + numero)
            if error:
                return "Non sono riuscito ad aprire il dialer: " + error
            return "Ho preparato il numero nel dialer del telefono. Controllalo e premi tu il pulsante di chiamata."
        packages, error = self._shell(serial, "pm", "list", "packages")
        if error:
            return "Non riesco a verificare l'app Contatti: " + error
        installati = {line.strip().removeprefix("package:") for line in packages.splitlines() if line.strip().startswith("package:")}
        contatti = next((p for p in ("com.google.android.contacts", "com.android.contacts") if p in installati), None)
        if not contatti:
            return "Non ho trovato l'app Contatti sul telefono. Apri l'app Telefono manualmente per scegliere il contatto."
        _, error = self._shell(serial, "monkey", "-p", contatti, "1")
        if error:
            return "Non sono riuscito ad aprire Contatti: " + error
        return "Ho aperto Contatti sul telefono. Cerca '" + destinazione + "' e conferma tu la chiamata."

    def gestisci_comando(self, comando: str):
        """Restituisce una risposta se il testo è un comando telefonico noto, altrimenti None."""
        testo = re.sub(r"\s+", " ", str(comando or "").strip().lower())
        testo = re.sub(r"^(?:hey jarvis|ehi jarvis|jarvis)[, ]+", "", testo)
        if re.fullmatch(r"(?:sblocca|accendi|sveglia) (?:il )?(?:mio )?telefono|(?:accendi|risveglia) lo schermo (?:del )?(?:mio )?telefono|unlock my phone|wake (?:up )?my phone", testo):
            return self.risveglia_schermo()
        match = re.fullmatch(r"(?:apri|avvia|lancia) (?:l['’]app(?:licazione)? )?(.+?) (?:sul|nel|sopra il) (?:mio )?telefono", testo)
        if not match:
            match = re.fullmatch(r"(?:open|launch) (?:the app )?(.+?) (?:in|on) my phone", testo)
        if match:
            return self.apri_app(match.group(1).strip())
        match = re.fullmatch(r"(?:chiama|telefona a) (.+?)(?: dal| sul) (?:mio )?telefono", testo)
        if not match:
            match = re.fullmatch(r"(?:call|phone) (.+?)(?: on| from) my phone", testo)
        if not match:
            match = re.fullmatch(r"(?:chiama|telefona a|call|phone) (.+)", testo)
        if match:
            return self.chiama(match.group(1).strip())
        return None


__all__ = ["ControlloAndroidVideo"]
