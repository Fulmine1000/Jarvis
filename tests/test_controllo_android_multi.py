"""Test offline del controllo Android multi-dispositivo."""
import unittest
from unittest.mock import MagicMock, patch

from dispositivi.controllo_android_multi import ControlloAndroidMulti


class TestControlloAndroidMulti(unittest.TestCase):
    def setUp(self):
        self.controller = ControlloAndroidMulti(adb="/usr/bin/adb")

    def test_elenca_solo_dispositivi_autorizzati(self):
        with patch.object(self.controller, "_run", return_value=(
            "List of devices attached\nPHONE1\tdevice\nPHONE2\tunauthorized\nPHONE3\toffline", None
        )):
            self.assertEqual(self.controller.dispositivi(), (["PHONE1"], None))

    def test_risveglia_tutti_senza_comandi_di_sblocco(self):
        with patch.object(self.controller, "dispositivi", return_value=(["P1", "P2"], None)), \
             patch.object(self.controller, "_run", return_value=("", None)) as run:
            risposta = self.controller.risveglia_tutti()
        self.assertIn("2/2", risposta)
        self.assertIn("non vengono aggirati", risposta)
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            self.assertEqual(call.args[0][-3:], ["input", "keyevent", "224"])

    def test_rifiuta_url_non_http(self):
        self.assertIn("URL non valido", self.controller.apri_url_su_tutti("javascript:alert(1)"))

    def test_canzone_preferita_richiede_url_configurato(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertIn("JARVIS_MEDIA_PREFERITA_URL", self.controller.gestisci_comando(
                "riproduci la mia canzone preferita su tutti i telefoni"
            ))

    def test_comando_app_multi(self):
        with patch.object(self.controller, "apri_app_su_tutti", return_value="ok") as action:
            self.assertEqual(self.controller.gestisci_comando("apri youtube su tutti i telefoni"), "ok")
            action.assert_called_once_with("youtube")


if __name__ == "__main__":
    unittest.main()
