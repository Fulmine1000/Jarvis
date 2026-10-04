import os
import tempfile
import unittest

from core.istanza import IstanzaUnicaJarvis


class TestIstanzaUnicaJarvis(unittest.TestCase):
    def test_seconda_istanza_non_acquisisce_il_lock(self):
        nome = f"jarvis_test_{os.getpid()}"
        prima = IstanzaUnicaJarvis(nome)
        seconda = IstanzaUnicaJarvis(nome)

        try:
            self.assertTrue(prima.acquisisci())
            self.assertFalse(seconda.acquisisci())
        finally:
            seconda.rilascia()
            prima.rilascia()

            try:
                os.remove(prima.percorso)
            except OSError:
                pass

    def test_lock_rilasciato_puo_essere_acquisito_di_nuovo(self):
        nome = f"jarvis_test_release_{os.getpid()}"
        prima = IstanzaUnicaJarvis(nome)
        seconda = IstanzaUnicaJarvis(nome)

        try:
            self.assertTrue(prima.acquisisci())
            prima.rilascia()
            self.assertTrue(seconda.acquisisci())
        finally:
            prima.rilascia()
            seconda.rilascia()

            try:
                os.remove(seconda.percorso)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
