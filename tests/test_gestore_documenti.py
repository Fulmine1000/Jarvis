import tempfile
import unittest
from pathlib import Path

from moduli.gestore_documenti import GestoreDocumentiJarvis


class TestGestoreDocumenti(unittest.TestCase):
    def test_legge_file_testuale_senza_modificarlo(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "appunti.md"
            originale = "# Titolo\nContenuto da leggere."
            path.write_text(originale, encoding="utf-8")
            risposta = GestoreDocumentiJarvis().leggi_file(str(path))
            self.assertIn("Contenuto da leggere", risposta)
            self.assertEqual(path.read_text(encoding="utf-8"), originale)

    def test_cerca_testo_ignorando_maiuscole(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "appunti.txt"
            path.write_text("Prima riga\nSimone usa Jarvis\nUltima riga", encoding="utf-8")
            risposta = GestoreDocumentiJarvis().cerca_nel_file(str(path), "simone")
            self.assertIn("Riga 2", risposta)
            self.assertIn("Simone usa Jarvis", risposta)

    def test_cerca_testo_assente(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "appunti.txt"
            path.write_text("Solo contenuto", encoding="utf-8")
            self.assertIn("Non ho trovato", GestoreDocumentiJarvis().cerca_nel_file(str(path), "mancante"))

    def test_rifiuta_estensione_non_supportata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "appunti.bin"
            path.write_bytes(b"\x00\x01")
            with self.assertRaises(ValueError):
                GestoreDocumentiJarvis().estrai_testo(str(path))

    def test_html_rimuove_script_e_tag(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pagina.html"
            path.write_text("<h1>Titolo</h1><script>segreto()</script><p>Ciao &amp; mondo</p>", encoding="utf-8")
            testo = GestoreDocumentiJarvis().estrai_testo(str(path))
            self.assertIn("Titolo", testo)
            self.assertIn("Ciao & mondo", testo)
            self.assertNotIn("segreto", testo)

    def test_file_mancante(self):
        with tempfile.TemporaryDirectory() as directory:
            risposta = GestoreDocumentiJarvis().leggi_file(str(Path(directory) / "assente.txt"))
            self.assertIn("Non trovo il file", risposta)


if __name__ == "__main__":
    unittest.main()
