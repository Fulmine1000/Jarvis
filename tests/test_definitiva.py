import unittest

from core.automazioni import AutomazioniJarvis, PianificatoreJarvis
from core.capacita import CapacitaJarvis
from core.diagnostica import DiagnosticaJarvis
from core.dialogo import DialogoJarvis
from voce.wake_word import WakeWordJarvis


class TestDefinitiva(unittest.TestCase):
    def test_calcolatrice_sicura(self):
        cap = CapacitaJarvis()
        self.assertEqual(cap.calcola("2 + 3 * 4"), 14)
        with self.assertRaises(Exception):
            cap.calcola("__import__('os').system('echo no')")

    def test_wake_word(self):
        wake = WakeWordJarvis()
        risultato = wake.controlla("Ehi, Jarvis che ore sono")
        self.assertTrue(risultato["attivato"])
        self.assertEqual(risultato["comando"], "che ore sono")

    def test_automazione(self):
        eventi = []
        auto = AutomazioniJarvis()
        auto.avvia()
        auto.registra("test", lambda: eventi.append(True))
        self.assertTrue(auto.esegui("test"))
        self.assertEqual(eventi, [True])
        auto.ferma()

    def test_scheduler(self):
        scheduler = PianificatoreJarvis()
        self.assertIn("test", scheduler.pianifica("test", 30, lambda: None))
        self.assertTrue(scheduler.annulla("test"))
        scheduler.ferma()

    def test_diagnostica(self):
        diagnostica = DiagnosticaJarvis()
        risultato = diagnostica.esegui()
        self.assertIn("python", risultato)
        self.assertTrue(diagnostica.avviata)

    def test_dialogo_fallback(self):
        dialogo = DialogoJarvis()
        self.assertEqual(dialogo.stato()["motore"], "Ollama locale")


if __name__ == "__main__":
    unittest.main()
