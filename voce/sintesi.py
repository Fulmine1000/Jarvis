import os
import platform
import shutil
import subprocess
import sys
import tempfile
import hashlib
import re
import base64

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
        # La voce personalizzata Jarvis viene generata da XTTS in un worker
        # isolato: il caricamento lento non blocca il ciclo principale.
        # Deve essere attiva anche su macOS, altrimenti la configurazione
        # voicepack ricade sempre su Piper/say e non usa la voce creata.
        # Per disabilitarla manualmente: JARVIS_XTTS_LIVE=0.
        default_xtts_live = "1"
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

            # Non scegliamo una voce italiana qualsiasi: potrebbe essere femminile.
            # Se nessuna voce maschile nota e installata, restituiamo None e
            # lasciamo che Jarvis segnali il fallback invece di usare Alice.

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
        # Windows non dispone di afplay/aplay: usa il player WAV integrato.
        if platform.system() == "Windows":
            try:
                import winsound
                winsound.PlaySound(file_audio, winsound.SND_FILENAME)
                return True
            except (OSError, RuntimeError):
                return False

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
        # I WAV pre-generati non rispettano il parametro velocita: sotto 0.9
        # li saltiamo per provare XTTS con la velocita configurata o il fallback lento.
        if self.velocita < 0.9:
            return False
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
        """Fallback di sistema solo se esiste una voce esplicitamente selezionata.

        Se la voce scelta non è disponibile, prova la voce italiana maschile
        rilevata all'avvio. Non usa mai la voce predefinita non configurata.
        """
        if platform.system() == "Darwin" and shutil.which("say"):
            rate = self.rate_cinematico if self.pausa_cinematica else int(170 * self.velocita)
            comandi = []
            # Usiamo esclusivamente voci esplicitamente selezionate e note come
            # maschili. Non invochiamo "say" senza -v: macOS potrebbe scegliere
            # una voce predefinita femminile, contro la preferenza di Jarvis.
            if voce_forzata:
                comandi.append(["say", "-v", voce_forzata, "-r", str(rate), str(testo)])
            if self.voce_sistema and self.voce_sistema != voce_forzata:
                comandi.append(["say", "-v", self.voce_sistema, "-r", str(rate), str(testo)])

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

        if platform.system() == "Windows" and shutil.which("powershell.exe"):
            # Usa il sintetizzatore vocale integrato in Windows (System.Speech).
            # Il testo viaggia come Base64 UTF-8 per preservare accenti e caratteri.
            testo_base64 = base64.b64encode(
                str(testo).encode("utf-8")
            ).decode("ascii")
            script = (
                "$ErrorActionPreference='Stop'; "
                "Add-Type -AssemblyName System.Speech; "
                "$b=[Console]::In.ReadToEnd().Trim(); "
                "$text=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($b)); "
                "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$v=$s.GetInstalledVoices() | Where-Object { "
                "$_.Enabled -and $_.VoiceInfo.Culture.Name -like 'it-*' } | "
                "Select-Object -First 1; "
                "if ($v) { $s.SelectVoice($v.VoiceInfo.Name) }; "
                "$s.Volume=100; $s.Speak($text); $s.Dispose()"
            )
            try:
                risultato = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-NonInteractive",
                     "-ExecutionPolicy", "Bypass", "-Command", script],
                    input=testo_base64,
                    capture_output=True,
                    text=True,
                    encoding="ascii",
                    timeout=60,
                    check=False,
                )
                if risultato.returncode == 0:
                    return True
                dettaglio = (risultato.stderr or risultato.stdout or "").strip()
                print(f"⚠️ Sintesi Windows non riuscita: {dettaglio or 'errore senza dettagli'}")
            except (OSError, subprocess.SubprocessError) as errore:
                print(f"⚠️ Sintesi Windows non disponibile: {errore}")
            return False

        return False

    def parla(self, testo):
        if not self.attivo or not str(testo or "").strip():
            return False

        # La sintesi di sistema gestisce meglio un unico flusso continuo:
        # rimuoviamo a capo e spazi ripetuti che possono creare pause spezzate.
        testo = " ".join(str(testo).strip().split())

        try:
            # Non forzare mai voci di sistema (come Alice) per parole specifiche:
            # la pronuncia corretta va applicata al motore vocale creato per Jarvis.
            if self._parla_con_voce_clonata(testo):
                return True

            # Prima scelta: frase gia preparata con XTTS, riproduzione immediata.
            if self._parla_con_voicepack(testo):
                return True

            # XTTS live deve essere esplicitamente abilitato.
            # Su macOS/High Sierra una frase contenente "blu" non deve
            # avviare da sola un worker lento: la risposta potrebbe restare
            # in attesa del modello invece di usare subito "say".
            # La guida fonetica resta disponibile quando XTTS live e attivo.
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

            # Quando Piper e selezionato e disponibile, deve essere provato anche
            # su macOS: altrimenti Jarvis resta sempre sulla voce di sistema e
            # non usa mai il modello italiano Riccardo.
            if self._parla_con_piper(testo):
                return True

            voce_sir = self._voce_per_sir(testo)
            return self._parla_con_sistema(testo, voce_forzata=voce_sir)

        except Exception as errore:
            print(f"⚠️ Errore sintesi vocale: {errore}")
            return False

    @staticmethod
    def _voce_per_sir(testo):
        """Restituisce una voce inglese solo per la parola Sir isolata."""
        if re.search(r"(?i)\bsir\b", str(testo)):
            return "Daniel"
        return None


    def avvia(self):
        """Attiva la sintesi vocale senza obbligare la presenza di un backend."""
        self.attivo = True
        return True

    def ferma(self):
        """Disattiva la sintesi vocale e impedisce ulteriori riproduzioni."""
        self.attivo = False
        return True

    def stato(self):
        """Restituisce lo stato della sintesi e la disponibilità dei backend."""
        return {
            "nome": self.nome,
            "attivo": self.attivo,
            "motore": self.motore,
            "voce": self.voce,
            "voce_sistema": self.voce_sistema,
            "piper_disponibile": self._piper_disponibile(),
            "campione_voce_locale": bool(self.voce_riferimento),
            "xtts_attivo": self.xtts_attivo,
            "xtts_live": self.xtts_live,
        }
