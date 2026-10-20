import os
import unittest
from unittest.mock import Mock, patch

from voce.sintesi import SintesiVocale


class TestSintesiXTTSLive(unittest.TestCase):
    def test_xtts_live_attivo_per_default(self):
        with patch.dict(os.environ, {"JARVIS_ENABLE_XTTS": "1"}, clear=False):
            os.environ.pop("JARVIS_XTTS_LIVE", None)
            with patch.object(SintesiVocale, "_trova_campione_locale", return_value=None), \
                 patch.object(SintesiVocale, "_trova_voce_italiana", return_value=None), \
                 patch("voce.sintesi.ElevenLabsVoce"):
                sintesi = SintesiVocale()
        self.assertTrue(sintesi.xtts_live)

    @patch("voce.sintesi.platform.system", return_value="Darwin")
    def test_xtts_live_disattivo_per_default_su_macos(self, _platform):
        with patch.dict(os.environ, {"JARVIS_ENABLE_XTTS": "1"}, clear=False):
            os.environ.pop("JARVIS_XTTS_LIVE", None)
            with patch.object(SintesiVocale, "_trova_campione_locale", return_value=None):
                with patch.object(SintesiVocale, "_trova_voce_italiana", return_value=None):
                    with patch("voce.sintesi.ElevenLabsVoce"):
                        sintesi = SintesiVocale()
        self.assertFalse(sintesi.xtts_live)

    def test_blu_viene_guidato_foneticamente_solo_per_xtts(self):
        self.assertEqual(
            SintesiVocale._testo_per_xtts("Il mio colore preferito è blu."),
            "Il mio colore preferito è blù.",
        )
        self.assertEqual(
            SintesiVocale._testo_per_xtts("BLU e il colore"),
            "blù e il colore",
        )
        self.assertEqual(
            SintesiVocale._testo_per_xtts("Bluetooth è connesso"),
            "Bluetooth è connesso",
        )

    def test_frasi_con_blu_non_usano_cache_potenzialmente_difettosa(self):
        sintesi = SintesiVocale.__new__(SintesiVocale)
        sintesi.xtts_attivo = True
        with patch("voce.sintesi.os.path.isfile") as isfile:
            self.assertFalse(sintesi._parla_con_voicepack("Il mio colore è blu."))
        isfile.assert_not_called()

    @patch("voce.sintesi.platform.system", return_value="Darwin")
    def test_risposta_con_blu_invia_la_guida_fonetica_a_xtts(self, _platform):
        sintesi = SintesiVocale.__new__(SintesiVocale)
        sintesi.attivo = True
        sintesi.motore = "voicepack"
        sintesi.xtts_attivo = True
        sintesi.xtts_live = True
        sintesi.voce_riferimento = "/tmp/campione.wav"
        sintesi.velocita = 0.92
        sintesi._voicepack_tts = None
        sintesi._voicepack_tts_attempted = False

        fake_tts = Mock()
        fake_tts.synthesize_and_play.return_value = True
        with patch.object(SintesiVocale, "_parla_con_voce_clonata", return_value=False), \
             patch.object(SintesiVocale, "_parla_con_voicepack", return_value=False), \
             patch.object(SintesiVocale, "_parla_con_sistema", return_value=False), \
             patch("voce.sintesi.TextToSpeech", return_value=fake_tts):
            self.assertTrue(sintesi.parla("Il mio colore preferito è blu."))

        fake_tts.synthesize_and_play.assert_called_once_with(
            "Il mio colore preferito è blù."
        )


if __name__ == "__main__":
    unittest.main()
