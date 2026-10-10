import unittest

from voce.whisper_multilingue import WhisperMultilingue


def blocco(valore, campioni=8000):
    return (int(valore).to_bytes(2, "little", signed=True)) * campioni


class WhisperFinto(WhisperMultilingue):
    def _trascrivi(self, blocchi):
        self.blocchi_trascritti = blocchi
        return "Hey Jarvis what time is it"


class TestWhisperMultilingue(unittest.TestCase):
    def test_rms_silenzio_e_voce(self):
        self.assertEqual(WhisperMultilingue._rms(blocco(0)), 0)
        self.assertEqual(WhisperMultilingue._rms(blocco(1000)), 1000)

    def test_segmenta_una_frase_dopo_il_silenzio(self):
        motore = WhisperFinto(soglia_rms=300, silenzio_blocchi=2)
        motore.attivo = True
        self.assertIsNone(motore.riconosci(blocco(1200)))
        self.assertIsNone(motore.riconosci(blocco(900)))
        self.assertIsNone(motore.riconosci(blocco(0)))
        risultato = motore.riconosci(blocco(0))
        self.assertEqual(risultato, "Hey Jarvis what time is it")
        self.assertFalse(motore._in_parlato)
        self.assertEqual(len(motore.blocchi_trascritti), 4)

    def test_non_trascrive_il_solo_silenzio(self):
        motore = WhisperFinto()
        motore.attivo = True
        for _ in range(4):
            self.assertIsNone(motore.riconosci(blocco(0)))
        self.assertFalse(hasattr(motore, "blocchi_trascritti"))


if __name__ == "__main__":
    unittest.main()
