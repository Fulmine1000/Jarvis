"""Test di avvio e integrazione del kernel."""

import importlib
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.kernel import KernelJarvis


class TestAvvio(unittest.TestCase):
    def setUp(self):
        self.kernel = KernelJarvis()

    def test_costruzione_kernel(self):
        self.assertIsNotNone(self.kernel)
        self.assertEqual(self.kernel.nome, "J.A.R.V.I.S.")
        self.assertEqual(self.kernel.versione, "4.0")

    def test_avvio_kernel(self):
        self.assertTrue(self.kernel.avvia())
        self.assertEqual(self.kernel.stato, "Operativo")

    def test_moduli_cablati(self):
        for attributo in ("personalita", "preferenze", "contesto", "sicurezza", "stato_sistema_modulo", "aggiornamenti", "automazioni", "pianificatore", "visione", "diagnostica"):
            self.assertIsNotNone(getattr(self.kernel, attributo))

    def test_stato_sistema(self):
        self.kernel.avvia()
        stato = self.kernel.stato_sistema()
        for chiave in ("nome", "versione", "memoria", "voce", "comandi", "dispositivi", "plugin", "diagnostica"):
            self.assertIn(chiave, stato)

    def test_arresto(self):
        self.kernel.avvia()
        self.kernel.arresta()
        self.assertEqual(self.kernel.stato, "Spento")

    def tearDown(self):
        try:
            self.kernel.arresta()
        except Exception:
            pass


class TestImportModuli(unittest.TestCase):
    def test_import_moduli_ufficiali(self):
        moduli = [
            "core.kernel", "core.config", "core.logger", "core.event_bus", "core.manager",
            "core.automazioni", "core.diagnostica", "core.dialogo", "core.visione",
            "memoria.memoria", "memoria.database", "memoria.profilo", "memoria.preferenze", "memoria.contesto",
            "voce.sintesi", "voce.wake_word", "voce.assistente_voce", "voce.motore_ascolto",
            "comandi.gestore", "moduli.voce_modulo", "moduli.comandi_modulo", "moduli.dispositivi_modulo",
            "dispositivi.gestore", "dispositivi.telefono", "dispositivi.smart_home", "dispositivi.tv_lg",
            "plugin.plugin_manager", "personalita.personalita", "interfaccia.hud",
        ]
        for mod in moduli:
            with self.subTest(modulo=mod):
                importlib.import_module(mod)


if __name__ == "__main__":
    unittest.main()
