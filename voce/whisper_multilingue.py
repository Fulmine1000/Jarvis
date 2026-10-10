"""Riconoscimento multilingue offline tramite whisper.cpp.

Il modulo riceve blocchi PCM int16 mono e segmenta le frasi con una breve
pausa. Conserva un pre-roll configurabile per non perdere l'attacco delle
parole, cosa particolarmente importante per la wake word "Jarvis".
"""
from __future__ import annotations

import math
import os
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path


class WhisperMultilingue:
    """Adattatore a whisper.cpp con segmentazione audio basata sul silenzio."""

    def __init__(
        self,
        modello=None,
        eseguibile=None,
        sample_rate=16000,
        timeout=90,
        silenzio_blocchi=2,
        soglia_rms=420,
        pre_roll_blocchi=3,
    ):
        self.nome = "Whisper multilingue (whisper.cpp)"
        self.sample_rate = int(sample_rate)
        self.timeout = max(10, int(timeout))
        self.silenzio_blocchi = max(1, int(silenzio_blocchi))
        self.soglia_rms = max(50, int(soglia_rms))
        self.pre_roll_blocchi = max(0, int(pre_roll_blocchi))
        base = Path(__file__).resolve().parent.parent
        self.modello = str(Path(modello).expanduser()) if modello else str(
            base / "motore_ia" / "whisper.cpp" / "models" / "ggml-base.bin"
        )
        self.eseguibile_configurato = str(eseguibile or "").strip()
        self.eseguibile = None
        self.attivo = False
        self.ultimo_errore = None
        self._in_parlato = False
        self._blocchi = []
        self._blocchi_silenzio = 0
        self._pre_roll = []

    def _trova_eseguibile(self):
        candidati = []
        if self.eseguibile_configurato:
            candidati.append(self.eseguibile_configurato)
        env = os.environ.get("JARVIS_WHISPER_CPP")
        if env:
            candidati.append(env)
        base = Path(__file__).resolve().parent.parent
        candidati.extend([
            str(base / "motore_ia" / "whisper.cpp" / "build" / "bin" / "whisper-cli"),
            str(base / "motore_ia" / "whisper.cpp" / "build" / "bin" / "main"),
            str(base / "motore_ia" / "whisper.cpp" / "main"),
        ])
        for nome in ("whisper-cli", "main"):
            trovato = shutil.which(nome)
            if trovato:
                candidati.append(trovato)
        for candidato in candidati:
            percorso = os.path.expanduser(candidato)
            if os.path.isfile(percorso) and os.access(percorso, os.X_OK):
                return percorso
        return None

    def avvia(self):
        self.eseguibile = self._trova_eseguibile()
        if not self.eseguibile:
            self.ultimo_errore = (
                "whisper.cpp non trovato. Eseguire "
                "bash scripts/prepara_riconoscimento_multilingue.sh"
            )
            return False
        if not os.path.isfile(self.modello):
            self.ultimo_errore = (
                f"Modello multilingue non trovato: {self.modello}. "
                "Eseguire bash scripts/prepara_riconoscimento_multilingue.sh"
            )
            return False
        self.attivo = True
        self.ultimo_errore = None
        self._reset_segmento()
        return True

    @staticmethod
    def _rms(audio):
        if not audio:
            return 0
        campioni = len(audio) // 2
        if campioni <= 0:
            return 0
        valori = struct.unpack("<" + "h" * campioni, audio[:campioni * 2])
        return int(math.sqrt(sum(v * v for v in valori) / campioni))

    def _conserva_pre_roll(self, audio):
        if self.pre_roll_blocchi <= 0:
            self._pre_roll = []
            return
        self._pre_roll.append(audio)
        if len(self._pre_roll) > self.pre_roll_blocchi:
            del self._pre_roll[:-self.pre_roll_blocchi]

    def riconosci(self, audio):
        """Restituisce una trascrizione quando la frase termina con una pausa."""
        if not self.attivo or not audio:
            return None

        # I blocchi silenziosi precedenti all'inizio della voce vengono
        # conservati per includere l'attacco della prima parola.
        livello = self._rms(audio)
        if not self._in_parlato:
            if livello < self.soglia_rms:
                self._conserva_pre_roll(audio)
                return None

            self._in_parlato = True
            self._blocchi = self._pre_roll[:] + [audio]
            self._pre_roll = []
            self._blocchi_silenzio = 0
            return None

        self._blocchi.append(audio)
        if livello < self.soglia_rms:
            self._blocchi_silenzio += 1
        else:
            self._blocchi_silenzio = 0

        if self._blocchi_silenzio < self.silenzio_blocchi:
            return None

        blocchi = self._blocchi[:]
        self._reset_segmento()

        # Ignora rumori brevissimi, ma consenti wake word e risposte brevi.
        if sum(map(len, blocchi)) < int(self.sample_rate * 2 * 0.30):
            return None
        return self._trascrivi(blocchi)

    def _trascrivi(self, blocchi):
        wav_path = None
        output_base = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wav_path = tmp.name
            output_base = wav_path[:-4] + "_trascrizione"
            with wave.open(wav_path, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(self.sample_rate)
                wav.writeframes(b"".join(blocchi))

            comando = [
                self.eseguibile, "-m", self.modello, "-f", wav_path,
                "-l", "auto", "-nt", "-np", "-t", "2",
                "-otxt", "-of", output_base,
            ]
            risultato = subprocess.run(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=self.timeout,
                check=False,
            )
            testo_path = output_base + ".txt"
            if os.path.isfile(testo_path):
                with open(testo_path, "r", encoding="utf-8", errors="replace") as file:
                    testo = file.read().strip()
                if testo:
                    if risultato.returncode == 0:
                        self.ultimo_errore = None
                    else:
                        self.ultimo_errore = (
                            f"whisper.cpp ha restituito il codice {risultato.returncode}"
                        )
                    return testo

            # Alcune build stampano il testo direttamente su stdout.
            testo = (risultato.stdout or "").strip()
            if risultato.returncode == 0 and testo:
                righe = [r.strip() for r in testo.splitlines() if r.strip()]
                testo = " ".join(righe)
                if testo and not testo.startswith(("whisper_", "main:")):
                    self.ultimo_errore = None
                    return testo

            dettaglio = (risultato.stderr or "").strip()
            self.ultimo_errore = (
                f"whisper.cpp non ha prodotto una trascrizione "
                f"(codice {risultato.returncode})"
                + (f": {dettaglio[-400:]}" if dettaglio else "")
            )
            return None
        except subprocess.TimeoutExpired:
            self.ultimo_errore = (
                f"Timeout di whisper.cpp dopo {self.timeout} secondi. "
                "Sul Mac Intel prova a usare un modello più piccolo."
            )
            return None
        except (OSError, subprocess.SubprocessError, ValueError) as errore:
            self.ultimo_errore = str(errore)
            return None
        finally:
            for percorso in (
                wav_path,
                (output_base + ".txt") if output_base else None,
            ):
                if percorso:
                    try:
                        os.remove(percorso)
                    except OSError:
                        pass

    def _reset_segmento(self):
        self._in_parlato = False
        self._blocchi = []
        self._blocchi_silenzio = 0
        self._pre_roll = []

    def ferma(self):
        self.attivo = False
        self._reset_segmento()
        return True

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo" if self.attivo else "spento",
            "lingua": "auto (multilingue)",
            "modello": self.modello,
            "eseguibile": self.eseguibile,
            "pre_roll_blocchi": self.pre_roll_blocchi,
            "ultimo_errore": self.ultimo_errore,
        }
