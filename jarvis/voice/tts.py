"""
Text-to-Speech (Sintesi Vocale) di Jarvis.

Motori supportati:
1. Coqui XTTS v2 con campione WAV per la clonazione vocale locale.
2. Coqui Glow-TTS come fallback locale.
3. pyttsx3 come ulteriore fallback.
4. macOS "say" come ultimo fallback.

Il motore XTTS v2 permette a Jarvis di usare un campione della voce
come riferimento senza richiedere un'API esterna.
"""

import os
import platform
import shutil
import subprocess
import tempfile
from typing import Optional

try:
    from TTS.api import TTS
    HAS_TTS = True
except ImportError:
    TTS = None
    HAS_TTS = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    pyttsx3 = None
    HAS_PYTTSX3 = False


class TextToSpeech:
    """Motore TTS di Jarvis con clonazione vocale locale e fallback."""

    XTTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
    GLOW_MODEL = "tts_models/it/mai/glow-tts"

    def __init__(
        self,
        language: str = "it",
        speed: float = 0.9,
        pitch: float = 0.8,
        reference_wav: Optional[str] = None,
        use_voice_clone: bool = True,
    ):
        self.language = self._normalizza_lingua(language)
        self.speed = max(0.5, min(1.5, float(speed)))
        self.pitch = max(0.5, min(1.5, float(pitch)))
        self.model = None
        self.engine = None
        self.use_xtts = False
        self.use_glow = False
        self.use_pyttsx3 = False
        self.reference_wav = self._trova_campione(reference_wav)

        if use_voice_clone:
            self._inizializza()

    def _inizializza(self):
        if HAS_TTS:
            if self.reference_wav:
                try:
                    print("Caricamento voce locale Jarvis (XTTS v2)...")
                    self.model = TTS(
                        model_name=self.XTTS_MODEL,
                        progress_bar=False,
                        gpu=False,
                    )
                    self.use_xtts = True
                    print("Motore vocale XTTS v2 pronto")
                    print(f"Campione voce: {self.reference_wav}")
                    return
                except Exception as errore:
                    self.model = None
                    self.use_xtts = False
                    print(f"XTTS v2 non disponibile: {errore}")

            try:
                print("Caricamento Coqui Glow-TTS italiano...")
                self.model = TTS(
                    model_name=self.GLOW_MODEL,
                    progress_bar=False,
                    gpu=False,
                )
                self.use_glow = True
                print("Coqui Glow-TTS italiano caricato")
                return
            except Exception as errore:
                self.model = None
                self.use_glow = False
                print(f"Coqui TTS non disponibile: {errore}")

        if HAS_PYTTSX3:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", int(170 * self.speed))
                self.use_pyttsx3 = True
                print("pyttsx3 inizializzato")
                return
            except Exception as errore:
                self.engine = None
                self.use_pyttsx3 = False
                print(f"pyttsx3 non disponibile: {errore}")

        if platform.system() == "Darwin" and shutil.which("say"):
            print("Utilizzo voce di sistema macOS come fallback")
            return

        print("Nessun motore TTS disponibile.")

    def _trova_campione(self, riferimento: Optional[str]) -> Optional[str]:
        candidati = []

        if riferimento:
            candidati.append(os.path.expanduser(str(riferimento)))

        variabile = os.environ.get("JARVIS_VOICE_REFERENCE")
        if variabile:
            candidati.append(os.path.expanduser(variabile))

        home = os.path.expanduser("~")
        candidati.extend([
            os.path.join(
                home, "Desktop",
                "jarvis-are-you-there-at-your-service-sir.wav",
            ),
        ])

        base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        candidati.extend([
            os.path.join(
                base_dir, "voce", "campioni",
                "jarvis-are-you-there-at-your-service-sir.wav",
            ),
            os.path.join(
                base_dir, "voce", "modelli",
                "jarvis-are-you-there-at-your-service-sir.wav",
            ),
            os.path.join(
                base_dir, "voce",
                "jarvis-are-you-there-at-your-service-sir.wav",
            ),
        ])

        for percorso in candidati:
            if not percorso:
                continue
            percorso = os.path.abspath(percorso)
            if (
                os.path.isfile(percorso)
                and percorso.lower().endswith(".wav")
            ):
                return percorso

        return None

    def set_reference_wav(self, percorso: str) -> bool:
        if not percorso:
            return False

        percorso = os.path.abspath(os.path.expanduser(str(percorso)))
        if not os.path.isfile(percorso):
            return False
        if not percorso.lower().endswith(".wav"):
            return False

        self.reference_wav = percorso

        if HAS_TTS and not self.use_xtts:
            try:
                self.model = TTS(
                    model_name=self.XTTS_MODEL,
                    progress_bar=False,
                    gpu=False,
                )
                self.use_xtts = True
                self.use_glow = False
            except Exception:
                self.model = None
                self.use_xtts = False

        return True

    @staticmethod
    def _normalizza_lingua(language: str) -> str:
        lingua = str(language or "it").strip()
        if "_" in lingua:
            lingua = lingua.split("_", 1)[0]
        if "-" in lingua:
            lingua = lingua.split("-", 1)[0]
        return lingua.lower() or "it"

    def synthesize_and_play(self, text: str) -> bool:
        testo = str(text or "").strip()
        if not testo:
            return False

        if self.use_xtts and self.reference_wav:
            if self._play_with_xtts(testo):
                return True

        if self.use_glow:
            if self._play_with_glow(testo):
                return True

        if self.use_pyttsx3:
            if self._play_with_pyttsx3(testo):
                return True

        if self._play_with_macos(testo):
            return True

        print(f"Sintesi vocale non disponibile. Testo: {testo}")
        return False

    def _play_with_xtts(self, text: str) -> bool:
        if not self.model or not self.reference_wav:
            return False
        if not os.path.isfile(self.reference_wav):
            return False

        audio_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as file_audio:
                audio_path = file_audio.name

            print("Sintetizzazione con voce Jarvis...")
            self.model.tts_to_file(
                text=text,
                speaker_wav=self.reference_wav,
                language=self.language,
                file_path=audio_path,
            )

            if not os.path.isfile(audio_path):
                return False
            return self._play_audio(audio_path)
        except Exception as errore:
            print(f"Errore voce clonata XTTS: {errore}")
            return False
        finally:
            self._elimina_file_temporaneo(audio_path)

    def _play_with_glow(self, text: str) -> bool:
        if not self.model:
            return False

        audio_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as file_audio:
                audio_path = file_audio.name

            print("Sintetizzazione con Coqui Glow-TTS...")
            self.model.tts_to_file(
                text=text,
                file_path=audio_path,
                language_idx="it",
            )

            if not os.path.isfile(audio_path):
                return False
            return self._play_audio(audio_path)
        except Exception as errore:
            print(f"Errore Coqui Glow-TTS: {errore}")
            return False
        finally:
            self._elimina_file_temporaneo(audio_path)

    def _play_with_pyttsx3(self, text: str) -> bool:
        if not self.engine:
            return False

        try:
            self.engine.setProperty("rate", int(170 * self.speed))
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as errore:
            print(f"Errore pyttsx3: {errore}")
            return False

    def _play_with_macos(self, text: str) -> bool:
        if platform.system() != "Darwin":
            return False

        say = shutil.which("say")
        if not say:
            return False

        try:
            risultato = subprocess.run(
                [say, "-r", str(int(170 * self.speed)), text],
                check=False,
            )
            return risultato.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def _play_audio(self, file_path: str) -> bool:
        if not file_path or not os.path.isfile(file_path):
            return False

        if platform.system() == "Darwin":
            afplay = shutil.which("afplay")
            if afplay:
                try:
                    risultato = subprocess.run(
                        [afplay, file_path],
                        check=False,
                    )
                    if risultato.returncode == 0:
                        return True
                except (OSError, subprocess.SubprocessError):
                    pass

        ffplay = shutil.which("ffplay")
        if ffplay:
            try:
                risultato = subprocess.run(
                    [
                        ffplay, "-nodisp", "-autoexit",
                        "-loglevel", "quiet", file_path,
                    ],
                    check=False,
                )
                if risultato.returncode == 0:
                    return True
            except (OSError, subprocess.SubprocessError):
                pass

        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.quit()
            return True
        except Exception:
            return False

    @staticmethod
    def _elimina_file_temporaneo(file_path: Optional[str]):
        if not file_path:
            return
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass

    def stato(self) -> dict:
        if self.use_xtts:
            motore = "xtts"
        elif self.use_glow:
            motore = "glow-tts"
        elif self.use_pyttsx3:
            motore = "pyttsx3"
        elif platform.system() == "Darwin" and shutil.which("say"):
            motore = "macos-say"
        else:
            motore = "nessuno"

        return {
            "motore": motore,
            "lingua": self.language,
            "velocita": self.speed,
            "tono": self.pitch,
            "campione_voce": self.reference_wav,
            "campione_disponibile": bool(
                self.reference_wav
                and os.path.isfile(self.reference_wav)
            ),
            "xtts_disponibile": self.use_xtts,
            "glow_tts_disponibile": self.use_glow,
            "pyttsx3_disponibile": self.use_pyttsx3,
        }

    def ferma(self) -> bool:
        try:
            if self.engine and self.use_pyttsx3:
                self.engine.stop()
        except Exception:
            pass

        try:
            if platform.system() == "Darwin":
                subprocess.run(
                    ["killall", "afplay"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
        except Exception:
            pass

        return True
