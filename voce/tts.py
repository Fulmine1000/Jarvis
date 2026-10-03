"""
Text-to-Speech di Jarvis.

Motori supportati:
1. Coqui XTTS v2 locale con riferimento WAV.
2. Coqui Glow-TTS italiano come fallback locale.
3. pyttsx3.
4. macOS "say".

Il profilo XTTS usa un post-processing leggero "cinematico" per ottenere
una voce italiana maschile piu profonda, controllata e cinematografica,
senza tentare di riprodurre indistinguibilmente la voce di un doppiatore.
Il motore resta lazy-loaded per non rallentare l'avvio di Jarvis.
"""

import os
import platform
import shutil
import subprocess
import tempfile
import threading
import multiprocessing
from typing import Optional

TTS = None
HAS_TTS = None


def _carica_coqui():
    """Carica Coqui TTS solo quando serve."""
    global TTS, HAS_TTS
    if HAS_TTS is not None:
        return bool(HAS_TTS)

    try:
        from TTS.api import TTS as CoquiTTS
        TTS = CoquiTTS
        HAS_TTS = True
    except Exception as errore:
        TTS = None
        HAS_TTS = False
        print(f"⚠️ Coqui TTS non disponibile: {errore}")

    return bool(HAS_TTS)


try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    pyttsx3 = None
    HAS_PYTTSX3 = False


def _xtts_worker(model_name: str, text: str, reference_wav: str, language: str, audio_path: str, status_path: str) -> None:
    """Processo isolato per XTTS: un eventuale crash di PyTorch/Coqui non abbatte Jarvis."""
    try:
        from TTS.api import TTS as CoquiTTS

        print("🔊 Processo XTTS: caricamento modello...", flush=True)
        model = CoquiTTS(
            model_name=model_name,
            progress_bar=False,
            gpu=False,
        )
        print("🎙️ Processo XTTS: generazione audio...", flush=True)
        model.tts_to_file(
            text=text,
            speaker_wav=reference_wav,
            language=language,
            file_path=audio_path,
        )
        with open(status_path, "w", encoding="utf-8") as stato:
            stato.write("OK")
    except Exception as errore:
        try:
            with open(status_path, "w", encoding="utf-8") as stato:
                stato.write("ERROR:" + str(errore))
        except Exception:
            pass
        raise


