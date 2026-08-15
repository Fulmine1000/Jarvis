"""Test del sistema vocale (Fase 5.8).

Verifica che i componenti vocali si costruiscano senza dipendenze audio,
che la disponibilità venga riportata correttamente e che la sintesi
funzioni (almeno in fallback stampa).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voce.sintesi import SintesiVocale
from voce.wake_word import WakeWordJarvis
from voce.ascoltatore import AscoltatoreVoce
from voce.riconoscimento import RiconoscitoreVoce


class TestSintesi(unittest.TestCase):

    def setUp(self):
        self.sintesi = SintesiVocale()

    def test_costruzione(self):
        self.assertTrue(self.sintesi.attivo)

    def test_parla_stringa_vuota(self):
        self.assertFalse(self.sintesi.parla(""))

    def test_parla_disattivata(self):
        self.sintesi.ferma()
        self.assertFalse(self.sintesi.parla("ciao"))
        self.sintesi.avvia()

    def test_parla_testo(self):
        """parla() con testo non vuoto ritorna True (fallback stampa incluso)."""
        # In ambiente di test senza piper/say/espeak, cade su print().
        risultato = self.sintesi.parla("Test di sintesi.")
        self.assertTrue(risultato)

    def test_stato(self):
        stato = self.sintesi.stato()
        self.assertIn("piper_disponibile", stato)
        self.assertIn("motore", stato)


class TestWakeWord(unittest.TestCase):

    def setUp(self):
        self.ww = WakeWordJarvis()

    def test_rileva_jarvis(self):
        """La wake word 'jarvis' viene rilevata."""
        risultato = self.ww.controlla("jarvis accendi la luce")
        self.assertTrue(risultato["attivato"])

    def test_rileva_case_insensitive(self):
        risultato = self.ww.controlla("JARVIS")
        self.assertTrue(risultato["attivato"])

    def test_non_rileva_altro(self):
        risultato = self.ww.controlla("ciao come stai")
        self.assertFalse(risultato["attivato"])


class TestAscoltatore(unittest.TestCase):

    def setUp(self):
        self.a = AscoltatoreVoce()

    def test_disponibilita(self):
        """disponibile riflette la presenza di sounddevice."""
        try:
            __import__("sounddevice")
            sd = True
        except Exception:
            sd = False
        self.assertEqual(self.a.disponibile, sd)

    def test_stato(self):
        stato = self.a.stato()
        self.assertIn("disponibile", stato)


class TestRiconoscitore(unittest.TestCase):

    def setUp(self):
        self.r = RiconoscitoreVoce()

    def test_disponibilita(self):
        """disponibile riflette la presenza di vosk."""
        try:
            __import__("vosk")
            vosk = True
        except Exception:
            vosk = False
        self.assertEqual(self.r.disponibile, vosk)

    def test_avvio_senza_vosk(self):
        """Senza vosk, avvia() ritorna False invece di lanciare un'eccezione."""
        if self.r.disponibile:
            self.skipTest("Vosk installato: skip del test di fallback.")
        self.assertFalse(self.r.avvia())

    def test_stato(self):
        stato = self.r.stato()
        self.assertIn("disponibile", stato)


if __name__ == "__main__":
    unittest.main()
