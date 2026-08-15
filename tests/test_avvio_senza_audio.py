"""Test di avvio in ambiente SENZA sounddevice e vosk.

Simula esattamente le condizioni del Mac dell'utente: Python con virtualenv
in cui sounddevice e vosk non sono installati (ModuleNotFoundError).
Impostando i moduli a None in sys.modules, l'import successivo solleva
ModuleNotFoundError (sottoclasse di ImportError).
"""
import sys
import os
import io
import unittest

# Blocca sounddevice e vosk come se non fossero installati
sys.modules['sounddevice'] = None
sys.modules['vosk'] = None

# Assicura che la directory del progetto sia nel path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestAvvioSenzaAudio(unittest.TestCase):
    """Verifica che Jarvis si avvii senza sounddevice né vosk."""

    def test_import_voce_package(self):
        """voce/__init__.py si importa senza sounddevice/vosk."""
        from voce import AscoltatoreVoce, RiconoscitoreVoce, SintesiVocale
        self.assertIsNotNone(AscoltatoreVoce)
        self.assertIsNotNone(RiconoscitoreVoce)
        self.assertIsNotNone(SintesiVocale)

    def test_import_modulo_voce(self):
        """moduli/voce_modulo.py si importa senza audio."""
        from moduli.voce_modulo import ModuloVoce
        self.assertIsNotNone(ModuloVoce)

    def test_import_kernel(self):
        """core/kernel.py si importa senza audio."""
        from core.kernel import KernelJarvis
        self.assertIsNotNone(KernelJarvis)

    def test_ascoltatore_disponibile_false(self):
        """AscoltatoreVoce.disponibile = False senza sounddevice."""
        from voce.ascoltatore import AscoltatoreVoce
        a = AscoltatoreVoce()
        self.assertFalse(a.disponibile)

    def test_ascoltatore_avvia_false(self):
        """AscoltatoreVoce.avvia() ritorna False senza crash."""
        from voce.ascoltatore import AscoltatoreVoce
        a = AscoltatoreVoce()
        self.assertFalse(a.avvia())

    def test_riconoscitore_disponibile_false(self):
        """RiconoscitoreVoce.disponibile = False senza vosk."""
        from voce.riconoscimento import RiconoscitoreVoce
        r = RiconoscitoreVoce()
        self.assertFalse(r.disponibile)

    def test_riconoscitore_avvia_false(self):
        """RiconoscitoreVoce.avvia() ritorna False senza crash."""
        from voce.riconoscimento import RiconoscitoreVoce
        r = RiconoscitoreVoce()
        self.assertFalse(r.avvia())

    def test_sintesi_disponibile(self):
        """SintesiVocale si costruisce anche senza audio."""
        from voce.sintesi import SintesiVocale
        s = SintesiVocale()
        self.assertTrue(s.attivo)

    def test_kernel_costruzione(self):
        """KernelJarvis si costruisce senza audio."""
        from core.kernel import KernelJarvis
        k = KernelJarvis()
        self.assertEqual(k.personalita.nome, "Jarvis")

    def test_kernel_avvio_solo_testo(self):
        """kernel.avvia() ritorna True e voce_disponibile = False."""
        from core.kernel import KernelJarvis
        k = KernelJarvis()
        self.assertTrue(k.avvia())
        self.assertFalse(k.voce_disponibile)
        self.assertFalse(k.modulo_voce.ascolto_attivo)
        self.assertTrue(k.modulo_voce.sintesi_attiva)
        k.arresta()

    def test_comando_funziona(self):
        """I comandi funzionano anche senza audio."""
        from core.kernel import KernelJarvis
        k = KernelJarvis()
        k.avvia()
        r = k.esegui_comando("che ore sono")
        self.assertIsInstance(r, str)
        self.assertIn("Sono le", r)
        k.arresta()


if __name__ == "__main__":
    unittest.main()
