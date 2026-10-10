"""Test per le correzioni mirate delle trascrizioni Vosk osservate in Jarvis."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voce.riconoscimento import RiconoscitoreVoce


class TestNormalizzazioneVocale(unittest.TestCase):
    def test_stato_cybersecurity_trascritto_male(self):
        casi = (
            "stato sai per security",
            "sai per security",
            "cybersecurity",
            "cyber security",
        )
        for testo in casi:
            with self.subTest(testo=testo):
                self.assertEqual(
                    RiconoscitoreVoce.normalizza_comando_riconosciuto(testo),
                    "stato cybersecurity",
                )

    def test_cybersecurity_trascritto_foneticamente(self):
        self.assertEqual(
            RiconoscitoreVoce.normalizza_comando_riconosciuto("sai bersi uniti"),
            "cybersecurity",
        )

    def test_comando_rete_trascritto_male(self):
        casi = (
            "analizzano il mia rete",
            "analizzano la mia rete",
            "analizza il mia rete",
        )
        for testo in casi:
            with self.subTest(testo=testo):
                self.assertEqual(
                    RiconoscitoreVoce.normalizza_comando_riconosciuto(testo),
                    "analizza la mia rete",
                )

    def test_punteggiatura_finale_non_impedisce_correzione(self):
        self.assertEqual(
            RiconoscitoreVoce.normalizza_comando_riconosciuto("stato sai per security."),
            "stato cybersecurity",
        )

    def test_frasi_non_correlate_restano_invariate(self):
        for testo in ("che ore sono", "apri Safari", "ricorda colore è blu"):
            with self.subTest(testo=testo):
                self.assertEqual(
                    RiconoscitoreVoce.normalizza_comando_riconosciuto(testo),
                    testo,
                )


if __name__ == "__main__":
    unittest.main()
