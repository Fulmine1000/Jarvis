import unittest
from types import SimpleNamespace

from moduli.voce_modulo import ModuloVoce


class TestAcquisizioneModuloVoce(unittest.TestCase):
    def test_usa_un_blocco_audio_per_preservare_la_segmentazione_vosk(self):
        class AscoltatoreFinto:
            def __init__(self):
                self.chiamate_ascolta = 0
                self.chiamate_batch = 0

            def ascolta(self, timeout=1):
                self.chiamate_ascolta += 1
                return b"\x00\x00" * 16

            def ascolta_batch(self, *args, **kwargs):
                self.chiamate_batch += 1
                raise AssertionError("Il modulo voce non deve aggregare i blocchi per Vosk")

        class RiconoscitoreFinto:
            backend_attivo = "vosk"
            ultima_trascrizione_grezza = ""
            ultima_trascrizione_normalizzata = ""
            ultima_confidenza_media = None
            ultime_parole_riconosciute = []

            def riconosci(self, audio):
                return "jarvis"

        modulo = ModuloVoce.__new__(ModuloVoce)
        modulo.ascolto_attivo = True
        modulo.ascoltatore = AscoltatoreFinto()
        modulo.riconoscitore = RiconoscitoreFinto()
        modulo.kernel = None
        modulo.ultimo_errore_ascolto = None
        modulo._ultima_diagnostica_microfono = 0.0
        modulo._ultimo_errore_whisper_loggato = None

        self.assertEqual(modulo.ascolta_comando(), "jarvis")
        self.assertEqual(modulo.ascoltatore.chiamate_ascolta, 1)
        self.assertEqual(modulo.ascoltatore.chiamate_batch, 0)


if __name__ == "__main__":
    unittest.main()
