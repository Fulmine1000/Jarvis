import unittest
from unittest.mock import patch

from cybersecurity.modulo import CybersecurityJarvis


class TestCybersecurityFacciata(unittest.TestCase):
    def test_esporta_il_risultato_della_verifica_macOS(self):
        atteso = {
            "ok": True,
            "sistema": "Darwin",
            "controlli": [{"nome": "FileVault", "stato": "attivo", "dettaglio": "verificato"}],
            "nota": "read-only",
        }
        with patch("cybersecurity.postura_mac.controlla_postura_mac", return_value=atteso) as controllo:
            risultato = CybersecurityJarvis().controlla_sicurezza_mac()

        controllo.assert_called_once_with()
        self.assertIs(risultato, atteso)

    def test_dichiara_la_nuova_capacita_nello_stato(self):
        stato = CybersecurityJarvis().stato()

        self.assertIn("postura macOS read-only", stato["modalita"])


if __name__ == "__main__":
    unittest.main()
