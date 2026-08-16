import os
import platform
import shutil
import subprocess


class SintesiVocale:
    """
    Sistema di sintesi vocale di Jarvis.

    Su macOS utilizza il comando nativo 'say'.
    Supporta inoltre Piper ed espeak come fallback.

    La sintesi è indipendente dal microfono e da Vosk.
    """

    def __init__(self, modulo_voce=None):
        self.modulo_voce = modulo_voce

        self.attiva = True
        self.disponibile = False
        self.attivo = False

        self.sistema = platform.system().lower()

        self.piper = shutil.which("piper")
        self.say = shutil.which("say")
        self.espeak = shutil.which("espeak")
        self.afplay = shutil.which("afplay")

        self._rileva_disponibilita()

    def _rileva_disponibilita(self):
        """Controlla se esiste almeno un sistema TTS utilizzabile."""

        if self.sistema == "darwin" and self.say:
            self.disponibile = True
            return

        if self.piper and self.afplay:
            self.disponibile = True
            return

        if self.espeak:
            self.disponibile = True
            return

        self.disponibile = False

    def avvia(self):
        """Avvia la sintesi vocale."""

        self._rileva_disponibilita()

        self.attiva = True
        self.attivo = self.disponibile

        if self.attivo:
            self._log("Sintesi vocale disponibile.")

        else:
            self._log(
                "Sintesi vocale non disponibile."
            )

        return self.attivo

    def parla(self, testo):
        """
        Pronuncia il testo una sola volta.
        """

        if not self.attiva:
            return False

        if not self.disponibile:
            return False

        if testo is None:
            return False

        testo = str(testo).strip()

        if not testo:
            return False

        # =========================================================
        # macOS
        # =========================================================

        if self.sistema == "darwin":

            comando_say = (
                self.say
                or shutil.which("say")
            )

            if comando_say:

                try:
                    risultato = subprocess.run(
                        [
                            comando_say,
                            "-v",
                            "Alice",
                            testo
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False
                    )

                    if risultato.returncode == 0:
                        return True

                    self._log(
                        "Il comando say ha restituito un errore."
                    )

                except Exception as errore:

                    self._log(
                        f"Errore say macOS: {errore}"
                    )

        # =========================================================
        # Piper
        # =========================================================

        if self.piper:

            try:

                file_audio = "/tmp/jarvis_tts.wav"

                risultato = subprocess.run(
                    [
                        self.piper,
                        "--output_file",
                        file_audio
                    ],
                    input=testo.encode("utf-8"),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )

                if (
                    risultato.returncode == 0
                    and os.path.exists(file_audio)
                    and self.afplay
                ):

                    riproduzione = subprocess.run(
                        [
                            self.afplay,
                            file_audio
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False
                    )

                    if riproduzione.returncode == 0:
                        return True

            except Exception as errore:

                self._log(
                    f"Errore Piper: {errore}"
                )

        # =========================================================
        # Linux / espeak
        # =========================================================

        if self.espeak:

            try:

                risultato = subprocess.run(
                    [
                        self.espeak,
                        testo
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )

                if risultato.returncode == 0:
                    return True

            except Exception as errore:

                self._log(
                    f"Errore espeak: {errore}"
                )

        return False

    def attiva_voce(self):
        """Attiva la sintesi vocale."""

        self.attiva = True
        self._rileva_disponibilita()

        self.attivo = self.disponibile

        return self.attivo

    def disattiva_voce(self):
        """Disattiva la sintesi vocale."""

        self.attiva = False
        self.attivo = False

        return True

    def ferma(self):
        """Arresta la sintesi vocale."""

        self.attiva = False
        self.attivo = False

        return True

    def stato(self):
        """Restituisce lo stato della sintesi vocale."""

        return {
            "attiva": self.attiva,
            "attivo": self.attivo,
            "disponibile": self.disponibile,
            "sistema": self.sistema,
            "piper": bool(self.piper),
            "say": bool(self.say),
            "espeak": bool(self.espeak),
            "afplay": bool(self.afplay)
        }

    def _log(self, messaggio):
        """Scrive nel logger del modulo voce."""

        try:

            if self.modulo_voce is not None:

                logger = getattr(
                    self.modulo_voce,
                    "logger",
                    None
                )

                if logger is not None:

                    metodo = getattr(
                        logger,
                        "info",
                        None
                    )

                    if callable(metodo):
                        metodo(messaggio)
                        return

        except Exception:
            pass

        print(messaggio)
