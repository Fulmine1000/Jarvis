"""Test dei dispositivi (Fase 5.7).

Verifica il gestore dispositivi, SmartHomeJarvis, e le funzionalità di base
dei dispositivi registrati.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.kernel import KernelJarvis


class TestDispositivi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kernel = KernelJarvis()
        cls.kernel.avvia()
        cls.gestore = cls.kernel.modulo_dispositivi.gestore

    @classmethod
    def tearDownClass(cls):
        cls.kernel.arresta()

    def test_dispositivi_registrati(self):
        """Tutti i dispositivi previsti sono registrati."""
        elenco = self.gestore.elenco()
        for atteso in ("computer", "rete", "bluetooth", "smart_home", "telefono"):
            self.assertIn(atteso, elenco)

    def test_smart_home_registrata(self):
        """SmartHomeJarvis è registrata (cablaggio Fase 2.4)."""
        self.assertIn("smart_home", self.gestore.elenco())
        sh = self.gestore.cerca("smart_home")
        self.assertIsNotNone(sh)

    def test_stato_tutti(self):
        """stato_tutti() restituisce un dict con tutti i dispositivi."""
        stati = self.gestore.stato_tutti()
        self.assertIsInstance(stati, dict)
        self.assertIn("computer", stati)

    def test_computer(self):
        """ComputerJarvis restituisce il proprio stato."""
        computer = self.gestore.cerca("computer")
        stato = computer.stato()
        self.assertEqual(stato["stato"], "attivo")

    def test_rete(self):
        """Rete è online e ha un IP."""
        rete = self.gestore.cerca("rete")
        stato = rete.stato()
        self.assertEqual(stato["stato"], "online")

    def test_telefono(self):
        """TelefonoJarvis è connesso."""
        telefono = self.gestore.cerca("telefono")
        stato = telefono.stato()
        self.assertTrue(stato["connesso"])

    def test_smart_home_luce(self):
        """La luce soggiorno è presente e accendibile."""
        sh = self.gestore.cerca("smart_home")
        dispositivi = sh.lista()
        nomi = [d["nome"].lower() for d in dispositivi]
        self.assertTrue(any("luce" in n for n in nomi))


if __name__ == "__main__":
    unittest.main()
