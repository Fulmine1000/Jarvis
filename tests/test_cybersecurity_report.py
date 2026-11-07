import unittest
from unittest.mock import patch

from cybersecurity.modulo import CybersecurityJarvis


class TestRapportoCybersecurity(unittest.TestCase):
    def test_rapporto_unifica_i_controlli_read_only_senza_scansionare_malware(self):
        posture = {"ok": True, "controlli": [{"nome": "Firewall", "stato": "attivo"}]}
        processi = {"ok": True, "processi_esaminati": 4, "porte_in_ascolto": []}
        avvii = {"ok": True, "elementi": []}
        permessi = {"ok": True, "controlli": []}

        with patch("cybersecurity.modulo.controlla_postura_mac", create=True, return_value=posture), \
             patch("cybersecurity.audit_host.audit_processi_servizi", return_value=processi), \
             patch("cybersecurity.audit_host.audit_avvii_mac", return_value=avvii), \
             patch("cybersecurity.audit_host.audit_permessi_sensibili", return_value=permessi), \
             patch("cybersecurity.scanner_malware.scansiona_malware") as malware:
            risultato = CybersecurityJarvis().rapporto_sicurezza()

        self.assertTrue(risultato["ok"])
        self.assertEqual(risultato["postura_mac"], posture)
        self.assertEqual(risultato["processi_servizi"], processi)
        self.assertEqual(risultato["avvii_automatici"], avvii)
        self.assertEqual(risultato["permessi_sensibili"], permessi)
        malware.assert_not_called()


if __name__ == "__main__":
    unittest.main()
