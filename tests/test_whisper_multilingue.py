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

    def test_pre_roll_conserva_audio_prima_della_prima_parola(self):
        motore = WhisperFinto(
            soglia_rms=300,
            silenzio_blocchi=2,
            pre_roll_blocchi=3,
        )
        motore.attivo = True
        self.assertIsNone(motore.riconosci(blocco(0)))
        self.assertIsNone(motore.riconosci(blocco(0)))
        self.assertIsNone(motore.riconosci(blocco(1200)))
        self.assertIsNone(motore.riconosci(blocco(900)))
        self.assertIsNone(motore.riconosci(blocco(0)))
        self.assertEqual(
            motore.riconosci(blocco(0)),
            "Hey Jarvis what time is it",
        )
        self.assertEqual(len(motore.blocchi_trascritti), 6)
        self.assertEqual(motore.blocchi_trascritti[0], blocco(0))
        self.assertEqual(motore.blocchi_trascritti[1], blocco(0))

    def test_pre_roll_rispetta_il_limite_configurato(self):
        motore = WhisperFinto(pre_roll_blocchi=2)
        motore.attivo = True
        for _ in range(5):
            self.assertIsNone(motore.riconosci(blocco(0)))
        self.assertEqual(len(motore._pre_roll), 2)

    def test_non_trascrive_il_solo_silenzio(self):
        motore = WhisperFinto()
        motore.attivo = True
        for _ in range(4):
            self.assertIsNone(motore.riconosci(blocco(0)))
        self.assertFalse(hasattr(motore, "blocchi_trascritti"))


if __name__ == "__main__":
    unittest.main()
