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

    def test_ignora_risposta_con_varianti_wake_word(self):
        self.assertTrue(self.motore._e_eco_jarvis("hey jarvis sono qui"))
        self.assertTrue(self.motore._e_eco_jarvis("ehi jarvis sono qui"))

    def test_non_scarta_comandi_reali(self):
        self.assertFalse(self.motore._e_eco_jarvis("jarvis che ore sono"))
        self.assertFalse(self.motore._e_eco_jarvis("sono qui vicino"))


if __name__ == "__main__":
    unittest.main()
