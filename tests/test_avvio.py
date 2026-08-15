"""Test di avvio del kernel (Fase 5.1 / 5.2 / 5.4).

Verifica che il kernel si costruisca e si avvii anche SENZA dipendenze audio
(sounddevice, vosk) e SENZA modello Vosk, entrando in modalità solo-testo.
"""

import os
import sys
import unittest

# Permette l'import dei moduli del progetto dalla root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.kernel import KernelJarvis


class TestAvvio(unittest.TestCase):

    def setUp(self):
        self.kernel = KernelJarvis()

    def test_costruzione_kernel(self):
        """Il kernel si costruisce senza errori anche senza dipendenze audio."""
        self.assertIsNotNone(self.kernel)
        self.assertEqual(self.kernel.nome, "Jarvis")
        self.assertEqual(self.kernel.versione, "3.0")

    def test_avvio_kernel(self):
        """Il kernel avvia e ritorna True anche in modalità degradata."""
        ok = self.kernel.avvia()
        self.assertTrue(ok)
        self.assertEqual(self.kernel.stato, "Operativo")

    def test_moduli_scollegati_cablati(self):
        """Personalita, Preferenze, Contesto, Sicurezza, Stato sono cablati."""
        self.assertIsNotNone(self.kernel.personalita)
        self.assertIsNotNone(self.kernel.preferenze)
        self.assertIsNotNone(self.kernel.contesto)
        self.assertIsNotNone(self.kernel.sicurezza)
        self.assertIsNotNone(self.kernel.stato_sistema_modulo)
        self.assertIsNotNone(self.kernel.aggiornamenti)

    def test_modalita_solo_testo(self):
        """Senza audio, il kernel entra in modalità solo-testo."""
        self.kernel.avvia()
        # In ambiente di test senza microfono/vosk, l'ascolto è spento.
        self.assertFalse(self.kernel.voce_disponibile)
        # Ma la sintesi resta disponibile (modulo attivo).
        self.assertTrue(self.kernel.modulo_voce.attivo)
        self.assertTrue(self.kernel.modulo_voce.sintesi_attiva)

    def test_stato_sistema(self):
        """stato_sistema() restituisce un dict completo."""
        self.kernel.avvia()
        stato = self.kernel.stato_sistema()
        self.assertIn("nome", stato)
        self.assertIn("versione", stato)
        self.assertIn("memoria", stato)
        self.assertIn("voce", stato)
        self.assertIn("comandi", stato)
        self.assertIn("dispositivi", stato)
        self.assertIn("plugin", stato)
        self.assertIn("personalita", stato)
        self.assertIn("sicurezza", stato)

    def test_arresto(self):
        """L'arresto porta lo stato a Spento."""
        self.kernel.avvia()
        self.kernel.arresta()
        self.assertEqual(self.kernel.stato, "Spento")

    def tearDown(self):
        try:
            self.kernel.arresta()
        except Exception:
            pass


class TestImportModuli(unittest.TestCase):
    """Verifica che tutti i moduli ufficiali siano importabili (Fase 5.2)."""

    def test_import_moduli_ufficiali(self):

        importlib = __import__("importlib")

        moduli = [
            "core.kernel",
            "core.config",
            "core.logger",
            "core.event_bus",
            "core.manager",
            "memoria.memoria",
            "memoria.database",
            "memoria.profilo",
            "memoria.preferenze",
            "memoria.contesto",
            "voce.sintesi",
            "voce.wake_word",
            "voce.assistente_voce",
            "voce.motore_ascolto",
            "comandi.gestore",
            "moduli.voce_modulo",
            "moduli.comandi_modulo",
            "moduli.dispositivi_modulo",
            "dispositivi.gestore",
            "dispositivi.telefono",
            "dispositivi.smart_home",
            "plugin.plugin_manager",
            "personalita.personalita",
            "interfaccia.hud",
            "stato",
            "sicurezza",
            "aggiornamenti",
        ]

        for mod in moduli:
            with self.subTest(modulo=mod):
                importlib.import_module(mod)

    def test_import_condizionali_audio(self):
        """I moduli audio si importano anche senza sounddevice/vosk."""
        import importlib

        from voce.ascoltatore import AscoltatoreVoce
        from voce.riconoscimento import RiconoscitoreVoce

        a = AscoltatoreVoce()
        r = RiconoscitoreVoce()

        # Disponibilità reale: l'import effettivo riesce (non solo find_spec,
        # perché sounddevice può essere installato ma PortAudio assente).
        try:
            importlib.import_module("sounddevice")
            sd_disponibile = True
        except Exception:
            sd_disponibile = False

        try:
            importlib.import_module("vosk")
            vosk_disponibile = True
        except Exception:
            vosk_disponibile = False

        self.assertEqual(a.disponibile, sd_disponibile)
        self.assertEqual(r.disponibile, vosk_disponibile)


if __name__ == "__main__":
    unittest.main()
