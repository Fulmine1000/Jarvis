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

    def _piper_disponibile(self):
        return shutil.which("piper") is not None and os.path.isfile(self.modello)

    def _riproduci(self, file_audio):
        if platform.system() == "Darwin" and shutil.which("afplay"):
            risultato = subprocess.run(["afplay", file_audio], check=False)
            return risultato.returncode == 0
        if platform.system() == "Linux" and shutil.which("aplay"):
            risultato = subprocess.run(["aplay", "-q", file_audio], check=False)
            return risultato.returncode == 0
        return False

    def parla(self, testo):
        if not self.attivo or not str(testo or "").strip():
            return False
        testo = str(testo).strip()

        try:
            if self._piper_disponibile():
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as file_audio:
                    percorso = file_audio.name
                try:
                    processo = subprocess.run(
                        ["piper", "--model", self.modello, "--output_file", percorso],
                        input=testo,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    if processo.returncode == 0 and self._riproduci(percorso):
                        return True
                finally:
                    try:
                        os.remove(percorso)
                    except OSError:
                        pass

            if platform.system() == "Darwin" and shutil.which("say"):
                risultato = subprocess.run(
                    ["say", "-v", self.voce, "-r", str(int(170 * self.velocita)), testo],
                    check=False,
                )
                return risultato.returncode == 0

            if platform.system() == "Linux" and shutil.which("espeak"):
                risultato = subprocess.run(["espeak", "-v", "it", testo], check=False)
                return risultato.returncode == 0

            print(f"[JARVIS] {testo}")
            return True
        except (OSError, ValueError, subprocess.SubprocessError):
            print(f"[JARVIS] {testo}")
            return False

    def cambia_modello(self, modello):
        self.modello = str(modello)
        return self.modello

    def cambia_velocita(self, velocita):
        self.velocita = max(0.1, min(3, float(velocita)))
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
            "velocita": self.velocita,
            "volume": self.volume,
            "stile": self.stile,
            "piper_disponibile": self._piper_disponibile(),
        }
