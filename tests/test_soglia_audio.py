"""Test per impedire che il rumore quasi silenzioso generi trascrizioni."""

import array
import unittest

from voce.ascoltatore import AscoltatoreVoce


class TestSogliaAudio(unittest.TestCase):
    def setUp(self):
        self.ascoltatore = AscoltatoreVoce(
            frequenza=16000,
            filtro_rumore=False,
            soglia_rms_minima=12,
        )

    def test_blocco_quasi_silenzioso_diventa_silenzio_pcm(self):
        # Un rumore di fondo con RMS inferiore alla soglia deve essere silenziato.
        audio = array.array("h", [5, -5, 4, -4] * 400).tobytes()
        self.ascoltatore.callback(audio, 1600, None, None)
        ricevuto = self.ascoltatore.audio.get_nowait()
        self.assertEqual(ricevuto, bytes(len(audio)))
        self.assertEqual(self.ascoltatore.blocchi_sotto_soglia, 1)
        self.assertEqual(self.ascoltatore.ultimo_rms_uscita, 4)

    def test_voce_sopra_soglia_viene_preservata(self):
        audio = array.array("h", [120, -120, 80, -80] * 400).tobytes()
        self.ascoltatore.callback(audio, 1600, None, None)
        ricevuto = self.ascoltatore.audio.get_nowait()
        self.assertEqual(ricevuto, audio)
        self.assertEqual(self.ascoltatore.blocchi_sotto_soglia, 0)

    def test_soglia_disattivabile(self):
        self.ascoltatore.soglia_rms_minima = 0
        audio = array.array("h", [1, -1] * 800).tobytes()
        self.ascoltatore.callback(audio, 1600, None, None)
        self.assertEqual(self.ascoltatore.audio.get_nowait(), audio)
        self.assertEqual(self.ascoltatore.blocchi_sotto_soglia, 0)


if __name__ == "__main__":
    unittest.main()
