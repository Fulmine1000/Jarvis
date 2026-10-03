import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile

from voce.elevenlabs import ElevenLabsVoce

try:
    from voce.tts import TextToSpeech
except ImportError:
    TextToSpeech = None


class SintesiVocale:
    """Motore vocale ufficiale di Jarvis con Piper e fallback di sistema."""

    def __init__(self, config=None):
        self.nome = "Sintesi Vocale"
        self.attivo = True
        self.config = config

        self.motore = os.environ.get("JARVIS_VOICE_PROVIDER", "piper").strip().lower()
        self.voce_clonata = ElevenLabsVoce()
        self._voicepack_tts = None
        self._voicepack_tts_attempted = False
        self._base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.modello = os.path.join(
            self._base_dir,
            "voce",
            "modelli",
            "it_IT-riccardo-x_low.onnx",
        )
        self.voce = "Jarvis"
        self.voce_sistema = None
        self.velocita = 1.0
        self.volume = 100
        self.stile = "Jarvis"

        if config:
            voce_config = config.sezione("voce")
            self.motore = voce_config.get("motore", self.motore)
            modello_config = voce_config.get("modello", self.modello)
            self.modello = self._percorso_modello(modello_config)
            self.velocita = float(voce_config.get("velocita", self.velocita))
            self.volume = int(voce_config.get("volume", self.volume))
            self.stile = voce_config.get("stile", self.stile)
            self.voce = voce_config.get("voce", self.voce)

        # La variabile d'ambiente può selezionare il provider senza modificare config/config.json.
        self.motore = os.environ.get("JARVIS_VOICE_PROVIDER", self.motore).strip().lower()
        # Il campione locale viene scoperto automaticamente.
        self.voce_riferimento = self._trova_campione_locale()
        self.voce_sistema = self._trova_voce_italiana()

    def _trova_campione_locale(self):
        """Trova il campione WAV di Jarvis senza configurazione manuale."""
        candidati = []
        riferimento = os.environ.get("JARVIS_VOICE_REFERENCE", "").strip()
        if riferimento:
            candidati.append(os.path.expanduser(riferimento))

        nome = "jarvis-are-you-there-at-your-service-sir.wav"
        candidati.extend([
            os.path.join(os.path.expanduser("~"), "Desktop", nome),
            os.path.join(self._base_dir, "voce", "campioni", nome),
            os.path.join(self._base_dir, "voce", nome),
        ])

        for percorso in candidati:
            percorso = os.path.abspath(percorso)
            if os.path.isfile(percorso) and percorso.lower().endswith(".wav"):
                return percorso
        return None

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

    def _percorso_modello(self, modello):
        """Rende assoluto il percorso del modello rispetto alla repository."""
        percorso = os.path.expanduser(str(modello))
        if os.path.isabs(percorso):
            return percorso
        return os.path.normpath(os.path.join(self._base_dir, percorso))

    def _trova_piper(self):
        """Trova Piper anche quando Jarvis viene avviato da un'altra cartella."""
        trovato = shutil.which("piper")
        if trovato:
            return trovato

        candidato = os.path.join(sys.prefix, "bin", "piper")
        if os.path.isfile(candidato) and os.access(candidato, os.X_OK):
            return candidato

        locale = os.path.join(
            self._base_dir,
            "voce",
            "bin",
            "piper",
        )
        if os.path.isfile(locale) and os.access(locale, os.X_OK):
            return locale

        return None

    def _piper_disponibile(self):
        return (
            self.motore.lower() == "piper"
            and self._trova_piper() is not None
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

    def _parla_con_voce_clonata(self, testo):
        """Sintetizza con la voce clonata configurata, se disponibile."""
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

    def _parla_con_voicepack(self, testo):
        """Usa il motore TTS locale del Voice Pack con il campione WAV.

        Il motore viene inizializzato solo quando serve, così la presenza del
        modulo non rallenta l'avvio di Jarvis su macOS meno recenti.
        """
        if TextToSpeech is None:
            return False

        if self._voicepack_tts_attempted and self._voicepack_tts is None:
            return False

        if self._voicepack_tts is None:
            self._voicepack_tts_attempted = True
            try:
                riferimento = self.voce_riferimento
                self._voicepack_tts = TextToSpeech(
                    language="it_IT",
                    speed=self.velocita,
                    pitch=0.8,
                    reference_wav=riferimento,
                    use_voice_clone=True,
                )
            except Exception:
                self._voicepack_tts = None
                return False

        try:
            return bool(self._voicepack_tts.synthesize_and_play(testo))
        except Exception:
            return False

    def _parla_con_piper(self, testo):
        """Sintetizza e riproduce il testo tramite Piper."""
        if not self._piper_disponibile():
            return False

        percorso = None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as file_audio:
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

            # Alcune build macOS di Piper usano librerie locali accanto
            # all'eseguibile. Le rendiamo esplicitamente visibili al processo
            # figlio, mantenendo compatibilita con le build che usano gia @rpath.
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
                print("⚠️ Piper ha terminato senza produrre un file WAV valido.")
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

    def _contiene_appellativo_sir(self, testo):
        """Rileva la parola intera 'Sir' senza toccare parole più lunghe."""
        return re.search(r"(?<!\w)Sir(?!\w)", str(testo)) is not None

    def _parla_sir_inglese(self, testo):
        """Pronuncia 'Sir' con una voce inglese, lasciando il resto in italiano.

        Questa modalità serve a ottenere la pronuncia inglese del campione
        originale di Jarvis. La voce inglese viene usata solo per la parola
        'Sir'; il resto della frase continua con la voce italiana.
        """
        if platform.system() != "Darwin" or not shutil.which("say"):
            return False

        match = re.search(r"(?<!\w)Sir(?!\w)", str(testo))
        if not match:
            return False

        voci_inglesi = []
        try:
            risultato = subprocess.run(
                ["say", "-v", "?"],
                capture_output=True,
                text=True,
                check=False,
            )
            if risultato.returncode == 0:
                for riga in risultato.stdout.splitlines():
                    parti = riga.strip().split()
                    if not parti:
                        continue
                    nome = parti[0]
                    if "en_GB" in riga:
                        voci_inglesi.append(nome)

                for preferita in ("Daniel", "Oliver", "Arthur"):
                    if preferita in voci_inglesi:
                        voce = preferita
                        break
                else:
                    voce = voci_inglesi[0] if voci_inglesi else None
            else:
                voce = None
        except (OSError, subprocess.SubprocessError):
            voce = None

        if not voce:
            return False

        prima = str(testo)[:match.start()].strip()
        dopo = str(testo)[match.end():].strip()

        try:
            if prima:
                if not self._parla_con_voce_clonata(prima):
                    if not self._parla_con_piper(prima):
                        self._parla_con_sistema(prima)

            subprocess.run(
                ["say", "-v", voce, "-r", str(int(145 * self.velocita)), "Sir"],
                check=False,
            )

            if dopo:
                if not self._parla_con_voce_clonata(dopo):
                    if not self._parla_con_piper(dopo):
                        self._parla_con_sistema(dopo)

            return True
        except (OSError, subprocess.SubprocessError):
            return False

    def _parla_con_sistema(self, testo):
        """Usa il motore vocale integrato nel sistema operativo."""
        if platform.system() == "Darwin" and shutil.which("say"):
            voce = self.voce_sistema
            testo_voce = str(testo)

            if voce:
                try:
                    risultato = subprocess.run(
                        [
                            "say",
                            "-v",
                            voce,
                            "-r",
                            str(int(170 * self.velocita)),
                            testo_voce,
                        ],
                        check=False,
                    )
                    if risultato.returncode == 0:
                        return True
                except (OSError, subprocess.SubprocessError):
                    pass

            try:
                risultato = subprocess.run(
                    [
                        "say",
                        "-r",
                        str(int(170 * self.velocita)),
                        testo_voce,
                    ],
                    check=False,
                )
                return risultato.returncode == 0
            except (OSError, subprocess.SubprocessError):
                return False

        if platform.system() == "Linux" and shutil.which("espeak"):
            try:
                risultato = subprocess.run(
                    ["espeak", "-v", "it", testo],
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
            # "Sir" non deve bypassare il motore vocale configurato.
            # In precedenza questa parola attivava direttamente say di macOS,
            # facendo sembrare che Jarvis usasse sempre la voce predefinita.
            # Ora l'intera frase segue lo stesso provider scelto per Jarvis.

            if self._parla_con_voce_clonata(testo):
                return True

            if self._parla_con_piper(testo):
                return True

            # Se Piper non è disponibile, prova il Voice Pack locale con il
            # campione WAV prima di ricorrere alla voce di sistema.
            if self._parla_con_voicepack(testo):
                return True

            if self._parla_con_sistema(testo):
                return True

        except (OSError, ValueError, subprocess.SubprocessError):
            pass

        print(f"[JARVIS] {testo}")
        return True

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
            "voicepack_tts_disponibile": TextToSpeech is not None,
            "voicepack_tts_inizializzato": self._voicepack_tts is not None,
            "campione_voce_locale": bool(self.voce_riferimento),
            "percorso_campione_voce": self.voce_riferimento,
        }
