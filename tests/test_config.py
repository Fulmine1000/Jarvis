import json
import os
import tempfile
import unittest
from unittest.mock import patch

import core.config as config_module
from core.config import ConfigJarvis


class TestConfigJarvis(unittest.TestCase):
    def test_config_malformata_non_viene_sovrascritta(self):
        with tempfile.TemporaryDirectory() as tmp:
            percorso = os.path.join(tmp, "config.json")
            originale = '{"utente": {"nome": "Simone"},'
            with open(percorso, "w", encoding="utf-8") as file:
                file.write(originale)

            with patch.object(config_module, "PERCORSO_CONFIG", percorso):
                config = ConfigJarvis()

            with open(percorso, "r", encoding="utf-8") as file:
                self.assertEqual(file.read(), originale)
            self.assertEqual(config.sezione("utente")["nome"], "Simone")
            self.assertTrue(config.ultimo_errore_caricamento)

    def test_sezione_nota_con_tipo_errato_usa_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            percorso = os.path.join(tmp, "config.json")
            with open(percorso, "w", encoding="utf-8") as file:
                json.dump({"voce": "non è un oggetto", "utente": ["Simone"]}, file)

            with patch.object(config_module, "PERCORSO_CONFIG", percorso):
                config = ConfigJarvis()

            self.assertIsInstance(config.sezione("voce"), dict)
            self.assertEqual(config.sezione("voce")["wake_word"], "jarvis")
            self.assertEqual(config.sezione("utente")["nome"], "Simone")
            self.assertIsNone(config.ultimo_errore_caricamento)

    def test_radice_json_non_oggetto_non_viene_sovrascritta(self):
        with tempfile.TemporaryDirectory() as tmp:
            percorso = os.path.join(tmp, "config.json")
            originale = "[]"
            with open(percorso, "w", encoding="utf-8") as file:
                file.write(originale)

            with patch.object(config_module, "PERCORSO_CONFIG", percorso):
                config = ConfigJarvis()

            with open(percorso, "r", encoding="utf-8") as file:
                self.assertEqual(file.read(), originale)
            self.assertEqual(config.sezione("jarvis")["nome"], "J.A.R.V.I.S.")
            self.assertTrue(config.ultimo_errore_caricamento)

    def test_modifica_sezione_malformata_la_ripara(self):
        with tempfile.TemporaryDirectory() as tmp:
            percorso = os.path.join(tmp, "config.json")
            with open(percorso, "w", encoding="utf-8") as file:
                json.dump({"utente": "Simone"}, file)

            with patch.object(config_module, "PERCORSO_CONFIG", percorso):
                config = ConfigJarvis()
                config.modifica("utente", "nome", "Simone")

            with open(percorso, "r", encoding="utf-8") as file:
                salvata = json.load(file)
            self.assertEqual(salvata["utente"]["nome"], "Simone")


if __name__ == "__main__":
    unittest.main()
