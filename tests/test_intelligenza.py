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

        risposta = cervello.rispondi("Spiegami cos'è un buco nero")

        self.assertEqual(risposta, "Risposta IA")
        self.assertEqual(
            kernel.dialogo.richiesta,
            "Rispondi SOLO alla richiesta attuale dell'utente, in italiano. "
            "Non aggiungere data, ora, saluti, stato del sistema, riepiloghi "
            "o altri argomenti che l'utente non ha richiesto. "
            "Non usare la cronologia precedente come motivo per cambiare "
            "argomento. Per una domanda semplice, rispondi in una o due frasi. "
            "Se la richiesta chiede una spiegazione, spiega soltanto quella. "
            "Domanda attuale: Spiegami cos'è un buco nero",
        )

    def test_stato(self):
        cervello = CervelloJarvis(FintoKernel())
        stato = cervello.stato()
        self.assertTrue(stato["attivo"])
        self.assertEqual(stato["richieste"], 0)


if __name__ == "__main__":
    unittest.main()
