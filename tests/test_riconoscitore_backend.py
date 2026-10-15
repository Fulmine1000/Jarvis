import unittest
from unittest.mock import Mock, patch

from voce.riconoscimento import RiconoscitoreVoce


class ConfigWhisper:
    def sezione(self, nome):
        if nome != "voce":
            return {}
        return {
            "riconoscimento_multilingue": True,
            "modello_multilingue": "motore_ia/whisper.cpp/models/ggml-base.bin",
            "eseguibile_multilingue": "",
            "timeout_multilingue": 90,
            "sample_rate": 16000,
        }


class TestSelezioneBackendWhisper(unittest.TestCase):
    @patch("voce.whisper_multilingue.WhisperMultilingue")
    def test_whisper_selezionato_diventa_backend_attivo(self, factory):
        whisper = Mock()
        whisper.avvia.return_value = True
        whisper.ultimo_errore = None
        whisper.stato.return_value = {"stato": "attivo"}
        factory.return_value = whisper

        riconoscitore = RiconoscitoreVoce(config=ConfigWhisper())

        self.assertTrue(riconoscitore.avvia())
        self.assertEqual(riconoscitore.backend_attivo, "whisper")
        self.assertEqual(riconoscitore.lingua, "auto")
        self.assertTrue(riconoscitore.attivo)

    @patch("voce.whisper_multilingue.WhisperMultilingue")
    def test_whisper_non_disponibile_non_ricade_su_vosk(self, factory):
        whisper = Mock()
        whisper.avvia.return_value = False
        whisper.ultimo_errore = "whisper.cpp non trovato"
        whisper.stato.return_value = {"stato": "spento"}
        factory.return_value = whisper

        riconoscitore = RiconoscitoreVoce(config=ConfigWhisper())
        riconoscitore._vosk_disponibile = Mock(return_value=True)
        riconoscitore._carica_vosk = Mock(return_value=True)

        self.assertFalse(riconoscitore.avvia())
        self.assertEqual(riconoscitore.backend_attivo, "whisper")
        self.assertFalse(riconoscitore.attivo)
        self.assertEqual(riconoscitore.ultimo_errore, "whisper.cpp non trovato")
        riconoscitore._carica_vosk.assert_not_called()

    @patch("voce.whisper_multilingue.WhisperMultilingue")
    def test_whisper_non_inizializzato_non_usa_vosk(self, factory):
        factory.side_effect = ImportError("dipendenza non disponibile")
        riconoscitore = RiconoscitoreVoce(config=ConfigWhisper())
        riconoscitore._vosk_disponibile = Mock(return_value=True)
        riconoscitore._carica_vosk = Mock(return_value=True)

        self.assertFalse(riconoscitore.avvia())
        self.assertFalse(riconoscitore.attivo)
        riconoscitore._carica_vosk.assert_not_called()


if __name__ == "__main__":
    unittest.main()
