import unittest
from unittest.mock import patch

from cybersecurity.modulo import CybersecurityJarvis


class TestCybersecurityJarvis(unittest.TestCase):
    def setUp(self):
        self.modulo = CybersecurityJarvis()

    def test_inventario_rete_e_sola_lettura(self):
        with patch("cybersecurity.modulo.socket.getaddrinfo", return_value=[]), patch("cybersecurity.modulo.socket.gethostname", return_value="mac-test"):
            risultato = self.modulo.analizza_rete_locale()
        self.assertEqual(risultato["host"], "mac-test")
        self.assertIn("sola lettura", risultato["tipo_controllo"])

    def test_rifiuta_ip_pubblico(self):
        self.assertIn("solo IP privati", self.modulo.richiedi_scansione_host("8.8.8.8"))
        self.assertIsNone(self.modulo._host_in_attesa)

    def test_rifiuta_nome_host(self):
        self.assertIn("IP numerico", self.modulo.richiedi_scansione_host("example.com"))

    def test_scan_non_parte_senza_conferma_esplicita(self):
        self.modulo.richiedi_scansione_host("192.168.1.20")
        with patch("cybersecurity.modulo.socket.create_connection") as conn:
            risposta = self.modulo.conferma_scansione_host("192.168.1.21")
        conn.assert_not_called()
        self.assertIn("Nessuna verifica", risposta)

    def test_scan_confermata_usa_solo_porte_in_lista(self):
        self.modulo.richiedi_scansione_host("192.168.1.20")
        class Connessione:
            def __enter__(self): return self
            def __exit__(self, *args): return False
        def connessione(addr, timeout):
            if addr[1] == 80:
                return Connessione()
            raise OSError("closed")
        with patch("cybersecurity.modulo.socket.create_connection", side_effect=connessione) as conn:
            risposta = self.modulo.conferma_scansione_host("192.168.1.20")
        self.assertIn("80", risposta)
        self.assertEqual([call.args[0][1] for call in conn.call_args_list], list(self.modulo.PORTE_CONSENTITE))
        self.assertIsNone(self.modulo._host_in_attesa)

    def test_anulla_conferma_in_attesa(self):
        self.modulo.richiedi_scansione_host("192.168.1.20")
        self.assertIn("annullata", self.modulo.annulla_scansione())
        self.assertIsNone(self.modulo._host_in_attesa)


if __name__ == "__main__":
    unittest.main()
