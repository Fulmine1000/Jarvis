"""Test dei comandi vocali per gli strumenti file di cybersecurity."""

import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from comandi.gestore import GestoreComandi


class TestComandiCybersecurityFile(unittest.TestCase):
    def setUp(self):
        self.cyber = Mock()
        self.cyber.hash_file.return_value = {
            "ok": True,
            "file": "/tmp/Prova.txt",
            "sha256": "abc123",
        }
        self.gestore = GestoreComandi(
            kernel=SimpleNamespace(cybersecurity=self.cyber)
        )

    def test_hash_sha256_con_percorso_diretto(self):
        risposta = self.gestore._esegui_cybersecurity_file_command(
            "calcola hash SHA-256 di /tmp/Prova.txt"
        )
        self.cyber.hash_file.assert_called_once_with("/tmp/Prova.txt")
        self.assertIn("abc123", risposta)

    def test_hash_sha256_con_formulazione_del_file(self):
        risposta = self.gestore._esegui_cybersecurity_file_command(
            "calcola l'hash SHA-256 del file /tmp/Prova.txt"
        )
        self.cyber.hash_file.assert_called_once_with("/tmp/Prova.txt")
        self.assertIn("SHA-256", risposta)

    def test_hash_senza_percorso_chiede_il_percorso(self):
        risposta = self.gestore._esegui_cybersecurity_file_command(
            "calcola hash SHA-256 di un file"
        )
        self.cyber.hash_file.assert_not_called()
        self.assertIn("percorso completo", risposta)


if __name__ == "__main__":
    unittest.main()
