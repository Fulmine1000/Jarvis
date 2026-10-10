import os
import tempfile
import time
import unittest
from unittest.mock import patch

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
        # Il test deve usare una cronologia isolata: la cronologia reale di
        # Jarvis è persistente e può contenere messaggi di sessioni precedenti.
        with tempfile.TemporaryDirectory() as cartella:
            file_storia_test = os.path.join(cartella, "conversazioni.json")
            with patch.object(DialogoJarvis, "FILE_STORIA", file_storia_test):
                dialogo = DialogoJarvis()
                stato = dialogo.stato()

        self.assertIn(
            stato["motore"],
            {
                "Ollama locale",
                "Conversation Engine locale",
                "IA automatica (backend non attivo)",
                "llama.cpp locale",
                "API compatibile",
            },
        )
        self.assertEqual(stato["storia_messaggi"], 0)


if __name__ == "__main__":
    unittest.main()
