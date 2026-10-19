import os
import sys
import types
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from voce.ascoltatore import AscoltatoreVoce


class TestSelezioneDispositivoAudio(unittest.TestCase):
    def crea_ascoltatore_senza_hardware(self, richiesto=""):
        ascoltatore = AscoltatoreVoce.__new__(AscoltatoreVoce)
        ascoltatore.dispositivo_richiesto = richiesto
        ascoltatore._sd = types.SimpleNamespace(
            default=types.SimpleNamespace(device=(1, 2)),
            query_devices=lambda: [
                {"name": "Built-in Microphone", "max_input_channels": 2},
                {"name": "Built-in Input", "max_input_channels": 2},
                {"name": "Built-in Output", "max_input_channels": 0},
            ],
        )
        return ascoltatore

    def test_predefinito_prima_e_altri_ingressi_come_fallback(self):
        ascoltatore = self.crea_ascoltatore_senza_hardware()
        self.assertEqual(ascoltatore._candidati_dispositivo(), [1, 0])

    def test_dispositivo_configurato_per_nome_ha_priorita(self):
        ascoltatore = self.crea_ascoltatore_senza_hardware("Microphone")
        self.assertEqual(ascoltatore._candidati_dispositivo(), [0, 1])

    def test_dispositivo_configurato_per_indice_ha_priorita(self):
        ascoltatore = self.crea_ascoltatore_senza_hardware("0")
        self.assertEqual(ascoltatore._candidati_dispositivo(), [0, 1])

    def test_non_ripete_indici_e_ignora_dispositivi_senza_ingresso(self):
        ascoltatore = self.crea_ascoltatore_senza_hardware()
        self.assertEqual(ascoltatore._candidati_dispositivo(), [1, 0])
        self.assertNotIn(2, ascoltatore._candidati_dispositivo())


    def test_avvia_prova_il_dispositivo_successivo_se_il_default_fallisce(self):
        tentativi = []

        class StreamFinto:
            def __init__(self, device):
                self.device = device

            def start(self):
                tentativi.append(self.device)
                if self.device == 1:
                    raise RuntimeError("PortAudio: ingresso non disponibile")

            def close(self):
                pass

        class SoundDeviceFinto:
            def RawInputStream(self, **kwargs):
                return StreamFinto(kwargs["device"])

        ascoltatore = AscoltatoreVoce(filtro_rumore=False)
        ascoltatore._sd = SoundDeviceFinto()
        ascoltatore.disponibile = True
        ascoltatore._candidati_dispositivo = lambda: [1, 0]

        with patch.object(AscoltatoreVoce, "_sounddevice_disponibile", return_value=True):
            self.assertTrue(ascoltatore.avvia())

        self.assertEqual(tentativi, [1, 0])
        self.assertEqual(ascoltatore.dispositivo_attivo, 0)
        self.assertTrue(ascoltatore.attivo)
        ascoltatore.ferma()


if __name__ == "__main__":
    unittest.main()
