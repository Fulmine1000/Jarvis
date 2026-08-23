import time
import unittest

from core.automazioni import AutomazioniJarvis, PianificatoreJarvis
from core.visione import VisioneJarvis
from core.dialogo import DialogoJarvis


class TestAutomazioni(unittest.TestCase):
    def test_automazione(self):
        risultati = []
        motore = AutomazioniJarvis()
        motore.registra("test", lambda: risultati.append(True))
        self.assertTrue(motore.esegui("test"))
        self.assertEqual(risultati, [True])
        self.assertTrue(motore.disattiva("test"))
        self.assertFalse(motore.esegui("test"))
        motore.ferma()

    def test_pianificatore(self):
        risultati = []
        scheduler = PianificatoreJarvis()
        scheduler.pianifica("test", 0.01, lambda: risultati.append(True))
        time.sleep(0.05)
        self.assertEqual(risultati, [True])


class TestVisione(unittest.TestCase):
    def test_stato_senza_dipendenze(self):
        visione = VisioneJarvis()
        stato = visione.stato()
        self.assertIn("camera_disponibile", stato)


class TestDialogo(unittest.TestCase):
    def test_stato(self):
        dialogo = DialogoJarvis()
        stato = dialogo.stato()
        self.assertEqual(stato["motore"], "Ollama locale")
        self.assertEqual(stato["storia_messaggi"], 0)


if __name__ == "__main__":
    unittest.main()
