import unittest

from comandi.gestore import GestoreComandi


class CybersecurityFinta:
    def __init__(self):
        self.chiamate = 0

    def controlla_sicurezza_mac(self):
        self.chiamate += 1
        return {
            "ok": True,
            "sistema": "Darwin",
            "controlli": [
                {"nome": "Firewall applicazioni", "stato": "attivo"},
                {"nome": "FileVault", "stato": "non verificabile"},
            ],
            "nota": "read-only",
        }


class KernelFinto:
    def __init__(self, cybersecurity):
        self.cybersecurity = cybersecurity


class TestComandoPosturaMac(unittest.TestCase):
    def test_comando_principale_richiede_la_verifica_e_riferisce_gli_stati(self):
        cyber = CybersecurityFinta()
        gestore = GestoreComandi(kernel=KernelFinto(cyber))

        risposta = gestore._esegui_raw("controlla sicurezza mac")

        self.assertEqual(cyber.chiamate, 1)
        self.assertIn("Firewall applicazioni: attivo", risposta)
        self.assertIn("FileVault: non verificabile", risposta)

    def test_alias_macOS_usa_lo_stesso_controllo(self):
        cyber = CybersecurityFinta()
        gestore = GestoreComandi(kernel=KernelFinto(cyber))

        risposta = gestore._esegui_raw("controlla protezioni macos")

        self.assertEqual(cyber.chiamate, 1)
        self.assertIn("Verifica sicurezza macOS completata", risposta)

    def test_risponde_chiaramente_se_il_modulo_non_e_disponibile(self):
        gestore = GestoreComandi(kernel=KernelFinto(None))

        risposta = gestore._esegui_raw("controlla sicurezza mac")

        self.assertEqual(risposta, "Modulo cybersecurity non disponibile.")


if __name__ == "__main__":
    unittest.main()
