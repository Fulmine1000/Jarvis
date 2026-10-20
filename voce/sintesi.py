import os
import platform
import shutil
import subprocess
import sys
import tempfile
import hashlib
import re

from voce.elevenlabs import ElevenLabsVoce

try:
    from voce.tts import TextToSpeech
except ImportError:
    TextToSpeech = None


class SintesiVocale:
    """Motore vocale ufficiale di Jarvis.

    Usa prima le frasi gia pronte nel voicepack e, quando mancano,
    prova la voce clonata XTTS in background. Se il modello non e disponibile
    o la generazione fallisce, mantiene il fallback vocale di sistema.
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

        # La generazione XTTS avviene in background: Jarvis non resta bloccato
        # durante il caricamento del modello. E disattivabile esplicitamente.
        self.xtts_attivo = os.environ.get(
            "JARVIS_ENABLE_XTTS", "1"
        ).strip().lower() in ("1", "true", "yes", "on")
        # Su macOS (in particolare High Sierra/Intel) il worker XTTS puo
        # impiegare molto tempo o fallire durante il caricamento di PyTorch.
        # Per evitare che Jarvis resti muto, il live XTTS e opt-in su macOS:
        # la voce di sistema viene usata subito finche il worker non e verificato.
        # Su altri sistemi resta attivo come prima; si puo sempre forzare con
        # JARVIS_XTTS_LIVE=1 dopo aver verificato la compatibilita.
        default_xtts_live = "0" if platform.system() == "Darwin" else "1"
        self.xtts_live = os.environ.get(
            "JARVIS_XTTS_LIVE", default_xtts_live
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

    @staticmethod
    def _testo_per_xtts(testo):
        """Aiuta XTTS sulla pronuncia italiana di blu senza alterare il testo mostrato."""
        return re.sub(r"\bblu\b", "blù", str(testo), flags=re.IGNORECASE)

    def _parla_con_voicepack(self, testo):
        """Riproduce audio gia presente, tranne frasi con la pronuncia difettosa."""
        if not self.xtts_attivo:
            return False
        if re.search(r"\bblu\b", str(testo), flags=re.IGNORECASE):
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

    def _parla_con_sistema(self, testo, voce_forzata=None):
        """Fallback live immediato, con secondo tentativo senza voce nominata.

        Su macOS meno recenti una voce può comparire nell'elenco ma non essere
        utilizzabile. Se il tentativo con la voce scelta fallisce, riprova con
        la voce predefinita di sistema invece di lasciare Jarvis completamente muto.
        """
        if platform.system() == "Darwin" and shutil.which("say"):
            rate = self.rate_cinematico if self.pausa_cinematica else int(170 * self.velocita)
            base = ["say", "-r", str(rate), str(testo)]
            comandi = []
            # Una voce scelta esplicitamente ha priorita: serve, ad esempio,
            # per la parola "blu", che sul Mac dell'utente e pronunciata
            # correttamente da Alice ma non dalla voce clonata di Jarvis.
            if voce_forzata:
                comandi.append(["say", "-v", voce_forzata, "-r", str(rate), str(testo)])
            if self.voce_sistema and self.voce_sistema != voce_forzata:
                comandi.append(["say", "-v", self.voce_sistema, "-r", str(rate), str(testo)])
            comandi.append(base)

            for indice, comando in enumerate(comandi):
                try:
                    risultato = subprocess.run(
                        comando,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if risultato.returncode == 0:
                        return True
                    dettaglio = (risultato.stderr or risultato.stdout or "").strip()
                    if dettaglio:
                        print(f"⚠️ macOS say (tentativo {indice + 1}): {dettaglio}")
                except (OSError, subprocess.SubprocessError) as errore:
                    print(f"⚠️ macOS say (tentativo {indice + 1}): {errore}")
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

        # La sintesi di sistema gestisce meglio un unico flusso continuo:
        # rimuoviamo a capo e spazi ripetuti che possono creare pause spezzate.
        testo = " ".join(str(testo).strip().split())

        try:
            # Su questo Mac la voce predefinita pronuncia "blu" come "bleah".
            # Alice pronuncia correttamente questa parola; per non cambiare la
            # voce generale di Jarvis, la usiamo solo nelle frasi che la contengono.
            if (
                platform.system() == "Darwin"
                and re.search(r"\bblu\b", testo, flags=re.IGNORECASE)
                and self._parla_con_sistema(testo, voce_forzata="Alice")
            ):
                return True

            if self._parla_con_voce_clonata(testo):
                return True

            # Prima scelta: frase gia preparata con XTTS, riproduzione immediata.
            if self._parla_con_voicepack(testo):
                return True

            # Se manca una frase pronta, prova la voce clonata XTTS in background.
            # Per blu applica una guida fonetica solo al testo inviato al sintetizzatore.
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
                        testo_sintesi = self._testo_per_xtts(testo)
                        if self._voicepack_tts.synthesize_and_play(testo_sintesi):
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
