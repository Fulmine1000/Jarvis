import os
import plistlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from cybersecurity.audit_host import (
    audit_avvii_mac,
    audit_permessi_sensibili,
    audit_processi_servizi,
)


class ProcessoFinto:
    def __init__(self, pid, nome, eseguibile):
        self.info = {"pid": pid, "name": nome, "exe": eseguibile}


class PsutilFinto:
    CONN_LISTEN = "LISTEN"

    def process_iter(self, attrs):
        return iter([
            ProcessoFinto(7, "app-sconosciuta", "/Users/test/Downloads/app-sconosciuta"),
            ProcessoFinto(8, "Finder", "/System/Library/CoreServices/Finder.app/Contents/MacOS/Finder"),
        ])

    def net_connections(self, kind):
        return [
            SimpleNamespace(
                status="LISTEN",
                laddr=SimpleNamespace(ip="0.0.0.0", port=8080),
                pid=7,
            ),
            SimpleNamespace(
                status="ESTABLISHED",
                laddr=SimpleNamespace(ip="127.0.0.1", port=55000),
                pid=8,
            ),
        ]


class TestAuditProcessiServizi(unittest.TestCase):
    def test_elenca_processi_e_segnala_listener_esposto_senza_scansionare_rete(self):
        risultato = audit_processi_servizi(psutil_mod=PsutilFinto())

        self.assertTrue(risultato["ok"])
        self.assertEqual(risultato["processi_esaminati"], 2)
        self.assertEqual(len(risultato["indicatori"]), 1)
        self.assertEqual(risultato["indicatori"][0]["pid"], 7)
        self.assertEqual(len(risultato["porte_in_ascolto"]), 1)
        self.assertEqual(risultato["porte_in_ascolto"][0]["porta"], 8080)
        self.assertTrue(risultato["porte_in_ascolto"][0]["esposto_su_tutte_le_interfacce"])

    def test_psutil_non_disponibile_non_blocca_jarvis(self):
        risultato = audit_processi_servizi(psutil_mod=False)

        self.assertFalse(risultato["ok"])
        self.assertIn("psutil", risultato["errore"])


class TestAuditAvviiMac(unittest.TestCase):
    def test_ignora_link_simbolici_e_plist_oltre_un_megabyte(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "LaunchAgents"
            root.mkdir()
            target = root / "target.plist"
            with target.open("wb") as file:
                plistlib.dump({"Label": "target"}, file)
            link = root / "linked.plist"
            link.symlink_to(target)
            grande = root / "grande.plist"
            with grande.open("wb") as file:
                file.truncate(1024 * 1024 + 1)

            risultato = audit_avvii_mac(roots=[root])

        self.assertFalse(risultato["ok"])
        self.assertEqual(risultato["elementi"], [])
        self.assertTrue(any("symlink" in errore.lower() or "simbolico" in errore.lower() for errore in risultato["errori"]))
        self.assertTrue(any("limite" in errore.lower() for errore in risultato["errori"]))

    def test_analizza_plist_senza_eseguire_i_programmi(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "LaunchAgents"
            root.mkdir()
            plist = root / "com.example.agent.plist"
            with plist.open("wb") as file:
                plistlib.dump({
                    "Label": "com.example.agent",
                    "ProgramArguments": ["/Users/test/Downloads/agent"],
                    "RunAtLoad": True,
                    "KeepAlive": False,
                }, file)

            risultato = audit_avvii_mac(roots=[root])

        self.assertTrue(risultato["ok"])
        self.assertEqual(len(risultato["elementi"]), 1)
        self.assertEqual(risultato["elementi"][0]["etichetta"], "com.example.agent")
        self.assertIn("percorso download o temporaneo", risultato["elementi"][0]["indicatori"])


class TestAuditPermessi(unittest.TestCase):
    @unittest.skipUnless(hasattr(os, "chmod"), "Permessi POSIX non disponibili")
    def test_segnala_chiave_ssh_e_cartella_con_permessi_troppo_aperti(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            ssh = home / ".ssh"
            ssh.mkdir()
            chiave = ssh / "id_ed25519"
            chiave.write_text("not-a-real-key", encoding="utf-8")
            os.chmod(ssh, 0o755)
            os.chmod(chiave, 0o644)

            risultato = audit_permessi_sensibili(home=home)

        self.assertTrue(risultato["ok"])
        stati = {item["percorso"].split("/")[-1]: item["stato"] for item in risultato["controlli"]}
        self.assertEqual(stati[".ssh"], "permessi troppo aperti")
        self.assertEqual(stati["id_ed25519"], "permessi troppo aperti")


if __name__ == "__main__":
    unittest.main()
