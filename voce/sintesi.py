import os
import platform
import shutil
import subprocess
import tempfile


class SintesiVocale:
    """Motore vocale ufficiale di Jarvis con Piper e fallback di sistema."""

    def __init__(self, config=None):
        self.nome = "Sintesi Vocale"
        self.attivo = True
        self.config = config

        self.motore = "piper"
        self.modello = "voce/modelli/it_IT-jarvis.onnx"
        self.voce = "Jarvis"
        self.voce_sistema = None
        self.velocita = 1.0
        self.volume = 100
        self.stile = "Jarvis"

        if config:
            voce_config = config.sezione("voce")
            self.motore = voce_config.get("motore", self.motore)
            self.modello = voce_config.get("modello", self.modello)
            self.velocita = float(voce_config.get("velocita", self.velocita))
            self.volume = int(voce_config.get("volume", self.volume))
            self.stile = voce_config.get("stile", self.stile)
            self.voce = voce_config.get("voce", self.voce)

        self.voce_sistema = self._trova_voce_italiana()

    def _trova_voce_italiana(self):
        """Trova una voce italiana installata sul sistema."""
        if platform.system() != "Darwin":
            return None

        say = shutil.which("say")
        if not say:
            return None

        try:
            risultato = subprocess.run(
                [say, "-v", "?"],
                capture_output=True,
                text=True,
                check=False,
            )

            if risultato.returncode != 0:
                return None

            voci = risultato.stdout.splitlines()

            for riga in voci:
                parti = riga.strip().split()
                if not parti:
                    continue
                nome_voce = parti[0]
                if "it_IT" in riga:
                    return nome_voce

            for riga in voci:
                parti = riga.strip().split()
                if not parti:
                    continue
                nome_voce = parti[0]
                if "Italian" in riga or "italiano" in riga.lower():
                    return nome_voce

        except (OSError, subprocess.SubprocessError):
            return None

        return None

    def _piper_disponibile(self):
        return (
            self.motore.lower() == "piper"
            and shutil.which("piper") is not None
            and os.path.isfile(self.modello)
        )

    def _riproduci(self, file_audio):
        if platform.system() == "Darwin" and shutil.which("afplay"):
            risultato = subprocess.run(["afplay", file_audio], check=False)
            return risultato.returncode == 0

        if platform.system() == "Linux" and shutil.which("aplay"):
            risultato = subprocess.run(["aplay", "-q", file_audio], check=False)
            return risultato.returncode == 0

        return False

    def _parla_con_piper(self, testo):
        """Sintetizza e riproduce il testo tramite Piper."""
        if not self._piper_disponibile():
            return False

        percorso = None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as file_audio:
                percorso = file_audio.name

            processo = subprocess.run(
                ["piper", "--model", self.modello, "--output_file", percorso],
                input=testo,
                text=True,
                capture_output=True,
                check=False,
            )

            if processo.returncode != 0:
                return False

            return self._riproduci(percorso)

        except (OSError, subprocess.SubprocessError):
            return False

        finally:
            if percorso:
                try:
                    os.remove(percorso)
                except OSError:
                    pass

    def _parla_con_sistema(self, testo):
        """Usa il motore vocale integrato nel sistema operativo."""
        if platform.system() == "Darwin" and shutil.which("say"):
            voce = self.voce_sistema or self.voce

            risultato = subprocess.run(
                [
                    "say",
                    "-v",
                    voce,
                    "-r",
                    str(int(170 * self.velocita)),
                    testo,
                ],
                check=False,
            )

            if risultato.returncode == 0:
                return True

            # Se la voce configurata non esiste, prova il motore predefinito.
            risultato = subprocess.run(
                [
                    "say",
                    "-r",
                    str(int(170 * self.velocita)),
                    testo,
                ],
                check=False,
            )
            return risultato.returncode == 0

        if platform.system() == "Linux" and shutil.which("espeak"):
            risultato = subprocess.run(
                ["espeak", "-v", "it", testo],
                check=False,
            )
            return risultato.returncode == 0

        return False

    def parla(self, testo):
        if not self.attivo or not str(testo or "").strip():
            return False

        testo = str(testo).strip()

        try:
            if self._parla_con_piper(testo):
                return True

            if self._parla_con_sistema(testo):
                return True

            print(f"[JARVIS] {testo}")
            return True

        except (OSError, ValueError, subprocess.SubprocessError):
            print(f"[JARVIS] {testo}")
            return False

    def cambia_modello(self, modello):
        self.modello = str(modello)
        return self.modello

    def cambia_velocita(self, velocita):
        self.velocita = max(0.1, min(3.0, float(velocita)))
        return self.velocita

    def cambia_stile(self, stile):
        self.stile = str(stile)
        return self.stile

    def ferma(self):
        self.attivo = False
        return True

    def avvia(self):
        self.attivo = True
        return True

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo" if self.attivo else "spento",
            "motore": self.motore,
            "modello": self.modello,
            "voce": self.voce,
            "voce_sistema": self.voce_sistema,
            "velocita": self.velocita,
            "volume": self.volume,
            "stile": self.stile,
            "piper_disponibile": self._piper_disponibile(),
        }
