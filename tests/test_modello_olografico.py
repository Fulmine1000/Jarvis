"""Test del caricatore mesh per la modalità olografica."""
import os
import tempfile
import unittest

from interfaccia.modello_olografico import carica_modello, ErroreModello3D


class TestModelloOlografico(unittest.TestCase):
    def _file(self, suffisso, testo):
        temporaneo = tempfile.NamedTemporaryFile(mode="w", suffix=suffisso, encoding="utf-8", delete=False)
        try:
            temporaneo.write(testo)
            temporaneo.close()
            self.addCleanup(lambda: os.path.exists(temporaneo.name) and os.unlink(temporaneo.name))
            return temporaneo.name
        except Exception:
            temporaneo.close()
            raise

    def test_carica_obj_e_normalizza_mesh(self):
        path = self._file(".obj", "v 0 0 0\nv 2 0 0\nv 0 2 0\nf 1 2 3\n")
        modello = carica_modello(path)
        self.assertEqual(modello["numero_vertici"], 3)
        self.assertEqual(modello["numero_spigoli"], 3)
        self.assertEqual(modello["formato"], "OBJ")
        self.assertTrue(all(-1.0 <= c <= 1.0 for p in modello["vertici"] for c in p))

    def test_carica_stl_ascii(self):
        testo = ("solid test\n facet normal 0 0 1\n outer loop\n"
                 " vertex 0 0 0\n vertex 1 0 0\n vertex 0 1 0\n"
                 " endloop\n endfacet\nendsolid test\n")
        modello = carica_modello(self._file(".stl", testo))
        self.assertEqual(modello["numero_vertici"], 3)
        self.assertEqual(modello["numero_spigoli"], 3)

    def test_rifiuta_formato_non_supportato(self):
        path = self._file(".txt", "contenuto")
        with self.assertRaises(ErroreModello3D):
            carica_modello(path)

    def test_rifiuta_indice_obj_non_valido(self):
        path = self._file(".obj", "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 99\n")
        with self.assertRaises(ErroreModello3D):
            carica_modello(path)

    def test_rifiuta_mesh_senza_dimensione(self):
        path = self._file(".obj", "v 1 1 1\nv 1 1 1\nv 1 1 1\nf 1 2 3\n")
        with self.assertRaises(ErroreModello3D):
            carica_modello(path)


if __name__ == "__main__":
    unittest.main()
