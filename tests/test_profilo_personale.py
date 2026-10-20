import unittest

from memoria.memoria import MemoriaJarvis


class DatabaseFinto:
    def __init__(self):
        self.dati = {
            "profilo": {
                "vecchia_preferenza": {"valore": "da eliminare"},
                "nome_utente": {"valore": "Altro"},
            },
            "ricordi": {
                "cane": {"valore": "animale precedente"},
                "cibo": {"valore": "pizza"},
            },
            "altro": {"dato": {"valore": "non è un dato del profilo personale"}},
        }

    def aggiungi(self, categoria, chiave, valore):
        self.dati.setdefault(categoria, {})[chiave] = {"valore": valore}
        return True

    def salva(self):
        return True


class TestProfiloPersonaleJarvis(unittest.TestCase):
    def test_conserva_solo_nome_animale_e_colore_preferiti(self):
        memoria = MemoriaJarvis.__new__(MemoriaJarvis)
        memoria.database = DatabaseFinto()

        memoria._sincronizza_profilo_personale()

        profilo = memoria.database.dati["profilo"]
        self.assertEqual(
            {k: v["valore"] for k, v in profilo.items()},
            {
                "nome_utente": "Simone",
                "animale_preferito": "lupo",
                "colore_preferito": "blu",
            },
        )
        self.assertIn("ricordi", memoria.database.dati)
        self.assertNotIn("cane", memoria.database.dati["ricordi"])
        self.assertEqual(
            memoria.database.dati["ricordi"]["cibo"]["valore"], "pizza"
        )
        self.assertIn("altro", memoria.database.dati)

    def test_non_cancella_ricordi_generali_nelle_accensioni_successive(self):
        memoria = MemoriaJarvis.__new__(MemoriaJarvis)
        memoria.database = DatabaseFinto()
        memoria._sincronizza_profilo_personale()
        memoria.database.dati["ricordi"] = {"appunto_generale": {"valore": "da conservare"}}

        memoria._sincronizza_profilo_personale()

        self.assertEqual(
            memoria.database.dati["ricordi"]["appunto_generale"]["valore"],
            "da conservare",
        )


if __name__ == "__main__":
    unittest.main()
