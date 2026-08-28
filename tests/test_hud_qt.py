"""Test strutturali dell'HUD Qt Quick definitivo."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HUD_PY = ROOT / "interfaccia" / "hud.py"
HUD_QML = ROOT / "interfaccia" / "hud.qml"


class TestHUDQtQuick(unittest.TestCase):
    def test_files_hud_presenti(self):
        self.assertTrue(HUD_PY.is_file())
        self.assertTrue(HUD_QML.is_file())

    def test_hud_python_non_usa_tkinter_o_canvas(self):
        source = HUD_PY.read_text(encoding="utf-8").lower()
        self.assertNotIn("import tkinter", source)
        self.assertNotIn("tkinter as", source)
        self.assertNotIn("tk.canvas", source)
        self.assertNotIn("create_canvas", source)

    def test_qml_usa_qt_quick(self):
        source = HUD_QML.read_text(encoding="utf-8")
        self.assertIn("import QtQuick 2.15", source)
        self.assertIn("ApplicationWindow", source)
        self.assertIn("Repeater", source)
        self.assertIn("Timer", source)


if __name__ == "__main__":
    unittest.main()
