import unittest

from core.portabilita import (
    AdapterDispositivoIA,
    GestorePortabilitaIA,
    ProfiloDispositivoIA,
)


class _Personalita:
    def stato_personalita(self):
        return {"stile": "jarvis"}


class _Kernel:
    nome = "J.A.R.V.I.S."
    versione = "test"
    personalita = _Personalita()


class _Adapter(AdapterDispositivoIA):
    def __init__(self, device_id, nome):
        super().__init__(ProfiloDispositivoIA(id=device_id, nome=nome))

    def rifiuta_attivazione(self):
        self.profilo.online = True
        self.attiva_jarvis = lambda: False


class TestPortabilitaIA(unittest.TestCase):
    def setUp(self):
        self.gestore = GestorePortabilitaIA(_Kernel())
        self.mac = _Adapter("mac", "Mac")
        self.alexa = _Adapter("alexa", "Alexa")
        self.gestore.registra(self.mac)
        self.gestore.registra(self.alexa)
        self.gestore.connetti("mac")
        self.gestore.connetti("alexa")

    def test_trasferimento_disattiva_host_precedente(self):
        self.gestore.trasferisci("mac")
        identita = self.gestore.trasferisci("alexa")
        self.assertEqual(self.gestore.host_attivo, "alexa")
        self.assertFalse(self.mac.profilo.jarvis_attivo)
        self.assertTrue(self.alexa.profilo.jarvis_attivo)
        self.assertEqual(identita["modalita"], "core_remoto")
        self.assertNotIn("memoria", identita)

    def test_trasferimento_non_connesso_non_cambia_host(self):
        self.gestore.trasferisci("mac")
        self.alexa.disconnetti()
        with self.assertRaises(RuntimeError):
            self.gestore.trasferisci("alexa")
        self.assertEqual(self.gestore.host_attivo, "mac")
        self.assertTrue(self.mac.profilo.jarvis_attivo)

    def test_rimozione_host_attivo_lo_disattiva(self):
        self.gestore.trasferisci("mac")
        self.assertTrue(self.gestore.rimuovi("mac"))
        self.assertIsNone(self.gestore.host_attivo)
        self.assertNotIn("mac", self.gestore.adapter)

    def test_trasferimento_non_sovrappone_host_se_attivazione_fallisce(self):
        self.gestore.trasferisci("mac")
        self.alexa.rifiuta_attivazione()
        with self.assertRaises(RuntimeError):
            self.gestore.trasferisci("alexa")
        self.assertEqual(self.gestore.host_attivo, "mac")
        self.assertTrue(self.mac.profilo.jarvis_attivo)


if __name__ == "__main__":
    unittest.main()
