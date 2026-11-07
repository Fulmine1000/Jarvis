import subprocess
import unittest
from unittest.mock import Mock

from cybersecurity.postura_mac import controlla_postura_mac


class RisultatoComando:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class TestPosturaMac(unittest.TestCase):
    def test_rileva_i_quattro_controlli_macOS(self):
        output = {
            "/usr/libexec/ApplicationFirewall/socketfilterfw": RisultatoComando("Firewall is enabled. (State = 1)"),
            "/usr/bin/fdesetup": RisultatoComando("FileVault is On."),
            "/usr/sbin/spctl": RisultatoComando("assessments enabled"),
            "/usr/bin/csrutil": RisultatoComando("System Integrity Protection status: enabled."),
        }

        def runner(args, **kwargs):
            return output[args[0]]

        risultato = controlla_postura_mac(sistema="Darwin", runner=runner)

        self.assertTrue(risultato["ok"])
        self.assertEqual(
            {item["nome"]: item["stato"] for item in risultato["controlli"]},
            {
                "Firewall applicazioni": "attivo",
                "FileVault": "attivo",
                "Gatekeeper": "attivo",
                "System Integrity Protection": "attivo",
            },
        )

    def test_non_esegue_comandi_su_sistemi_non_macOS(self):
        runner = Mock()
        risultato = controlla_postura_mac(sistema="Windows", runner=runner)

        runner.assert_not_called()
        self.assertTrue(risultato["ok"])
        self.assertTrue(all(item["stato"] == "non applicabile" for item in risultato["controlli"]))

    def test_usa_solo_comandi_fissi_senza_shell_e_con_timeout(self):
        chiamate = []

        def runner(args, **kwargs):
            chiamate.append((args, kwargs))
            return RisultatoComando("output non riconosciuto")

        controlla_postura_mac(sistema="Darwin", runner=runner)

        self.assertEqual(len(chiamate), 4)
        for args, kwargs in chiamate:
            self.assertIsInstance(args, tuple)
            self.assertFalse(kwargs["shell"])
            self.assertTrue(kwargs["capture_output"])
            self.assertTrue(kwargs["text"])
            self.assertLessEqual(kwargs["timeout"], 4)
        self.assertEqual(
            {args[0] for args, _ in chiamate},
            {
                "/usr/libexec/ApplicationFirewall/socketfilterfw",
                "/usr/bin/fdesetup",
                "/usr/sbin/spctl",
                "/usr/bin/csrutil",
            },
        )

    def test_timeout_e_comando_mancante_non_interrompono_gli_altri_controlli(self):
        def runner(args, **kwargs):
            if args[0].endswith("socketfilterfw"):
                raise subprocess.TimeoutExpired(args, 4)
            if args[0].endswith("fdesetup"):
                raise FileNotFoundError(args[0])
            if args[0].endswith("spctl"):
                return RisultatoComando("assessments disabled")
            return RisultatoComando("System Integrity Protection status: enabled.")

        risultato = controlla_postura_mac(sistema="Darwin", runner=runner)
        stati = {item["nome"]: item["stato"] for item in risultato["controlli"]}

        self.assertEqual(stati["Firewall applicazioni"], "non verificabile")
        self.assertEqual(stati["FileVault"], "non verificabile")
        self.assertEqual(stati["Gatekeeper"], "disattivo")
        self.assertEqual(stati["System Integrity Protection"], "attivo")

    def test_output_ambiguo_non_viene_classificato(self):
        risultato = controlla_postura_mac(
            sistema="Darwin",
            runner=lambda args, **kwargs: RisultatoComando("stato sconosciuto"),
        )

        self.assertTrue(all(item["stato"] == "non verificabile" for item in risultato["controlli"]))


if __name__ == "__main__":
    unittest.main()
