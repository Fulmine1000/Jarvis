"""Regressioni per risultati Vosk malformati o di tipo inatteso."""

import unittest
from unittest.mock import Mock

from voce.riconoscimento import RiconoscitoreVoce


class _RiconoscitoreConRisultato:
    def __init__(self, risultato):
        self.risultato = risultato

    def AcceptWaveform(self, audio):
        return True

    def Result(self):
        return self.risultato


class TestRisultatoVoskNonValido(unittest.TestCase):
    def _crea_riconoscitore(self, risultato):
        riconoscitore = RiconoscitoreVoce()
        riconoscitore.attivo = True
        riconoscitore.backend_attivo = "vosk"
        riconoscitore.modello = object()
        riconoscitore.riconoscitore = _RiconoscitoreConRisultato(risultato)
        riconoscitore._KaldiRecognizer = Mock(return_value=Mock())
        return riconoscitore

    def test_json_malformato_non_blocca_e_reinizializza_vosk(self):
        riconoscitore = self._crea_riconoscitore("{\n  'text': 'jarvis'\n}")

        self.assertIsNone(riconoscitore.riconosci(b"\\x00\\x00"))
        self.assertIn("Risultato JSON Vosk non valido", riconoscitore.ultimo_errore)
        self.assertIn("riconoscitore reimpostato", riconoscitore.ultimo_errore)
        riconoscitore._KaldiRecognizer.assert_called_once()
        self.assertTrue(riconoscitore.attivo)

    def test_json_valido_ma_non_oggetto_non_blocca(self):
        riconoscitore = self._crea_riconoscitore("[]")

        self.assertIsNone(riconoscitore.riconosci(b"\\x00\\x00"))
        self.assertIn("era atteso un oggetto JSON", riconoscitore.ultimo_errore)
        riconoscitore._KaldiRecognizer.assert_called_once()
        self.assertTrue(riconoscitore.attivo)

    def test_risultato_valido_viene_riconosciuto(self):
        riconoscitore = self._crea_riconoscitore('{"text": "jarvis che ore sono", "result": []}')

        self.assertEqual(riconoscitore.riconosci(b"\\x00\\x00"), "jarvis che ore sono")
        self.assertIsNone(riconoscitore.ultimo_errore)
        self.assertEqual(riconoscitore.ultima_trascrizione_grezza, "jarvis che ore sono")


if __name__ == "__main__":
    unittest.main()
