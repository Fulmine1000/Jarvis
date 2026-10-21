"""Test del rilevatore di doppio battito senza microfono reale."""
import unittest
from unittest.mock import Mock

from moduli.doppio_battito import RilevatoreDoppioBattito


class TestRilevatoreDoppioBattito(unittest.TestCase):
    def setUp(self):
        self.callback = Mock()
        self.detector = RilevatoreDoppioBattito(
            self.callback, soglia_rms=0.2, intervallo_minimo=0.1,
            intervallo_massimo=0.7, cooldown=1.5,
        )

    def test_due_picchi_ravvicinati_attivano_callback(self):
        self.assertFalse(self.detector.processa_rms(0.0, 10.0))
        self.assertFalse(self.detector.processa_rms(0.5, 10.1))
        self.assertFalse(self.detector.processa_rms(0.0, 10.2))
        self.assertTrue(self.detector.processa_rms(0.6, 10.4))
        self.callback.assert_called_once_with()

    def test_picchi_troppo_lontani_non_attivano(self):
        self.detector.processa_rms(0.5, 10.0)
        self.detector.processa_rms(0.0, 10.1)
        self.assertFalse(self.detector.processa_rms(0.5, 11.0))
        self.callback.assert_not_called()

    def test_blocchi_alti_contigui_contano_come_un_picco(self):
        self.detector.processa_rms(0.5, 10.0)
        self.assertFalse(self.detector.processa_rms(0.6, 10.1))
        self.callback.assert_not_called()

    def test_cooldown_impedisce_trigger_ripetuti(self):
        self.detector.processa_rms(0.5, 10.0)
        self.detector.processa_rms(0.0, 10.1)
        self.assertTrue(self.detector.processa_rms(0.5, 10.2))
        self.detector.processa_rms(0.0, 10.3)
        self.assertFalse(self.detector.processa_rms(0.5, 10.5))
        self.callback.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
