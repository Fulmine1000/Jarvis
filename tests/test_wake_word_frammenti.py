import unittest

from voce.wake_word import WakeWordJarvis


class TestWakeWordFrammenti(unittest.TestCase):
    def setUp(self):
        self.wake = WakeWordJarvis(timeout=10)

    def test_ignora_parola_isolata_non_affidabile_dopo_wake_word(self):
        risultato = self.wake.controlla("jarvis su")
        self.assertTrue(risultato["attivato"])
        self.assertEqual(risultato["comando"], "")
        self.assertTrue(risultato["parziale"])
        self.assertTrue(self.wake.attivo)

    def test_non_esegue_parola_isolata_riconosciuta_male(self):
        risultato = self.wake.controlla("jarvis georges")
        self.assertEqual(risultato["comando"], "")
        self.assertTrue(risultato["parziale"])

    def test_conserva_comando_mult_parola(self):
        risultato = self.wake.controlla("jarvis che ore sono")
        self.assertEqual(risultato["comando"], "che ore sono")
        self.assertNotIn("parziale", risultato)

    def test_conserva_comandi_singola_parola_in_allowlist(self):
        risultato = self.wake.controlla("jarvis aiuto")
        self.assertEqual(risultato["comando"], "aiuto")

    def test_wake_word_da_sola_non_e_un_comando(self):
        risultato = self.wake.controlla("jarvis")
        self.assertTrue(risultato["attivato"])
        self.assertEqual(risultato["comando"], "")
        self.assertNotIn("parziale", risultato)


if __name__ == "__main__":
    unittest.main()
