"""Test del filtro antirumore fail-safe di Jarvis."""

import array
import math
import unittest

from voce.filtro_rumore import FiltroRumore


class TestFiltroRumore(unittest.TestCase):
    def setUp(self):
        self.filtro = FiltroRumore(frequenza=16000, livello=1)
        # Isola i test del fallback dalla disponibilità opzionale di WebRTC.
        self.filtro._processor = None
        self.filtro._numpy = None

    @staticmethod
    def _rms(pcm):
        campioni = array.array("h")
        campioni.frombytes(pcm[: len(pcm) - (len(pcm) % 2)])
        if not campioni:
            return 0.0
        return math.sqrt(sum(x * x for x in campioni) / len(campioni))

    def test_blocco_vuoto(self):
        self.assertEqual(self.filtro.processa(b""), b"")

    def test_mantiene_formato_pcm16_e_lunghezza(self):
        campioni = array.array("h", [1200, -1200, 600, -600] * 400)
        audio = campioni.tobytes()
        filtrato = self.filtro.processa(audio)
        self.assertIsInstance(filtrato, bytes)
        self.assertEqual(len(filtrato), len(audio))
        self.assertEqual(len(filtrato) % 2, 0)

    def test_fallback_non_silenzia_voce_debole(self):
        # Simula una voce quieta a 440 Hz, non solo un segnale forte.
        campioni = array.array(
            "h",
            [int(350 * math.sin(2 * math.pi * 440 * i / 16000)) for i in range(1600)],
        )
        audio = campioni.tobytes()
        filtrato = self.filtro.processa(audio)
        self.assertEqual(len(filtrato), len(audio))
        self.assertGreater(self._rms(filtrato), self._rms(audio) * 0.75)

    def test_fallback_preserva_voce_normale(self):
        campioni = array.array(
            "h",
            [int(5000 * math.sin(2 * math.pi * 220 * i / 16000)) for i in range(1600)],
        )
        audio = campioni.tobytes()
        filtrato = self.filtro.processa(audio)
        self.assertEqual(len(filtrato), len(audio))
        self.assertGreater(self._rms(filtrato), self._rms(audio) * 0.75)

    def test_byte_finale_incompleto_non_viene_perso(self):
        audio = array.array("h", [1000, -1000, 500, -500]).tobytes() + bytes([0x7F])
        filtrato = self.filtro.processa(audio)
        self.assertEqual(len(filtrato), len(audio))
        self.assertEqual(filtrato[-1:], bytes([0x7F]))

    def test_errore_webrtc_fa_passare_il_blocco_originale(self):
        class FakeNumpy:
            int16 = object()

            @staticmethod
            def frombuffer(audio, dtype):
                return object()

        class BrokenProcessor:
            @staticmethod
            def process(campioni):
                raise RuntimeError("errore simulato")

        self.filtro._numpy = FakeNumpy()
        self.filtro._processor = BrokenProcessor()
        audio = array.array("h", [300, -300, 150, -150] * 400).tobytes()
        self.assertEqual(self.filtro.processa(audio), audio)
        self.assertIsNone(self.filtro._processor)
        self.assertEqual(self.filtro.stato()["modalita"], "passa-alto-sicuro")
        self.assertIn("errore simulato", self.filtro.stato()["ultimo_errore"])

    def test_webrtc_non_puo_silenziare_completamente_un_blocco_udibile(self):
        class FakeSamples:
            def __init__(self, values):
                self.values = array.array("h", values)

            @property
            def size(self):
                return len(self.values)

            def tobytes(self):
                return self.values.tobytes()

        class FakeNumpy:
            int16 = object()

            @staticmethod
            def frombuffer(audio, dtype):
                valori = array.array("h")
                valori.frombytes(audio)
                return FakeSamples(valori)

            @staticmethod
            def asarray(values, dtype):
                return values if isinstance(values, FakeSamples) else FakeSamples(values)

        class SilencingProcessor:
            @staticmethod
            def process(campioni):
                return FakeSamples([0] * campioni.size)

        self.filtro._numpy = FakeNumpy()
        self.filtro._processor = SilencingProcessor()
        self.filtro.modalita = "webrtc"
        audio = array.array("h", [1000, -1000, 800, -800] * 400).tobytes()

        # Se WebRTC cancella quasi tutto, il blocco originale deve arrivare a Vosk.
        self.assertEqual(self.filtro.processa(audio), audio)
        stato = self.filtro.stato()
        self.assertEqual(stato["blocchi_protetti_da_silenziamento"], 1)
        self.assertFalse(stato["noise_gate"])

    def test_filtro_disponibile_senza_dipendenze_opzionali(self):
        audio = array.array("h", [220] * 1600).tobytes()
        filtrato = self.filtro.processa(audio)
        self.assertEqual(len(filtrato), len(audio))
        stato = self.filtro.stato()
        self.assertTrue(stato["attivo"])
        self.assertEqual(stato["modalita"], "passa-alto-sicuro")

    def test_stato_indica_frequenza_e_livello(self):
        stato = self.filtro.stato()
        self.assertEqual(stato["frequenza"], 16000)
        self.assertEqual(stato["livello"], 1)
        self.assertIn("webrtc_disponibile", stato)


if __name__ == "__main__":
    unittest.main()
