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

    def test_ignora_parola_isolata_in_segmento_separato_dopo_wake_word(self):
        prima = self.wake.controlla("jarvis")
        self.assertTrue(prima["attivato"])
        self.assertEqual(prima["comando"], "")

        risultato = self.wake.controlla("su")
        self.assertTrue(risultato["attivato"])
        self.assertEqual(risultato["comando"], "")
        self.assertTrue(risultato["parziale"])
        self.assertTrue(self.wake.attivo)

    def test_accetta_comando_singolo_affidabile_in_segmento_separato(self):
        self.wake.controlla("jarvis")
        risultato = self.wake.controlla("aiuto")
        self.assertEqual(risultato["comando"], "aiuto")
        self.assertNotIn("parziale", risultato)

    def test_accetta_comando_mult_parola_in_segmento_separato(self):
        self.wake.controlla("jarvis")
        risultato = self.wake.controlla("che ore sono")
        self.assertEqual(risultato["comando"], "che ore sono")
        self.assertNotIn("parziale", risultato)

    def test_ignora_trascrizione_senza_wake_word_in_standby(self):
        risultato = self.wake.controlla("che ore sono")
        self.assertFalse(risultato["attivato"])
        self.assertEqual(risultato["comando"], "")
        self.assertFalse(self.wake.attivo)

    def test_ignora_trascrizione_vosk_errata_senza_wake_word(self):
        risultato = self.wake.controlla("barry jiu su")
        self.assertFalse(risultato["attivato"])
        self.assertEqual(risultato["comando"], "")
        self.assertFalse(self.wake.attivo)


if __name__ == "__main__":
    unittest.main()
