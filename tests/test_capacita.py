import unittest

from core.capacita import CapacitaJarvis


class TestCapacitaJarvis(unittest.TestCase):
    def setUp(self):
        self.cap = CapacitaJarvis()

    def test_calcolo(self):
        self.assertEqual(self.cap.calcola("2 + 3 * 4"), 14)

    def test_calcolo_non_consentito(self):
        with self.assertRaises(Exception):
            self.cap.calcola("__import__('os').system('echo no')")

    def test_stato(self):
        stato = self.cap.stato()
        self.assertEqual(stato["stato"], "attivo")
        self.assertIn("timer_attivi", stato)

    def test_timer(self):
        risposta = self.cap.timer_avvia(1, "test")
        self.assertIn("Timer test", risposta)
        self.assertIn("test", self.cap.timer)
        self.cap.timer_annulla("test")
        self.assertNotIn("test", self.cap.timer)


if __name__ == "__main__":
    unittest.main()
