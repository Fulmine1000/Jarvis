import array
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.diagnostica_voce import rms_pcm16, statistiche_pcm16


class TestDiagnosticaVoce(unittest.TestCase):
    def test_statistiche_pcm16_su_blocco_normale(self):
        campioni = array.array("h", [100, -100, 200, -200])
        rms, picco, saturi, totale = statistiche_pcm16(campioni.tobytes())
        self.assertEqual(rms, 158)
        self.assertEqual(picco, 200)
        self.assertEqual(saturi, 0)
        self.assertEqual(totale, 4)
        self.assertEqual(rms_pcm16(campioni.tobytes()), rms)

    def test_rileva_campioni_saturi(self):
        campioni = array.array("h", [0, 32760, -32768, 120])
        _, picco, saturi, totale = statistiche_pcm16(campioni.tobytes())
        self.assertEqual(picco, 32768)
        self.assertEqual(saturi, 2)
        self.assertEqual(totale, 4)

    def test_audio_vuoto_e_byte_dispari(self):
        self.assertEqual(statistiche_pcm16(b""), (0, 0, 0, 0))
        self.assertEqual(statistiche_pcm16(b"\x01"), (0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
