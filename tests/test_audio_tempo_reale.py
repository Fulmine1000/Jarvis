"""Regressioni per mantenere l'ascolto vocale in tempo reale su Mac Intel."""

import array
import sys
import unittest
from unittest.mock import patch

from voce.ascoltatore import AscoltatoreVoce
from voce.riconoscimento import RiconoscitoreVoce


class TestAudioTempoReale(unittest.TestCase):
    def test_mac_intel_preferisce_modello_small_se_presente(self):
        with patch("voce.riconoscimento.sys.platform", "darwin"), patch(
            "voce.riconoscimento.platform.machine", return_value="x86_64"
        ), patch("voce.riconoscimento.os.path.isdir", return_value=True):
            percorso = RiconoscitoreVoce._modello_italiano_predefinito("/jarvis")
        self.assertEqual(percorso, "/jarvis/vosk-model-small-it-0.22")

    def test_altri_sistemi_preferiscono_modello_completo(self):
        with patch("voce.riconoscimento.sys.platform", "linux"), patch(
            "voce.riconoscimento.platform.machine", return_value="x86_64"
        ), patch("voce.riconoscimento.os.path.isdir", return_value=True):
            percorso = RiconoscitoreVoce._modello_italiano_predefinito("/jarvis")
        self.assertEqual(percorso, "/jarvis/vosk-model-it-0.22")

    def test_coda_audio_limitata_e_scarto_del_blocco_piu_vecchio(self):
        ascoltatore = AscoltatoreVoce(filtro_rumore=False)
        self.assertEqual(ascoltatore.audio.maxsize, 12)

        for valore in range(1, 14):
            blocco = array.array("h", [valore] * 1600).tobytes()
            ascoltatore.callback(blocco, 1600, None, None)

        self.assertEqual(ascoltatore.audio.qsize(), 12)
        self.assertEqual(ascoltatore.blocchi_audio_scartati, 1)
        primo = ascoltatore.audio.get_nowait()
        campione = array.array("h")
        campione.frombytes(primo)
        if sys.byteorder != "little":
            campione.byteswap()
        self.assertEqual(campione[0], 2)
        stato = ascoltatore.stato()
        self.assertEqual(stato["buffer_massimo"], 12)
        self.assertEqual(stato["blocchi_audio_scartati"], 1)


if __name__ == "__main__":
    unittest.main()
