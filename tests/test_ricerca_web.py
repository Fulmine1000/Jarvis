"""Test offline per la ricerca web di Jarvis."""
import ssl
import sys
import unittest
from urllib.error import URLError
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from moduli import ricerca_web


class _Response:
    status = 200
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit):
        return b"""
        <div class="result">
          <a class="result__a" href="https://example.org/page">Titolo esempio</a>
          <a class="result__snippet">Estratto della fonte</a>
        </div>
        <div class="result">
          <a class="result__a" href="javascript:alert(1)">Non sicuro</a>
        </div>
        """


class TestRicercaWeb(unittest.TestCase):
    def test_query_vuota(self):
        self.assertIn("indichi cosa", ricerca_web.cerca_web(""))

    def test_query_troppo_lunga(self):
        self.assertIn("troppo lunga", ricerca_web.cerca_web("x" * 301))

    def test_parse_risultati_e_url_sicuri(self):
        with patch.object(ricerca_web, "urlopen", return_value=_Response()):
            result = ricerca_web.cerca_web("Jarvis")
        self.assertIn("Titolo esempio", result)
        self.assertIn("https://example.org/page", result)
        self.assertIn("Estratto della fonte", result)
        self.assertNotIn("javascript:", result)

    def test_errore_rete_gestito(self):
        with patch.object(ricerca_web, "urlopen", side_effect=OSError("offline")):
            result = ricerca_web.cerca_web("Jarvis")
        self.assertIn("connessione", result)

    def test_certificato_tls_non_attendibile_segnalato_senza_disabilitare_verifica(self):
        errore_tls = ssl.SSLCertVerificationError("self signed certificate in certificate chain")
        with patch.object(ricerca_web, "urlopen", side_effect=URLError(errore_tls)):
            result = ricerca_web.cerca_web("Jarvis")
        self.assertIn("certificato HTTPS non è attendibile", result)
        self.assertIn("verifica TLS", result)


if __name__ == "__main__":
    unittest.main()