class TextToSpeech:
    """Sintesi vocale locale di Jarvis con profilo vocale cinematografico."""

    XTTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
    GLOW_MODEL = "tts_models/it/mai/glow-tts"
    DEFAULT_REFERENCE = "jarvis-are-you-there-at-your-service-sir.wav"

    def __init__(
        self,
        language: str = "it_IT",
        speed: float = 0.94,
        pitch: float = 0.8,
        reference_wav: Optional[str] = None,
        use_voice_clone: bool = True,
    ):
        self.language = self._normalizza_lingua(language)
        self.speed = max(0.5, min(1.5, float(speed)))
        self.pitch = max(0.5, min(1.5, float(pitch)))

        # Profilo "cinematico": modifiche leggere, applicate dopo XTTS.
        self.cinematic_voice = os.environ.get(
            "JARVIS_CINEMATIC_VOICE", "1"
        ).strip().lower() in ("1", "true", "yes", "on")
        self.pitch_steps = float(
            os.environ.get("JARVIS_CINEMATIC_PITCH", "-1.0")
        )
        self.time_rate = float(
            os.environ.get("JARVIS_CINEMATIC_RATE", "0.96")
        )

        self.model = None
        self.engine = None
        self.reference_wav = self._trova_campione(reference_wav)
        self.use_xtts = False
        self.use_coqui = False
        self.use_pyttsx3 = False

        # Il modello XTTS viene caricato al primo utilizzo, non durante l'avvio di Jarvis.
        # In questo modo un caricamento lento/non compatibile non blocca l'interfaccia.
        self._use_voice_clone = bool(use_voice_clone)
        self._initialized = False

        # XTTS viene eseguito in un processo separato e avviato in background.
        # Cosi il caricamento di PyTorch/Coqui non puo bloccare il ciclo principale
        # di Jarvis e un crash nativo resta confinato al processo figlio.
        self.xtts_timeout = max(
            30.0,
            float(os.environ.get("JARVIS_XTTS_TIMEOUT", "120")),
        )
        self._xtts_thread = None
        self._xtts_process = None
        self._xtts_lock = threading.Lock()
        self._xtts_busy = False

    def _inizializza(self, use_voice_clone: bool) -> None:
        if _carica_coqui() and use_voice_clone and self.reference_wav:
            try:
                print("🔊 Caricamento voce locale Jarvis (XTTS v2)...")
                self.model = TTS(
                    model_name=self.XTTS_MODEL,
                    progress_bar=False,
                    gpu=False,
                )
                self.use_xtts = True
                print("✅ Motore vocale XTTS v2 pronto")
                print(f"🎙️ Riferimento vocale: {self.reference_wav}")
                print(
                    "🎬 Profilo voce cinematografico: "
                    f"pitch {self.pitch_steps:+.1f} st, "
                    f"ritmo {self.time_rate:.2f}"
                )
                return
            except Exception as errore:
                self.model = None
                print(f"⚠️ XTTS v2 non disponibile: {errore}")

        if _carica_coqui():
            try:
                print("🔊 Caricamento Coqui Glow-TTS italiano...")
                self.model = TTS(
                    model_name=self.GLOW_MODEL,
                    progress_bar=False,
                    gpu=False,
                )
                self.use_coqui = True
                print("✅ Coqui TTS italiano caricato")
                return
            except Exception as errore:
                self.model = None
                print(f"⚠️ Coqui TTS non disponibile: {errore}")

        if HAS_PYTTSX3:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", int(170 * self.speed))
                self.use_pyttsx3 = True
                print("✅ pyttsx3 inizializzato")
                return
            except Exception as errore:
                self.engine = None
                print(f"⚠️ pyttsx3 non disponibile: {errore}")

        if platform.system() == "Darwin" and shutil.which("say"):
            print("✅ Utilizzo voce di sistema macOS come fallback")

    def _trova_campione(self, riferimento: Optional[str]) -> Optional[str]:
        candidati = []

        if riferimento:
            candidati.append(os.path.expanduser(str(riferimento)))

        variabile = os.environ.get("JARVIS_VOICE_REFERENCE")
        if variabile:
            candidati.append(os.path.expanduser(variabile))

        home = os.path.expanduser("~")
        candidati.append(os.path.join(home, "Desktop", self.DEFAULT_REFERENCE))

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidati.extend(
            [
                os.path.join(
                    base_dir, "voce", "campioni", self.DEFAULT_REFERENCE
                ),
                os.path.join(base_dir, "voce", self.DEFAULT_REFERENCE),
            ]
        )

        for percorso in candidati:
            percorso = os.path.abspath(percorso)
            if os.path.isfile(percorso) and percorso.lower().endswith(".wav"):
                return percorso

        return None

    def _inizializza_lazy(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._inizializza(self._use_voice_clone)

    def set_reference_wav(self, percorso: str) -> bool:
        if not percorso:
            return False

        percorso = os.path.abspath(os.path.expanduser(str(percorso)))
        if not os.path.isfile(percorso) or not percorso.lower().endswith(".wav"):
            return False

        self.reference_wav = percorso

        if _carica_coqui() and not self.use_xtts:
            try:
                self.model = TTS(
                    model_name=self.XTTS_MODEL,
                    progress_bar=False,
                    gpu=False,
                )
                self.use_xtts = True
                self.use_coqui = False
                return True
            except Exception as errore:
                print(f"⚠️ Impossibile attivare XTTS v2: {errore}")

        return self.use_xtts

    def synthesize_and_play(self, text: str) -> bool:
        testo = str(text or "").strip()
        if not testo:
            return False

        # Non carichiamo mai XTTS nel thread principale. La prima risposta
        # vocale viene messa in coda a un worker isolato e Jarvis resta reattivo.
        if self.reference_wav and self._use_voice_clone:
            if self._avvia_xtts_background(testo):
                return True

        # Fallback immediati quando non esiste un campione o XTTS e disattivato.
        if not self._initialized:
            self._inizializza_lazy()

        if self.use_coqui and self._play_with_coqui(testo):
            return True
        if self.use_pyttsx3 and self._play_with_pyttsx3(testo):
            return True
        if self._play_with_macos(testo):
            return True

        print(f"⚠️ Sintesi vocale non disponibile. Testo: {testo}")
        return False

    def _avvia_xtts_background(self, text: str) -> bool:
        """Avvia XTTS senza bloccare il processo principale di Jarvis."""
        with self._xtts_lock:
            if self._xtts_busy:
                # Evita due generazioni pesanti contemporaneamente.
                print("⚠️ XTTS sta gia elaborando una risposta vocale.")
                return True
            self._xtts_busy = True

        self._xtts_thread = threading.Thread(
            target=self._worker_xtts,
            args=(text,),
            name="Jarvis-XTTS",
            daemon=True,
        )
        self._xtts_thread.start()
        return True

    def _worker_xtts(self, text: str) -> None:
        audio_path = None
        status_path = None
        process = None

        try:
            if not _carica_coqui():
                raise RuntimeError("Coqui TTS non disponibile")

            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as file_audio:
                audio_path = file_audio.name

            with tempfile.NamedTemporaryFile(
                suffix=".status", delete=False
            ) as file_status:
                status_path = file_status.name

            ctx = multiprocessing.get_context("spawn")
            process = ctx.Process(
                target=_xtts_worker,
                args=(
                    self.XTTS_MODEL,
                    text,
                    self.reference_wav,
                    self.language,
                    audio_path,
                    status_path,
                ),
                daemon=True,
            )
            self._xtts_process = process
            print(
                "🎙️ XTTS avviato in background. "
                "Jarvis rimane operativo mentre preparo la voce..."
            )
            process.start()
            process.join(self.xtts_timeout)

            if process.is_alive():
                print(
                    f"⏱️ XTTS ha superato il limite di {self.xtts_timeout:.0f}s; "
                    "termino il worker e uso la voce di sistema."
                )
                process.terminate()
                process.join(5)
                self._fallback_background(text)
                return

            if process.exitcode != 0:
                errore = ""
                try:
                    with open(status_path, "r", encoding="utf-8") as stato:
                        errore = stato.read().strip()
                except Exception:
                    pass
                print(
                    "⚠️ Il processo XTTS e terminato senza audio"
                    + (f": {errore}" if errore else ".")
                )
                self._fallback_background(text)
                return

            if not os.path.isfile(audio_path) or os.path.getsize(audio_path) == 0:
                print("⚠️ XTTS non ha prodotto un WAV valido.")
                self._fallback_background(text)
                return

            print("✅ XTTS ha generato l'audio Jarvis.")
            processed_path = None
            try:
                if self.cinematic_voice:
                    processed_path = self._applica_profilo_cinematografico(audio_path)
                self._play_audio(processed_path or audio_path)
            finally:
                self._elimina_file_temporaneo(processed_path)

        except Exception as errore:
            print(f"⚠️ XTTS in background non disponibile: {errore}")
            self._fallback_background(text)
        finally:
            if process is not None and process.is_alive():
                try:
                    process.terminate()
                    process.join(2)
                except Exception:
                    pass
            self._xtts_process = None
            self._elimina_file_temporaneo(audio_path)
            self._elimina_file_temporaneo(status_path)
            with self._xtts_lock:
                self._xtts_busy = False

    def _fallback_background(self, text: str) -> None:
        """Fallback sicuro eseguito dallo stesso worker vocale."""
        try:
            if platform.system() == "Darwin" and shutil.which("say"):
                print("🔊 Fallback immediato alla voce di sistema macOS.")
                self._play_with_macos(text)
                return
            if HAS_PYTTSX3:
                if not self.use_pyttsx3:
                    try:
                        self.engine = pyttsx3.init()
                        self.use_pyttsx3 = True
                    except Exception:
                        pass
                if self.use_pyttsx3:
                    self._play_with_pyttsx3(text)
                    return
        except Exception as errore:
            print(f"⚠️ Fallback vocale fallito: {errore}")

        print(f"⚠️ Sintesi vocale non disponibile. Testo: {text}")

    def _play_with_xtts(self, text: str) -> bool:
        """Compatibilita: inoltra la richiesta al worker non bloccante."""
        return self._avvia_xtts_background(text)

    def _applica_profilo_cinematografico(self, audio_path: str) -> Optional[str]:
        """Applica un trattamento leggero a XTTS per una resa piu cinematografica.

        Non sostituisce il modello vocale: agisce su pitch, ritmo e dinamica
        del WAV gia generato. Se le librerie audio non sono disponibili,
        il file originale viene usato senza trattamento.
        """
        try:
            import librosa
            import numpy as np
            import soundfile as sf

            y, sr = librosa.load(audio_path, sr=None, mono=True)
            if y.size == 0:
                return None

            # Elimina silenzio eccessivo ai bordi senza tagliare il parlato.
            y, _ = librosa.effects.trim(y, top_db=38)
            if y.size == 0:
                return None

            if abs(self.pitch_steps) > 0.01:
                y = librosa.effects.pitch_shift(
                    y, sr=sr, n_steps=self.pitch_steps
                )

            if abs(self.time_rate - 1.0) > 0.01:
                y = librosa.effects.time_stretch(
                    y, rate=max(0.75, min(1.25, self.time_rate))
                )

            # Compressione morbida: aumenta la presenza senza creare un
            # effetto radio/robotico.
            livello = np.abs(y)
            picco = float(np.max(livello)) if livello.size else 0.0
            if picco > 0:
                soglia = 0.72
                y = np.where(
                    np.abs(y) > soglia,
                    np.sign(y)
                    * (
                        soglia
                        + (1.0 - soglia)
                        * np.tanh(
                            (np.abs(y) - soglia) / (1.0 - soglia)
                        )
                    ),
                    y,
                )

            picco = float(np.max(np.abs(y))) if y.size else 0.0
            if picco > 0:
                y = y / picco * 0.92

            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as file_audio:
                processed_path = file_audio.name

            sf.write(processed_path, y, sr, subtype="PCM_16")
            return processed_path

        except Exception as errore:
            print(f"⚠️ Post-processing cinematico saltato: {errore}")
            return None

    def _play_with_coqui(self, text: str) -> bool:
        if not self.model:
            return False

        audio_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as file_audio:
                audio_path = file_audio.name

            print("🎙️ Sintetizzazione con Coqui TTS...")
            self.model.tts_to_file(
                text=text,
                file_path=audio_path,
                language_idx="it",
            )
            return self._play_audio(audio_path)
        except Exception as errore:
            print(f"❌ Errore Coqui: {errore}")
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
            print(f"❌ Errore pyttsx3: {errore}")
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
                    risultato = subprocess.run([afplay, file_path], check=False)
                    if risultato.returncode == 0:
                        return True
                except (OSError, subprocess.SubprocessError):
                    pass

        ffplay = shutil.which("ffplay")
        if ffplay:
            try:
                risultato = subprocess.run(
                    [
                        ffplay,
                        "-nodisp",
                        "-autoexit",
                        "-loglevel",
                        "quiet",
                        file_path,
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
    def _elimina_file_temporaneo(file_path: Optional[str]) -> None:
        if not file_path:
            return
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass

    @staticmethod
    def _normalizza_lingua(language: str) -> str:
        lingua = str(language or "it").strip()
        if "_" in lingua:
            lingua = lingua.split("_", 1)[0]
        if "-" in lingua:
            lingua = lingua.split("-", 1)[0]
        return lingua.lower() or "it"

    def stato(self) -> dict:
        if self.use_xtts:
            motore = "xtts-cinematic"
        elif self.use_coqui:
            motore = "coqui-glow-tts"
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
            "profilo_cinematografico": self.cinematic_voice,
            "pitch_steps": self.pitch_steps,
            "cinematic_rate": self.time_rate,
            "campione_voce": self.reference_wav,
            "campione_disponibile": bool(
                self.reference_wav and os.path.isfile(self.reference_wav)
            ),
            "xtts_disponibile": self.use_xtts,
            "coqui_disponibile": self.use_coqui,
            "pyttsx3_disponibile": self.use_pyttsx3,
        }

    def ferma(self) -> bool:
        try:
            if self.engine and self.use_pyttsx3:
                self.engine.stop()
        except Exception:
            pass

        processo = self._xtts_process
        if processo is not None and processo.is_alive():
            try:
                processo.terminate()
                processo.join(2)
            except Exception:
                pass
        self._xtts_process = None
        with self._xtts_lock:
            self._xtts_busy = False

        if platform.system() == "Darwin":
            try:
                subprocess.run(
                    ["killall", "afplay"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            except Exception:
                pass

        return True
