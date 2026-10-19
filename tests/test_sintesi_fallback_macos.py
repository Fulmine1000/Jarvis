import unittest
from types import SimpleNamespace
from unittest.mock import patch

from voce.sintesi import SintesiVocale


class TestFallbackSintesiMacOS(unittest.TestCase):
    def setUp(self):
        self.sintesi = SintesiVocale.__new__(SintesiVocale)
        self.sintesi.voce_sistema = "VoceItaliana"
        self.sintesi.pausa_cinematica = True
        self.sintesi.rate_cinematico = 156
        self.sintesi.velocita = 0.92

    @patch.object(SintesiVocale, "_parla_con_voicepack", return_value=True)
    @patch.object(SintesiVocale, "_parla_con_voce_clonata", return_value=True)
    @patch.object(SintesiVocale, "_parla_con_sistema", return_value=True)
    @patch("voce.sintesi.platform.system", return_value="Darwin")
    def test_blu_usa_prima_la_sintesi_di_sistema(
        self, _sistema, parla_sistema, parla_clonata, parla_voicepack
    ):
        self.sintesi.attivo = True

        self.assertTrue(self.sintesi.parla("Il mio colore preferito è blu."))
        parla_sistema.assert_called_once_with(
            "Il mio colore preferito è blu.", voce_forzata="Alice"
        )
        parla_clonata.assert_not_called()
        parla_voicepack.assert_not_called()

    @patch("voce.sintesi.subprocess.run")
    @patch("voce.sintesi.shutil.which", return_value="/usr/bin/say")
    @patch("voce.sintesi.platform.system", return_value="Darwin")
    def test_usa_alice_quando_la_voce_e_forzata(self, _sistema, _which, run):
        run.return_value = SimpleNamespace(returncode=0, stderr="", stdout="")

        self.assertTrue(
            self.sintesi._parla_con_sistema(
                "Il mio colore preferito è blu.", voce_forzata="Alice"
            )
        )
        comando = run.call_args.args[0]
        self.assertEqual(comando[:3], ["say", "-v", "Alice"])

    @patch("voce.sintesi.subprocess.run")
    @patch("voce.sintesi.shutil.which", return_value="/usr/bin/say")
    @patch("voce.sintesi.platform.system", return_value="Darwin")
    def test_riprova_con_voce_predefinita_se_voce_scelta_fallisce(
        self, _sistema, _which, run
    ):
        run.side_effect = [
            SimpleNamespace(returncode=1, stderr="voce non disponibile", stdout=""),
            SimpleNamespace(returncode=0, stderr="", stdout=""),
        ]

        self.assertTrue(self.sintesi._parla_con_sistema("Jarvis operativo"))
        self.assertEqual(run.call_count, 2)
        self.assertIn("-v", run.call_args_list[0].args[0])
        self.assertNotIn("-v", run.call_args_list[1].args[0])

    @patch("voce.sintesi.subprocess.run")
    @patch("voce.sintesi.shutil.which", return_value="/usr/bin/say")
    @patch("voce.sintesi.platform.system", return_value="Darwin")
    def test_usa_voce_predefinita_se_non_e_configurata(
        self, _sistema, _which, run
    ):
        self.sintesi.voce_sistema = None
        run.return_value = SimpleNamespace(returncode=0, stderr="", stdout="")

        self.assertTrue(self.sintesi._parla_con_sistema("Sono qui"))
        run.assert_called_once()
        self.assertNotIn("-v", run.call_args.args[0])

    @patch("voce.sintesi.subprocess.run")
    @patch("voce.sintesi.shutil.which", return_value="/usr/bin/say")
    @patch("voce.sintesi.platform.system", return_value="Darwin")
    def test_restituisce_false_se_entrambi_i_tentativi_falliscono(
        self, _sistema, _which, run
    ):
        run.side_effect = [
            SimpleNamespace(returncode=1, stderr="errore voce", stdout=""),
            SimpleNamespace(returncode=1, stderr="errore predefinita", stdout=""),
        ]

        self.assertFalse(self.sintesi._parla_con_sistema("Test"))
        self.assertEqual(run.call_count, 2)


if __name__ == "__main__":
    unittest.main()
