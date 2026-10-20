import contextlib
import io
import os
import subprocess
import threading
import unittest
from unittest.mock import Mock, patch

from voce.tts import TextToSpeech


class TestXTTSWorkerDiagnostics(unittest.TestCase):
    def test_richiesta_concorrente_viene_accodata(self):
        tts = TextToSpeech.__new__(TextToSpeech)
        tts._xtts_lock = threading.Lock()
        tts._xtts_busy = True
        tts._xtts_pending_text = []

        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertTrue(tts._avvia_xtts_background("Seconda risposta"))

        self.assertEqual(tts._xtts_pending_text, ["Seconda risposta"])
        self.assertIn("accodata", output.getvalue())

    def test_worker_registra_codice_uscita_e_stderr_e_fa_fallback(self):
        tts = TextToSpeech.__new__(TextToSpeech)
        tts.reference_wav = "/tmp/campione.wav"
        tts.language = "it_IT"
        tts.xtts_timeout = 30
        tts.cinematic_voice = False
        tts._xtts_lock = threading.Lock()
        tts._xtts_pending_text = []
        tts._xtts_busy = True
        tts._xtts_process = None
        fallback = Mock()

        result = subprocess.CompletedProcess(
            args=["python", "-m", "voce.xtts_worker"],
            returncode=1,
            stdout="Avvio worker",
            stderr="ImportError: torch non disponibile",
        )
        with patch("voce.tts.os.path.isfile", return_value=True), \
             patch("voce.tts.subprocess.run", return_value=result), \
             patch.object(tts, "_fallback_background", fallback), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            tts._worker_xtts("Salve Simone")

        self.assertIn("exit_code=1", output.getvalue())
        self.assertIn("ImportError: torch non disponibile", output.getvalue())
        fallback.assert_called_once_with("Salve Simone")
        self.assertFalse(tts._xtts_busy)


if __name__ == "__main__":
    unittest.main()
