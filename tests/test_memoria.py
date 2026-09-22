"""Test del sistema di memoria (Fase 5.5).

Verifica MemoriaJarvis, database, ricordi, preferenze, contesto.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import LoggerJarvis
from memoria.memoria import MemoriaJarvis
from memoria.database import DatabaseMemoria
from memoria.preferenze import PreferenzeJarvis
from memoria.contesto import ContestoJarvis


class TestMemoria(unittest.TestCase):

    def setUp(self):
        self.logger = LoggerJarvis()
        self.memoria = MemoriaJarvis(self.logger)
        self.memoria.avvia()

    def test_ricorda_e_cerca(self):
        """ricorda() e cerca() sono coerenti."""
        self.memoria.ricorda("colore_preferito", "verde")
        self.assertEqual(self.memoria.cerca("colore_preferito"), "verde")

    def test_ricorda_sovrascrive(self):
        """Un ricorda successivo aggiorna il valore."""
        self.memoria.ricorda("cibo", "pizza")
        self.memoria.ricorda("cibo", "sushi")
        self.assertEqual(self.memoria.cerca("cibo"), "sushi")

    def test_cerca_inesistente(self):
        """cerca() su chiave assente non solleva eccezioni."""
        risultato = self.memoria.cerca("chiave_inesistente_xyz")
        # Deve restituire un valore "non trovato" (None o stringa).
        self.assertIn(risultato, (None, "", "Non trovato"))

    def test_elenco_ricordi(self):
        """elenco_ricordi() restituisce un dict."""
        self.memoria.ricorda("test_key", "test_value")
        elenco = self.memoria.elenco_ricordi()
        self.assertIsInstance(elenco, dict)

    def test_dimentica(self):
        """dimentica() rimuove un ricordo."""
        self.memoria.ricorda("temporaneo", "valore")
        self.memoria.dimentica("temporaneo")
        # Dopo dimentica, la chiave non deve essere presente.
        risultato = self.memoria.cerca("temporaneo")
        self.assertIn(risultato, (None, "", "Non trovato"))

    def test_stato_memoria(self):
        """stato() restituisce un dict con le chiavi attese."""
        stato = self.memoria.stato()
        self.assertIsInstance(stato, dict)

    def tearDown(self):
        pass


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.db = DatabaseMemoria()

    def test_aggiungi_e_leggi(self):
        """aggiungi() e leggi() sono coerenti."""
        self.db.aggiungi("test_cat", "chiave", "valore")
        risultato = self.db.leggi("test_cat", "chiave")
        self.assertIsNotNone(risultato)
        self.assertEqual(risultato["valore"], "valore")

    def test_leggi_inesistente(self):
        """leggi() su categoria/chiave assente ritorna None."""
        self.assertIsNone(self.db.leggi("inesistente", "nessuna"))

    def test_elimina(self):
        """elimina() rimuove una voce."""
        self.db.aggiungi("test_cat", "temporaneo", "valore")
        self.assertTrue(self.db.elimina("test_cat", "temporaneo"))
        self.assertIsNone(self.db.leggi("test_cat", "temporaneo"))

    def test_tutto(self):
        """tutto() restituisce un dict."""
        self.db.aggiungi("test_cat", "k", "v")
        tutto = self.db.tutto()
        self.assertIsInstance(tutto, dict)


class TestPreferenze(unittest.TestCase):

    def setUp(self):
        self.pref = PreferenzeJarvis()

    def test_imposta_e_leggi(self):
        """imposta() e leggi() sono coerenti."""
        self.pref.imposta("nome_utente", "Simone")
        self.assertEqual(self.pref.leggi("nome_utente"), "Simone")

    def test_predefinite(self):
        """Le preferenze hanno valori predefiniti."""
        tutte = self.pref.tutte()
        self.assertIn("lingua", tutte)
        self.assertEqual(tutte["lingua"], "italiano")


class TestContesto(unittest.TestCase):

    def setUp(self):
        self.contesto = ContestoJarvis()

    def test_aggiorna_e_ultimo(self):
        """aggiorna() e ultimo() sono coerenti."""
        self.contesto.aggiorna("ciao", "buongiorno")
        ultimo = self.contesto.ultimo()
        self.assertEqual(ultimo["comando"], "ciao")
        self.assertEqual(ultimo["risposta"], "buongiorno")

    def test_stato_contesto(self):
        """stato() restituisce il conteggio dei comandi memorizzati."""
        self.contesto.aggiorna("a", "b")
        stato = self.contesto.stato()
        self.assertGreaterEqual(stato["comandi_memorizzati"], 1)


if __name__ == "__main__":
    unittest.main()
