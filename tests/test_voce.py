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


class TestWakeWordVarianti(unittest.TestCase):
    """Test robustezza wake word italiana (bug 'ehi' di Vosk)."""

    def setUp(self):
        self.ww = WakeWordJarvis()

    def _attiva_senza_comando(self, testo):
        """Assert che il testo attivi con comando vuoto (solo wake word)."""
        ww = WakeWordJarvis()
        r = ww.controlla(testo)
        self.assertTrue(r["attivato"], f"non attivato per {testo!r}")
        self.assertEqual(r["comando"], "", f"comando non vuoto per {testo!r}: {r['comando']!r}")

    def test_jarvis_solo(self):
        """'Jarvis' da solo attiva con comando vuoto."""
        self._attiva_senza_comando("Jarvis")

    def test_ehi_jarvis(self):
        """'Ehi Jarvis' attiva con comando vuoto."""
        self._attiva_senza_comando("Ehi Jarvis")

    def test_hey_jarvis(self):
        """'Hey Jarvis' attiva con comando vuoto."""
        self._attiva_senza_comando("Hey Jarvis")

    def test_ehi_jarvis_virgola(self):
        """'Ehi, Jarvis' (con virgola) attiva con comando vuoto."""
        self._attiva_senza_comando("Ehi, Jarvis")

    def test_hey_jarvis_virgola(self):
        """'Hey, Jarvis' (con virgola) attiva con comando vuoto."""
        self._attiva_senza_comando("Hey, Jarvis")

    def test_ehi_solo_prefisso(self):
        """Vosk trascrive solo 'ehi': attiva senza passare al GestoreComandi."""
        self._attiva_senza_comando("ehi")

    def test_hey_solo_prefisso(self):
        """Vosk trascrive solo 'hey': attiva senza passare al GestoreComandi."""
        self._attiva_senza_comando("hey")

    def test_ehi_jarvis_con_comando(self):
        """'Ehi Jarvis che ore sono' attiva ed estrae il comando."""
        r = self.ww.controlla("Ehi Jarvis che ore sono")
        self.assertTrue(r["attivato"])
        self.assertEqual(r["comando"], "che ore sono")

    def test_jarvis_con_comando(self):
        """'jarvis accendi la luce' attiva ed estrae il comando."""
        r = self.ww.controlla("jarvis accendi la luce")
        self.assertTrue(r["attivato"])
        self.assertEqual(r["comando"], "accendi la luce")


class TestWakeWordBugEhi(unittest.TestCase):
    """Test specifici per il bug: 'ehi' non deve produrre
    'Non ho trovato un comando compatibile'."""

    def test_jarvis_poi_ehi_non_passa_al_gestore(self):
        """Dopo 'Jarvis', un 'ehi' parziale non diventa comando."""
        ww = WakeWordJarvis()
        ww.controlla("Jarvis")  # attiva, comando vuoto
        r = ww.controlla("ehi")  # entro timeout
        self.assertTrue(r["attivato"])
        self.assertEqual(r["comando"], "",
                         "'ehi' non deve essere passato come comando")

    def test_ehi_poi_jarvis_poi_comando(self):
        """Vosk spezza 'Ehi Jarvis' in 'ehi' + 'jarvis': flusso corretto."""
        ww = WakeWordJarvis()
        r1 = ww.controlla("ehi")
        self.assertTrue(r1["attivato"])
        self.assertEqual(r1["comando"], "")
        r2 = ww.controlla("jarvis")
        self.assertTrue(r2["attivato"])
        self.assertEqual(r2["comando"], "",
                         "'jarvis' da solo non deve diventare comando")
        r3 = ww.controlla("che ore sono")
        self.assertTrue(r3["attivato"])
        self.assertEqual(r3["comando"], "che ore sono")

    def test_jarvis_poi_jarvis_non_doppia_risposta(self):
        """Doppio 'Jarvis' non produce comando residuo."""
        ww = WakeWordJarvis()
        ww.controlla("Jarvis")
        r = ww.controlla("Jarvis")
        self.assertTrue(r["attivato"])
        self.assertEqual(r["comando"], "")


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
