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

    def test_arresto_timer_hud_usa_il_thread_qt(self):
        source = HUD_PY.read_text(encoding="utf-8")
        self.assertIn("stopTimerRequested = Signal()", source)
        self.assertIn("self.bridge.stopTimerRequested.connect(self.timer.stop)", source)
        inizio = source.index("    def ferma(self):")
        fine = source.index("    def mostra(self):", inizio)
        metodo_ferma = source[inizio:fine]
        self.assertIn("self.bridge.stopTimerRequested.emit()", metodo_ferma)
        self.assertIn("threading.current_thread() is threading.main_thread()", metodo_ferma)

    def test_hud_include_nucleo_sferico_olografico(self):
        source = HUD_QML.read_text(encoding="utf-8")
        self.assertIn("id: orbCanvas", source)
        self.assertIn("Canvas {", source)
        self.assertIn("// Nucleo 3D a nuvola di punti: distribuzione uniforme sulla superficie sferica.", source)
        self.assertIn("var pointCount = 760", source)
        self.assertIn("points.sort(function(a, b) { return a.z - b.z; })", source)
        self.assertIn("Alone volumetrico molto leggero", source)
        self.assertIn("var goldenAngle", source)
        self.assertIn("var p3 = project(latP, lonP)", source)
        self.assertNotIn("Punti energetici sulla superficie", source)
        self.assertNotIn("Meridiani e linee guida sferiche", source)
        self.assertNotIn("var sphere = ctx.createRadialGradient", source)
        self.assertIn("ctx.ellipse(", source)
        self.assertIn("interval: 42", source)
        self.assertIn("root.gestureZoom", source)
        self.assertIn("root.gestureTurn", source)
        self.assertIn("CORE ORB-01", source)

    def test_pannelli_hud_non_condividono_le_coordinate(self):
        source = HUD_QML.read_text(encoding="utf-8")
        self.assertIn("x: 14; y: 70; width: 204; height: root.height - 86", source)
        self.assertIn("x: 230\n        y: 70\n        width: root.width - 456", source)
        self.assertIn("x: root.width - 218; y: 70; width: 204; height: root.height - 86", source)
        self.assertIn("x: 230; y: root.height - 65; width: root.width - 456; height: 49", source)
        self.assertIn("var radius = Math.min(160", source)
        self.assertIn("rgba(65,235,255,0.15)", source)
        self.assertNotIn("#ffad42", source)


if __name__ == "__main__":
    unittest.main()
