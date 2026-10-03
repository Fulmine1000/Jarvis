"""Test di integrazione della facciata Voice Pack con i moduli reali di Jarvis."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.core import JARVIS


class _VoceFinta:
    def __init__(self):
        self.ascoltato = None
        self.parlato = []

    def ascolta_comando(self):
        return self.ascoltato

    def rispondi(self, testo):
        self.parlato.append(testo)
        return True


class _ComandiFinti:
    def __init__(self, risposta=None):
        self.risposta = risposta

    def esegui(self, testo):
        return self.risposta or "Non ho trovato un comando compatibile."


class _CervelloFinto:
    def __init__(self, risposta=None):
        self.risposta = risposta

    def rispondi(self, testo):
        return self.risposta


class _KernelFinto:
    def __init__(self, comando=None, risposta_ai=None):
        self.nome = "JARVIS"
        self.arresto_richiesto = False
        self.modulo_voce = _VoceFinta()
        self.modulo_comandi = _ComandiFinti(comando)
        self.intelligenza = _CervelloFinto(risposta_ai)
        self.memoria = None
        self.logger = None
        self.stato = "Spento"

    def avvia(self):
        self.stato = "Operativo"
        return True

    def arresta(self):
        self.stato = "Spento"
        return True

    def stato_sistema(self):
        return {"nome": self.nome, "stato": self.stato}


class TestVoicePackFacade(unittest.TestCase):
    def test_listen_usa_il_modulo_voce_reale(self):
        kernel = _KernelFinto()
        kernel.modulo_voce.ascoltato = "che ore sono"

        jarvis = JARVIS(kernel=kernel)
        self.assertEqual(jarvis.listen(), "che ore sono")

    def test_processa_comando_senza_doppia_sintesi(self):
        kernel = _KernelFinto(comando="Comando eseguito.")
        jarvis = JARVIS(kernel=kernel)

        risposta = jarvis.process("accendi la luce")

        self.assertEqual(risposta, "Comando eseguito.")
        self.assertEqual(kernel.modulo_voce.parlato, [])

    def test_processa_con_cervello_se_comando_sconosciuto(self):
        kernel = _KernelFinto(risposta_ai="Risposta del cervello.")
        jarvis = JARVIS(kernel=kernel)

        risposta = jarvis.process("raccontami qualcosa")

        self.assertEqual(risposta, "Risposta del cervello.")

    def test_fallback_conversazione_locale(self):
        kernel = _KernelFinto()
        jarvis = JARVIS(kernel=kernel)

        risposta = jarvis.process("che ore sono")

        self.assertIn("Sono le", risposta)

    def test_speak_usa_rispondi_del_modulo_voce(self):
        kernel = _KernelFinto()
        jarvis = JARVIS(kernel=kernel)

        self.assertTrue(jarvis.speak("Salve, Sir."))
        self.assertEqual(kernel.modulo_voce.parlato, ["Salve, Sir."])


if __name__ == "__main__":
    unittest.main()
