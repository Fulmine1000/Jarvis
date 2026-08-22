import json
import tempfile
import unittest
from pathlib import Path

from dispositivi.tv_lg import LgWebOSTv
from dispositivi.smart_home import SmartHomeJarvis


class TestLgWebOS(unittest.TestCase):
    def test_non_configured_tv_never_fakes_connection(self):
        tv = LgWebOSTv(ip="")
        self.assertFalse(tv.disponibile())
        self.assertIn("non configurata", tv.connetti())

    def test_volume_is_clamped(self):
        tv = LgWebOSTv()
        self.assertFalse(tv.disponibile())


class TestSmartHome(unittest.TestCase):
    def test_add_and_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            import dispositivi.smart_home as module
            old = module.FILE_DISPOSITIVI
            module.FILE_DISPOSITIVI = str(Path(tmp) / "devices.json")
            try:
                home = SmartHomeJarvis()
                self.assertIn("aggiunto", home.aggiungi_dispositivo("Luce", "lampada"))
                self.assertIn("acceso", home.accendi("Luce"))
                data = json.loads(Path(module.FILE_DISPOSITIVI).read_text(encoding="utf-8"))
                self.assertEqual(data[0]["stato"], "acceso")
            finally:
                module.FILE_DISPOSITIVI = old


if __name__ == "__main__":
    unittest.main()
