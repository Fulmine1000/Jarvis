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

    def rapporto_sicurezza(self):
        return {
            "ok": True,
            "postura_mac": {"controlli": [{"nome": "Firewall", "stato": "attivo"}]},
            "processi_servizi": {"processi_esaminati": 12, "porte_in_ascolto": []},
            "avvii_automatici": {"elementi": []},
            "permessi_sensibili": {"controlli": []},
        }


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
        risposta = self.gestore._esegui_cybersecurity_file_command("scansiona malware /tmp/esempio.bin")
        self.assertIn("nessuna minaccia rilevata", risposta)
        self.assertIn("/tmp/esempio.bin", risposta)

    def test_rapporto_cybersecurity_unificato(self):
        risposta = self.gestore._esegui_raw("rapporto cybersecurity")
        self.assertIn("Firewall: attivo", risposta)
        self.assertIn("12 processi", risposta)


if __name__ == "__main__":
    unittest.main()
