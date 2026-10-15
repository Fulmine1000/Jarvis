import unittest
from types import SimpleNamespace

from voce.motore_ascolto import MotoreAscolto


class TestFiltroEcoJarvis(unittest.TestCase):
    def setUp(self):
        self.motore = MotoreAscolto(SimpleNamespace(config=None, kernel=None))

    def test_ignora_risposta_senza_wake_word(self):
        self.assertTrue(self.motore._e_eco_jarvis("sono qui"))

    def test_ignora_risposta_con_wake_word_riconosciuta(self):
        self.assertTrue(self.motore._e_eco_jarvis("jarvis sono qui"))
        self.assertTrue(self.motore._e_eco_jarvis("jarvis qui"))

    def test_ignora_risposta_con_varianti_wake_word(self):
        self.assertTrue(self.motore._e_eco_jarvis("hey jarvis sono qui"))
        self.assertTrue(self.motore._e_eco_jarvis("ehi jarvis sono qui"))
        self.assertTrue(self.motore._e_eco_jarvis("hey jarvis qui"))
        self.assertTrue(self.motore._e_eco_jarvis("ehi jarvis qui"))

    def test_non_scarta_comandi_reali(self):
        self.assertFalse(self.motore._e_eco_jarvis("jarvis che ore sono"))
        self.assertFalse(self.motore._e_eco_jarvis("sono qui vicino"))

    def test_normalizza_wake_word_trascritta_come_barry_jiu_su(self):
        self.assertEqual(
            self.motore._normalizza_trascrizione("barry jiu su"),
            "jarvis",
        )

    def test_normalizza_comando_dopo_wake_word_trascritta_male(self):
        self.assertEqual(
            self.motore._normalizza_trascrizione("barry jiu su che ore sono"),
            "jarvis che ore sono",
        )

    def test_non_corregge_frasi_solo_simili_alla_wake_word(self):
        self.assertEqual(
            self.motore._normalizza_trascrizione("Barry Jiu Su vicino"),
            "jarvis vicino",
        )


if __name__ == "__main__":
    unittest.main()
