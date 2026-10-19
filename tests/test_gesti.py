"""Test senza camera per il modulo di controllo gestuale."""
import unittest

from interfaccia.gesti import ControlloGesti


class TestControlloGesti(unittest.TestCase):
    def test_dita_alzate(self):
        # Mock leggero dei landmark richiesti dal classificatore.
        class Punto:
            def __init__(self, x, y):
                self.x, self.y = x, y

        punti = [Punto(0.5, 0.5) for _ in range(21)]
        for punta, articolazione in ((8, 6), (12, 10), (16, 14), (20, 18)):
            punti[punta].y = 0.1
            punti[articolazione].y = 0.4
        punti[4].x, punti[2].x = 0.9, 0.5
        self.assertEqual(ControlloGesti._dita_alzate(punti), 5)

    def test_distanza(self):
        class Punto:
            def __init__(self, x, y):
                self.x, self.y = x, y
        self.assertAlmostEqual(
            ControlloGesti._distanza(Punto(0, 0), Punto(3, 4)), 5.0
        )

    def test_callback_consegna_gesto(self):
        ricevuti = []
        gesti = ControlloGesti(ricevuti.append)
        gesti._emetti("pizzico")
        self.assertEqual(ricevuti, ["pizzico"])


if __name__ == "__main__":
    unittest.main()
