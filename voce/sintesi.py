import os
import platform
import shutil
import subprocess
import sys
import tempfile
import hashlib

from voce.elevenlabs import ElevenLabsVoce

try:
    from voce.tts import TextToSpeech
except ImportError:
    TextToSpeech = None


class SintesiVocale:
    """Motore vocale ufficiale di Jarvis.

    Su hardware lento come il MacBook Pro 2010 la voce live deve essere
    immediata: XTTS non viene piu usato per generare una risposta al volo.
    Le eventuali frasi XTTS gia generate vengono riprodotte dal voicepack;
    per tutto il resto viene usata subito la voce locale macOS.
    """

    def __init__(self, config=None):
        self.nome = "Sintesi Vocale"
        self.attivo = True
        self.config = config

        self.motore = os.environ.get(
            "JARVIS_VOICE_PROVIDER", "voicepack"
        ).strip().lower()
        self.voce_clonata = ElevenLabsVoce()
        self._voicepack_tts = None
        self._voicepack_tts_attempted = False

        # XTTS resta disponibile per generare/preparare il voicepack offline,
        # ma non deve bloccare la risposta live di Jarvis.
        self.xtts_attivo = os.environ.get(
            "JARVIS_ENABLE_XTTS", "1"
        ).strip().lower() in ("1", "true", "yes", "on")
        self.xtts_live = os.environ.get(
            "JARVIS_XTTS_LIVE", "0"
        ).strip().lower() in ("1", "true", "yes", "on")

        self._base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        self.modello = os.path.join(
            self._base_dir,
            "voce",
            "modelli",
            "it_IT-riccardo-x_low.onnx",
        )
        self.voce = "Jarvis"
        self.voce_sistema = None
        self.velocita = 0.92
        self.volume = 100
        self.stile = "Jarvis Cinematico"
        self.pausa_cinematica = True
        self.rate_cinematico = 156

        if config:
            voce_config = config.sezione("voce")
            self.motore = voce_config.get("motore", self.motore)
            modello_config = voce_config.get("modello", self.modello)
            self.modello = self._percorso_modello(modello_config)
            self.velocita = float(voce_config.get("velocita", self.velocita))
            self.volume = int(voce_config.get("volume", self.volume))
            self.stile = voce_config.get("stile", self.stile)
            self.voce = voce_config.get("voce", self.voce)
            self.pausa_cinematica = bool(voce_config.get("pausa_cinematica", self.pausa_cinematica))
            self.rate_cinematico = int(voce_config.get("rate_cinematico", self.rate_cinematico))

        self.motore = os.environ.get(
            "JARVIS_VOICE_PROVIDER", self.motore
        ).strip().lower()

        self.voce_riferimento = self._trova_campione_locale()
        self.voicepack_dir = os.path.join(self._base_dir, "voce", "voicepack")
        self.voce_sistema = self._trova_voce_italiana()

    def _trova_campione_locale(self):
        """Trova il campione WAV del Voice Pack senza configurazione manuale."""
        candidati = []
        riferimento = os.environ.get("JARVIS_VOICE_REFERENCE", "").strip()

        if riferimento:
            candidati.append(os.path.expanduser(riferimento))

        nome = "jarvis-are-you-there-at-your-service-sir.wav"
        candidati.extend(
            [
                os.path.join(os.path.expanduser("~"), "Desktop", nome),
                os.path.join(self._base_dir, "voce", "campioni", nome),
                os.path.join(self._base_dir, "voce", nome),
            ]
        )

        for percorso in candidati:
            percorso = os.path.abspath(percorso)
            if os.path.isfile(percorso) and percorso.lower().endswith(".wav"):
                return percorso

        return None

    def _trova_voce_italiana(self):
        """Preferisce una voce italiana maschile di sistema, se installata."""
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

            righe = risultato.stdout.splitlines()

            # Nelle installazioni macOS che la includono, Luca e una voce
            # italiana maschile e molto piu adatta al profilo Jarvis.
            preferite = ("Luca", "Federico", "Paolo", "Lorenzo")
            for nome in preferite:
                for riga in righe:
                    parti = riga.strip().split()
                    if parti and parti[0].lower() == nome.lower():
                        return parti[0]

            for riga in righe:
                parti = riga.strip().split()
                if parti and "it_IT" in riga:
                    return parti[0]

            for riga in righe:
                parti = riga.strip().split()
                if parti and (
                    "Italian" in riga or "italiano" in riga.lower()
                ):
                    return parti[0]

        except (OSError, subprocess.SubprocessError):
            return None

        return None

    def _percorso_modello(self, modello):
        percorso = os.path.expanduser(str(modello))
        if os.path.isabs(percorso):
            return percorso
        return os.path.normpath(os.path.join(self._base_dir, percorso))

    def _trova_piper(self):
        trovato = shutil.which("piper")
        if trovato:
            return trovato

        candidato = os.path.join(sys.prefix, "bin", "piper")
        if os.path.isfile(candidato) and os.access(candidato, os.X_OK):
            return candidato

        locale = os.path.join(self._base_dir, "voce", "bin", "piper")
        if os.path.isfile(locale) and os.access(locale, os.X_OK):
            return locale

        return None

    def _piper_disponibile(self):
        return (
            self.motore == "piper"
            and self._trova_piper() is not None
            and os.path.isfile(self.modello)
        )

    def _riproduci(self, file_audio):
        if platform.system() == "Darwin" and shutil.which("afplay"):
            try:
                risultato = subprocess.run(["afplay", file_audio], check=False)
                return risultato.returncode == 0
            except (OSError, subprocess.SubprocessError):
                return False

        if platform.system() == "Linux" and shutil.which("aplay"):
            try:
                risultato = subprocess.run(["aplay", "-q", file_audio], check=False)
                return risultato.returncode == 0
            except (OSError, subprocess.SubprocessError):
                return False

        return False

    def _parla_con_voce_clonata(self, testo):
        if self.motore not in ("elevenlabs", "voce_clonata", "clonata"):
            return False

        try:
            percorso = self.voce_clonata.parla(testo)
            if not percorso:
                return False
            try:
                return self._riproduci(percorso)
            finally:
                try:
                    os.remove(percorso)
                except OSError:
                    pass
        except (OSError, ValueError, RuntimeError):
            return False

    def _chiave_voicepack(self, testo):
        """Crea un nome stabile per una frase gia pronta nel voicepack."""
        normalizzato = " ".join(str(testo).strip().lower().split())
        digest = hashlib.sha256(normalizzato.encode("utf-8")).hexdigest()[:16]
        return os.path.join(self.voicepack_dir, digest + ".wav")

    def _parla_con_voicepack(self, testo):
        """Riproduce solo audio gia presente: nessuna generazione lenta live."""
        if not self.xtts_attivo:
            return False

        percorso = self._chiave_voicepack(testo)
        if not os.path.isfile(percorso) or os.path.getsize(percorso) == 0:
            return False

        try:
            print("🎙️ Voicepack Jarvis: riproduzione immediata.")
            return self._riproduci(percorso)
        except (OSError, subprocess.SubprocessError):
            return False

    def _parla_con_piper(self, testo):
        if not self._piper_disponibile():
            return False

        percorso = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as file_audio:
                percorso = file_audio.name

            piper = self._trova_piper()
            if not piper:
                return False

            comando = [
                piper,
                "--model",
                self.modello,
                "--output_file",
                percorso,
            ]

            ambiente = os.environ.copy()
            lib_dir = os.path.join(
                self._base_dir,
                "voce",
                "bin",
                "piper-phonemize",
                "lib",
            )
            if os.path.isdir(lib_dir):
                dyld = ambiente.get("DYLD_LIBRARY_PATH", "")
                ambiente["DYLD_LIBRARY_PATH"] = (
                    lib_dir if not dyld else lib_dir + os.pathsep + dyld
                )

            processo = subprocess.run(
                comando,
                input=testo,
                text=True,
                capture_output=True,
                env=ambiente,
                check=False,
            )

            if processo.returncode != 0:
                errore = (processo.stderr or processo.stdout or "").strip()
                if errore:
                    print(f"⚠️ Piper non ha generato l'audio: {errore}")
                return False

            if not os.path.isfile(percorso) or os.path.getsize(percorso) == 0:
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
        """Fallback live immediato."""
        if platform.system() == "Darwin" and shutil.which("say"):
            voce = self.voce_sistema
            try:
                comando = ["say"]
                if voce:
                    comando += ["-v", voce]
                rate = self.rate_cinematico if self.pausa_cinematica else int(170 * self.velocita)
                comando += ["-r", str(rate), str(testo)]
                risultato = subprocess.run(comando, check=False)
                return risultato.returncode == 0
            except (OSError, subprocess.SubprocessError):
                return False

        if platform.system() == "Linux" and shutil.which("espeak"):
            try:
                risultato = subprocess.run(
                    ["espeak", "-v", "it", str(testo)],
                    check=False,
                )
                return risultato.returncode == 0
            except (OSError, subprocess.SubprocessError):
                return False

        return False

    def parla(self, testo):
        if not self.attivo or not str(testo or "").strip():
            return False

        testo = str(testo).strip()

        try:
            if self._parla_con_voce_clonata(testo):
                return True

            # Prima scelta: frase gia preparata con XTTS, riproduzione immediata.
            if self._parla_con_voicepack(testo):
                return True

            # XTTS live resta disponibile solo se esplicitamente richiesto
            # tramite JARVIS_XTTS_LIVE=1. Non viene mai attivato per errore.
            if (
                self.xtts_live
                and self.xtts_attivo
                and self.voce_riferimento
                and TextToSpeech is not None
            ):
                if self._voicepack_tts is None and not self._voicepack_tts_attempted:
                    self._voicepack_tts_attempted = True
                    try:
                        self._voicepack_tts = TextToSpeech(
                            language="it_IT",
                            speed=self.velocita,
                            pitch=0.8,
                            reference_wav=self.voce_riferimento,
                            use_voice_clone=True,
                        )
                    except Exception as errore:
                        self._voicepack_tts = None
                        print(f"⚠️ XTTS live non disponibile: {errore}")

                if self._voicepack_tts is not None:
                    try:
                        if self._voicepack_tts.synthesize_and_play(testo):
                            return True
                    except Exception as errore:
                        print(f"⚠️ Errore XTTS live: {errore}")

            # Su High Sierra questa e la via rapida e affidabile.
            if platform.system() == "Darwin":
                if self._parla_con_sistema(testo):
                    return True
            else:
                if self._parla_con_piper(testo):
                    return True
                if self._parla_con_sistema(testo):
                    return True

        except (OSError, ValueError, subprocess.SubprocessError) as errore:
            print(f"⚠️ Errore sintesi vocale: {errore}")

        print(f"⚠️ Nessun motore vocale è riuscito a riprodurre: {testo}")
        return False

    def cambia_modello(self, modello):
        self.modello = self._percorso_modello(modello)
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
            "voce_clonata_disponibile": self.voce_clonata.disponibile(),
            "voicepack_tts_disponibile": TextToSpeech is not None and self.xtts_attivo,
            "xtts_attivo": self.xtts_attivo,
            "xtts_live": self.xtts_live,
            "voicepack_tts_inizializzato": self._voicepack_tts is not None,
            "campione_voce_locale": bool(self.voce_riferimento),
            "percorso_campione_voce": self.voce_riferimento,
            "profilo_cinematografico": True,
            "pausa_cinematica": self.pausa_cinematica,
            "rate_cinematico": self.rate_cinematico,
        }
