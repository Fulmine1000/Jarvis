import unittest

from intelligenza.cervello import CervelloJarvis


class FintaDialogo:
    def __init__(self):
        self.richiesta = None

    def rispondi(self, testo):
        self.richiesta = testo
        return "Risposta IA"

    def stato(self):
        return {"attivo": True}


class FintaPreferenze:
    def leggi(self, chiave):
        return "Simone" if chiave == "nome_utente" else None


class FintoContesto:
    def cronologia(self):
        return [{"ruolo": "utente", "testo": "precedente"}]


class FintoKernel:
    stato = "Operativo"

    def __init__(self):
        self.dialogo = FintaDialogo()
        self.preferenze = FintaPreferenze()
        self.contesto = FintoContesto()


class TestCervelloJarvis(unittest.TestCase):
    def test_delega_al_motore_ai_sulla_richiesta_attuale(self):
        kernel = FintoKernel()
        cervello = CervelloJarvis(kernel)

        risposta = cervello.rispondi("Parlami della teoria della relatività")

        self.assertEqual(risposta, "Risposta IA")
        self.assertTrue(
            kernel.dialogo.richiesta.startswith(
                "Parlami della teoria della relatività"
            )
        )
        self.assertIn("CONOSCENZA LOCALE PERTINENTE", kernel.dialogo.richiesta)

    def test_integra_conoscenza_locale_pertinente(self):
        kernel = FintoKernel()
        cervello = CervelloJarvis(kernel)

        cervello.rispondi("Parlami della teoria della relatività")

        self.assertIn("CONOSCENZA LOCALE PERTINENTE", kernel.dialogo.richiesta)
        self.assertIn("Relatività", kernel.dialogo.richiesta)

    def test_risposta_rapida_per_domanda_fattuale_nota(self):
        kernel = FintoKernel()
        cervello = CervelloJarvis(kernel)

        risposta = cervello.rispondi("Spiegami cos'è un buco nero")

        self.assertIsNotNone(risposta)
        self.assertTrue(risposta.startswith("In breve, "))
        self.assertIn("buco nero", risposta.lower())

        # La risposta rapida evita il passaggio al motore IA.
        self.assertIsNone(kernel.dialogo.richiesta)

    def test_stato(self):
        cervello = CervelloJarvis(FintoKernel())
        stato = cervello.stato()
        self.assertTrue(stato["attivo"])
        self.assertEqual(stato["richieste"], 0)


if __name__ == "__main__":
    unittest.main()
