import json
import os
import tempfile
import unittest
from unittest.mock import patch
from urllib.request import Request

from core.visione import VisioneJarvis


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps({"message": {"content": "Vedo un componente elettronico."}}).encode("utf-8")


class TestVisioneImmagine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.image = os.path.join(self.tmp.name, "Scrivania.JPG")
        with open(self.image, "wb") as file:
            file.write(b"image-bytes")

    def test_immagine_inesistente(self):
        result = VisioneJarvis().analizza_immagine(os.path.join(self.tmp.name, "missing.jpg"))
        self.assertFalse(result["ok"])

    def test_estensione_non_supportata(self):
        path = os.path.join(self.tmp.name, "script.py")
        with open(path, "w", encoding="utf-8") as file:
            file.write("test")
        result = VisioneJarvis().analizza_immagine(path)
        self.assertFalse(result["ok"])
        self.assertIn("Formato non supportato", result["errore"])

    def test_endpoint_remoto_bloccato(self):
        with patch.dict(os.environ, {"JARVIS_OLLAMA_URL": "https://example.com"}):
            result = VisioneJarvis().analizza_immagine(self.image)
        self.assertFalse(result["ok"])
        self.assertIn("solo Ollama locale", result["errore"])

    def test_analisi_usa_ollama_locale(self):
        def fake_urlopen(request, timeout):
            self.assertIsInstance(request, Request)
            self.assertEqual(timeout, 90)
            return FakeResponse()

        with patch("core.visione.urllib.request.urlopen", side_effect=fake_urlopen):
            result = VisioneJarvis().analizza_immagine(self.image, "Descrivi l'immagine.")
        self.assertTrue(result["ok"])
        self.assertEqual(result["risposta"], "Vedo un componente elettronico.")
        self.assertEqual(result["motore"], "Ollama locale: moondream")


if __name__ == "__main__":
    unittest.main()
