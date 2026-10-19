import unittest
from types import SimpleNamespace
from unittest.mock import patch

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
            "barry jiu su vicino",
        )

    def test_prefisso_incompleto_viene_distinto_dalla_wake_word(self):
        # "Ehi Jarvis" può essere diviso da Vosk in due risultati.
        # Il motore deve riconoscere il prefisso da solo e non avviare la sintesi.
        self.assertTrue(self.motore._e_prefisso_attivazione_incompleto("ehi"))
        self.assertTrue(self.motore._e_prefisso_attivazione_incompleto("HEY"))
        self.assertFalse(self.motore._e_prefisso_attivazione_incompleto("jarvis"))
        self.assertFalse(self.motore._e_prefisso_attivazione_incompleto("ehi jarvis"))


    def test_ciclo_non_rallenta_la_coda_con_blocchi_senza_trascrizione(self):
        class ListenerFinto:
            attivo = True

        class VoceFinta:
            def __init__(self):
                self.config = None
                self.kernel = SimpleNamespace(hud=None, logger=None)
                self.ascoltatore = ListenerFinto()
                self.ascolto_attivo = True
                self.chiamate = 0

            def ascolta_comando(self):
                self.chiamate += 1
                if self.chiamate >= 3:
                    self.ascolto_attivo = False
                return None

        voce = VoceFinta()
        motore = MotoreAscolto(voce)
        motore.attivo = True

        # Ogni None rappresenta un blocco audio senza una trascrizione finale.
        # Il ciclo deve consumare subito il blocco successivo, senza pause
        # artificiali che porterebbero la coda audio a saturazione.
        with patch("voce.motore_ascolto.time.sleep") as dormi:
            motore.ciclo()

        self.assertEqual(voce.chiamate, 3)
        dormi.assert_not_called()


if __name__ == "__main__":
    unittest.main()
