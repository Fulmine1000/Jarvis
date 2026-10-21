"""Test offline per i widget/comandi del dashboard HUD."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from moduli.dashboard_hud import DashboardHUD, calcola_espressione


class TestDashboardHUD(unittest.TestCase):
    def test_calcolo_aritmetico(self):
        self.assertEqual(calcola_espressione("2 + 3 * 4"), 14)
        self.assertEqual(calcola_espressione("(10 - 4) / 2"), 3)

    def test_calcolo_rifiuta_accesso_a_codice(self):
        with self.assertRaises(ValueError):
            calcola_espressione("__import__('os').system('echo no')")

    def test_calcolo_limita_esponenti(self):
        with self.assertRaises(ValueError):
            calcola_espressione("2 ** 100")

    def test_calcolo_rifiuta_risultati_complessi(self):
        with self.assertRaises(ValueError):
            calcola_espressione("(-1) ** 0.5")

    def test_salva_e_legge_nota_localmente(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "note.txt"
            dashboard = DashboardHUD(note_path=path)
            self.assertIn("Nota salvata", dashboard.gestisci_comando("nota: ricordare il progetto"))
            self.assertIn("ricordare il progetto", dashboard.gestisci_comando("leggi nota"))

    def test_comando_meteo_delega_citta(self):
        with patch.object(DashboardHUD, "meteo", return_value="Meteo mock") as meteo:
            self.assertEqual(DashboardHUD().gestisci_comando("meteo Roma"), "Meteo mock")
            meteo.assert_called_once_with("Roma")

    def test_comando_ora(self):
        self.assertIn("Sono le", DashboardHUD().gestisci_comando("che ora è"))


if __name__ == "__main__":
    unittest.main()
