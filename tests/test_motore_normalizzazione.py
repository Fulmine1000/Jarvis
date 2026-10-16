import unittest

from voce.motore_ascolto import MotoreAscolto


class TestNormalizzazioneNelMotore(unittest.TestCase):
    def test_corregge_wake_word_trascritta_male(self):
        self.assertEqual(
            MotoreAscolto._normalizza_trascrizione("barry jiu su"),
            "jarvis",
        )

    def test_corregge_wake_word_e_comando_nella_stessa_frase(self):
        self.assertEqual(
            MotoreAscolto._normalizza_trascrizione("barry jiu su che ore sono"),
            "barry jiu su che ore sono",
        )

    def test_non_corregge_wake_word_dubbia_con_punteggiatura(self):
        self.assertEqual(
            MotoreAscolto._normalizza_trascrizione("Barry Jiu Su, che ore sono?"),
            "barry jiu su, che ore sono?",
        )

    def test_non_riscrive_comandi_normali(self):
        self.assertEqual(
            MotoreAscolto._normalizza_trascrizione("che ore sono"),
            "che ore sono",
        )


if __name__ == "__main__":
    unittest.main()
