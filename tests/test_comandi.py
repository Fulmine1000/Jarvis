"""Test dei comandi (Fase 5.6).

Verifica il gestore comandi end-to-end attraverso il kernel, inclusi i
comandi protetti, l'integrazione del contesto e i fallback dei dispositivi.
I test non devono produrre audio reale: la sintesi viene sostituita da un
mock e viene verificato che ogni comando venga inoltrato una sola volta.
"""

import os
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.kernel import KernelJarvis


class TestComandi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kernel = KernelJarvis()
        cls.kernel.avvia()
        cls.parla_mock = Mock(return_value=True)
        cls.kernel.parla = cls.parla_mock

    @classmethod
    def tearDownClass(cls):
        cls.kernel.arresta()

    def setUp(self):
        self.parla_mock.reset_mock()

    def _cmd(self, comando):
        return self.kernel.esegui_comando(comando)

    def test_comando_vuoto(self):
        self.assertEqual(self._cmd(""), "Comando vuoto.")
        self.assertEqual(self._cmd("   "), "Comando vuoto.")

    def test_buongiorno(self):
        risposta = self._cmd("buongiorno")
        self.assertIsInstance(risposta, str)
        self.assertGreater(len(risposta), 0)

    def test_ora(self):
        risposta = self._cmd("che ore sono")
        self.assertIn(":", risposta)

    def test_data(self):
        risposta = self._cmd("che giorno è")
        self.assertIn("/", risposta)

    def test_stato_dispositivi(self):
        risposta = self._cmd("stato dispositivi")
        self.assertIsInstance(risposta, str)

    def test_quali_dispositivi(self):
        risposta = self._cmd("quali dispositivi")
        self.assertIn("computer", risposta)
        self.assertIn("telefono", risposta)
        self.assertIn("smart_home", risposta)

    def test_ricorda_e_cerca(self):
        self._cmd("ricorda animale è gatto")
        risposta = self._cmd("ricorda animale è gatto")
        self.assertIsInstance(risposta, str)

    def test_chiamami_e_come_mi_chiamo(self):
        self._cmd("chiamami TestUser")
        risposta = self._cmd("come mi chiamo")
        self.assertIn("testuser", risposta.lower())

    def test_accendi_luce(self):
        risposta = self._cmd("accendi luce soggiorno")
        self.assertIsInstance(risposta, str)

    def test_apri_senza_telefono_principale(self):
        risposta = self._cmd("apri spotify")
        self.assertIsInstance(risposta, str)
        self.assertNotEqual(risposta, "Non ho trovato un comando compatibile.")

    def test_chiudi_senza_telefono_principale(self):
        risposta = self._cmd("chiudi spotify")
        self.assertIsInstance(risposta, str)
        self.assertNotEqual(risposta, "Non ho trovato un comando compatibile.")

    def test_comando_sconosciuto(self):
        risposta = self._cmd("xyzzy_inesistente_12345")
        self.assertEqual(risposta, "Non ho trovato un comando compatibile.")

    def test_stato_sistema(self):
        risposta = self._cmd("stato sistema")
        self.assertIsInstance(risposta, str)

    def test_aiutami(self):
        risposta = self._cmd("aiutami")
        self.assertIsInstance(risposta, str)
        self.assertGreater(len(risposta), 0)

    def test_contesto_aggiornato(self):
        self._cmd("che ore sono")
        stato = self.kernel.contesto.stato()
        self.assertGreaterEqual(stato["comandi_memorizzati"], 1)

    def test_comando_protetto_bloccato(self):
        risposta = self._cmd("elimina file importante")
        self.assertIn("conferma", risposta.lower())

    def test_risposta_vocale_una_sola_volta(self):
        risposta = self._cmd("buongiorno")
        self.parla_mock.assert_called_once_with(risposta)


if __name__ == "__main__":
    unittest.main()
