import subprocess
import os
import shutil
import platform


class SintesiVocale:
    """Sintesi vocale di Jarvis.

    Motore principale: Piper (con modello .onnx). Se Piper o il modello non
    sono disponibili, cade su fallback di sistema: `say` (macOS), `espeak`
    (Linux), oppure stampa a terminale. Non solleva mai eccezioni per
    dipendenze mancanti.
    """

    def __init__(self, config=None):

        self.nome = "Sintesi Vocale"

        self.attivo = True

        self.config = config

        # MOTORE VOCE
        self.motore = "piper"

        # MODELLO VOCALE
        self.modello = "voce/modelli/it_IT-jarvis.onnx"

        # IMPOSTAZIONI
        self.voce = "Jarvis"
        self.velocita = 1.0
        self.volume = 100
        self.stile = "Jarvis"

        if self.config:

            voce_config = self.config.sezione("voce")

            self.modello = voce_config.get(
                "modello",
                self.modello
            )

            self.velocita = voce_config.get(
                "velocita",
                1.0
            )

            self.volume = voce_config.get(
                "volume",
                100
            )

            self.stile = voce_config.get(
                "stile",
                "Jarvis"
            )

    def _piper_disponibile(self):
        return shutil.which("piper") is not None

    def _afplay_disponibile(self):
        return shutil.which("afplay") is not None

    def parla(self, testo):

        if not self.attivo:
            return False

        if not testo:
            return False

        try:

            # PIPER + modello presente + afplay per riprodurre
            if (
                self._piper_disponibile()
                and os.path.exists(self.modello)
            ):

                file_audio = "jarvis_voce.wav"

                comando = [
                    "piper",
                    "--model",
                    self.modello,
                    "--output_file",
                    file_audio
                ]

                processo = subprocess.Popen(
                    comando,
                    stdin=subprocess.PIPE,
                    text=True
                )

                processo.communicate(testo)

                if self._afplay_disponibile():
                    subprocess.run(
                        ["afplay", file_audio]
                    )
                else:
                    # Nessun player WAV: riproduzione non disponibile
                    print(f"[JARVIS] {testo}")

                if os.path.exists(file_audio):
                    os.remove(file_audio)

                return True

            # FALLBACK macOS: say
            if platform.system() == "Darwin" and shutil.which("say"):

                subprocess.run(["say", testo])

                return True

            # FALLBACK Linux: espeak
            if platform.system() == "Linux" and shutil.which("espeak"):

                subprocess.run(["espeak", "-v", "it", testo])

                return True

            # ULTIMO FALLBACK: stampa a terminale
            print(f"[JARVIS] {testo}")

            return True

        except Exception as errore:

            print(
                f"Errore sintesi vocale: {errore}"
            )

            return False

    def cambia_modello(self, modello):
        self.modello = modello

    def cambia_velocita(self, velocita):
        self.velocita = velocita

    def cambia_stile(self, stile):
        self.stile = stile

    def ferma(self):
        self.attivo = False

    def avvia(self):
        self.attivo = True
        return True

    def stato(self):

        return {
            "nome":
                self.nome,

            "stato":
                "attivo"
                if self.attivo
                else "spento",

            "motore":
                self.motore,

            "modello":
                self.modello,

            "velocita":
                self.velocita,

            "stile":
                self.stile,

            "piper_disponibile":
                self._piper_disponibile()
        }
