import unittest

from comandi.gestore import GestoreComandi


class CybersecurityFinta:
    def audit_processi_servizi(self):
        return {"ok": True, "processi_esaminati": 12, "indicatori": [], "porte_in_ascolto": []}

    def audit_avvii_mac(self):
        return {"ok": True, "elementi": [{"etichetta": "agent", "indicatori": ["percorso download o temporaneo"]}]}

    def audit_permessi_sensibili(self):
        return {"ok": True, "controlli": [{"percorso": "~/.ssh/id_ed25519", "stato": "permessi troppo aperti"}]}

    def scansiona_malware(self, percorso):
        return {"ok": True, "stato": "nessuna minaccia rilevata", "percorso": percorso, "rilevamenti": [], "nota": "read-only"}


class KernelFinto:
    def __init__(self):
        self.cybersecurity = CybersecurityFinta()


class TestComandiAuditCybersecurity(unittest.TestCase):
    def setUp(self):
        self.gestore = GestoreComandi(kernel=KernelFinto())

    def test_comando_processi_e_servizi(self):
        risposta = self.gestore._esegui_raw("controlla processi e servizi")
        self.assertIn("12 processi", risposta)

    def test_comando_avvii_automatici(self):
        risposta = self.gestore._esegui_raw("controlla avvii automatici")
        self.assertIn("agent", risposta)
        self.assertIn("download", risposta)

    def test_comando_permessi_sensibili(self):
        risposta = self.gestore._esegui_raw("controlla permessi sensibili")
        self.assertIn("permessi troppo aperti", risposta)

    def test_comando_scansione_malware(self):
        risposta = self.gestore._esegui_raw("scansiona malware /tmp/esempio.bin")
        self.assertIn("nessuna minaccia rilevata", risposta)
        self.assertIn("/tmp/esempio.bin", risposta)


if __name__ == "__main__":
    unittest.main()
