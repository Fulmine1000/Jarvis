"""Test strutturali dell'HUD Qt Quick."""

from pathlib import Path
import re
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
        # Verifica il renderer effettivo, senza dipendere dal testo dei commenti.
        self.assertRegex(source, r"var pointCount\s*=\s*760\s*;")
        self.assertIn("var goldenAngle = Math.PI * (3.0 - Math.sqrt(5.0));", source)
        self.assertIn("var p3 = project(latP, lonP)", source)
        self.assertIn("points.sort(function(a, b) { return a.z - b.z; })", source)
        self.assertIn("Alone volumetrico molto leggero", source)
        self.assertIn("ctx.arc(point.x, point.y, dotSize", source)
        self.assertIn("interval: 42", source)
        self.assertIn("root.gestureZoom", source)
        self.assertIn("root.gestureTurn", source)
        self.assertNotIn("Punti energetici sulla superficie", source)
        self.assertNotIn("Meridiani e linee guida sferiche", source)
        self.assertNotIn("var sphere = ctx.createRadialGradient", source)
        self.assertNotIn("// Base discreta direttamente sotto la sfera", source)
        self.assertNotIn("ctx.ellipse(cx, cy + radius", source)

    def test_pannelli_hud_non_condividono_le_coordinate(self):
        source = HUD_QML.read_text(encoding="utf-8")

        # I pannelli laterali devono avere identità e geometrie indipendenti.
        left = re.search(
            r"Rectangle\s*\{\s*id: leftPanel\s*"
            r"x:\s*([^;\n]+);\s*y:\s*([^;\n]+);\s*"
            r"width:\s*([^;\n]+);\s*height:\s*([^\n]+)",
            source,
        )
        right = re.search(
            r"Rectangle\s*\{\s*id: rightPanel\s*"
            r"x:\s*([^;\n]+);\s*y:\s*([^;\n]+);\s*"
            r"width:\s*([^;\n]+);\s*height:\s*([^\n]+)",
            source,
        )
        self.assertIsNotNone(left, "Pannello sinistro non trovato")
        self.assertIsNotNone(right, "Pannello destro non trovato")
        self.assertNotEqual(left.group(1).strip(), right.group(1).strip())
        # La stessa quota verticale e intenzionale: i pannelli sono allineati.
        self.assertEqual(left.group(2).strip(), right.group(2).strip())
        # Larghezza e altezza uguali sono intenzionali; cambia la posizione orizzontale.
        self.assertEqual(left.group(3).strip(), right.group(3).strip())
        self.assertEqual(left.group(4).strip(), right.group(4).strip())
        self.assertIn("x: 22; y: root.height * 0.405; width: 265; height: 190", source)
        self.assertIn(
            "x: root.width - 287; y: root.height * 0.405; width: 265; height: 190",
            source,
        )

        # La zona centrale resta dimensionata in modo autonomo dai pannelli.
        self.assertIn("id: hologram", source)
        self.assertIn("width: root.width - 664", source)
        self.assertIn("height: root.height - 290", source)
        self.assertIn("var radius = Math.min(260", source)
        self.assertIn('rgba(65,235,255,0.15)', source)
        self.assertNotIn("#ffad42", source)


if __name__ == "__main__":
    unittest.main()
