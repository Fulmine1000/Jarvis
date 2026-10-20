"""Test unitari per il controllo Android via ADB senza dispositivi reali."""
import unittest
from unittest.mock import patch, MagicMock

from dispositivi.controllo_android import ControlloAndroidVideo


class TestControlloAndroidVideo(unittest.TestCase):
    def setUp(self):
        self.controller = ControlloAndroidVideo()
        self.controller.adb = "/usr/bin/adb"

    @patch("dispositivi.controllo_android.subprocess.run")
    def test_risveglia_schermo_non_sblocca_pin(self, run):
        run.side_effect = [
            MagicMock(returncode=0, stdout="List of devices attached\nTEST123\tdevice\n", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]
        result = self.controller.risveglia_schermo()
        self.assertIn("PIN, password o biometria", result)
        self.assertEqual(run.call_args_list[1].args[0][-3:], ["input", "keyevent", "224"])

    @patch("dispositivi.controllo_android.subprocess.run")
    def test_telefono_non_collegato(self, run):
        run.return_value = MagicMock(returncode=0, stdout="List of devices attached\n", stderr="")
        self.assertIn("Nessun telefono Android", self.controller.risveglia_schermo())

    @patch("dispositivi.controllo_android.subprocess.run")
    def test_app_non_installata(self, run):
        run.side_effect = [
            MagicMock(returncode=0, stdout="List of devices attached\nTEST123\tdevice\n", stderr=""),
            MagicMock(returncode=0, stdout="package:com.android.settings\n", stderr=""),
        ]
        self.assertIn("Non ho trovato un'app installata", self.controller.apri_app("jiohotstar"))

    def test_comando_app(self):
        with patch.object(self.controller, "apri_app", return_value="ok") as action:
            self.assertEqual(self.controller.gestisci_comando("apri youtube sul telefono"), "ok")
            action.assert_called_once_with("youtube")

    def test_comandi_in_inglese_del_video(self):
        with patch.object(self.controller, "risveglia_schermo", return_value="wake") as wake:
            self.assertEqual(self.controller.gestisci_comando("unlock my phone"), "wake")
            wake.assert_called_once_with()
        with patch.object(self.controller, "apri_app", return_value="open") as action:
            self.assertEqual(self.controller.gestisci_comando("open JioHotstar in my phone"), "open")
            action.assert_called_once_with("jiohotstar")

    def test_comando_chiamata_non_esegue_chiamata_silenziosa(self):
        with patch.object(self.controller, "chiama", return_value="dialer") as action:
            self.assertEqual(self.controller.gestisci_comando("chiama mia sorella"), "dialer")
            action.assert_called_once_with("mia sorella")


if __name__ == "__main__":
    unittest.main()
