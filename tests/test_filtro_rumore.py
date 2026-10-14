"""Test automatici del filtro antirumore di Jarvis."""

import array
import unittest

from voce.filtro_rumore import FiltroRumore


class TestFiltroRumore(unittest.TestCase):
    def setUp(self):
        self.filtro = FiltroRumore(frequenza=16000, livello=2)

    def test_blocco_vuoto(self):
        self.assertEqual(self.filtro.processa(b""), b"")

    def test_mantiene_formato_pcm16(self):
        campioni = array.array("h", [1200, -1200, 600, -600] * 400)
        audio = campioni.tobytes()
        filtrato = self.filtro.processa(audio)
        self.assertIsInstance(filtrato, bytes)
        self.assertEqual(len(filtrato), len(audio))
        self.assertEqual(len(filtrato) % 2, 0)

    def test_filtro_sempre_disponibile_senza_dipendenze_opzionali(self):
        # WebRTC può essere assente: il filtro adattivo integrato deve comunque
        # restituire PCM valido senza sollevare eccezioni.
        self.filtro._processor = None
        self.filtro._numpy = None
        campioni = array.array("h", [220] * 1600)
        filtrato = self.filtro.processa(campioni.tobytes())
        self.assertEqual(len(filtrato), len(campioni.tobytes()))
        stato = self.filtro.stato()
        self.assertTrue(stato["attivo"])
        self.assertEqual(stato["modalita"], "filtro-adattivo")

    def test_stato_indica_frequenza_e_livello(self):
        stato = self.filtro.stato()
        self.assertEqual(stato["frequenza"], 16000)
        self.assertEqual(stato["livello"], 2)
        self.assertIn("webrtc_disponibile", stato)


if __name__ == "__main__":
    unittest.main()
