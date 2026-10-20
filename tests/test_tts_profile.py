"""Test del profilo audio predefinito per XTTS su hardware lento."""

import os
import unittest
from unittest.mock import patch

from voce.tts import TextToSpeech


class TestProfiloVoceXTTS(unittest.TestCase):
    def test_effetti_cinematici_neutri_per_default(self):
        variabili = {
            "JARVIS_CINEMATIC_PITCH": "",
            "JARVIS_CINEMATIC_RATE": "",
            "JARVIS_CINEMATIC_VOICE": "1",
            "JARVIS_VOICE_REFERENCE": "",
        }
        with patch.dict(os.environ, variabili):
            os.environ.pop("JARVIS_CINEMATIC_PITCH", None)
            os.environ.pop("JARVIS_CINEMATIC_RATE", None)
            tts = TextToSpeech(use_voice_clone=False)

        self.assertTrue(tts.cinematic_voice)
        self.assertEqual(tts.pitch_steps, 0.0)
        self.assertEqual(tts.time_rate, 1.0)

    def test_effetti_possono_essere_configurati_dall_ambiente(self):
        with patch.dict(
            os.environ,
            {
                "JARVIS_CINEMATIC_PITCH": "-0.5",
                "JARVIS_CINEMATIC_RATE": "0.98",
                "JARVIS_CINEMATIC_VOICE": "1",
                "JARVIS_VOICE_REFERENCE": "",
            },
        ):
            tts = TextToSpeech(use_voice_clone=False)

        self.assertEqual(tts.pitch_steps, -0.5)
        self.assertEqual(tts.time_rate, 0.98)


if __name__ == "__main__":
    unittest.main()
