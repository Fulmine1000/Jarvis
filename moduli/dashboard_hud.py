"""Widget e comandi utili per il dashboard HUD di Jarvis.

Le richieste di rete vengono eseguite solo quando l'utente chiede meteo/notizie
o un test esplicito. Le note sono locali e la calcolatrice usa AST ristretto.
"""
from __future__ import annotations

import ast
import datetime as dt
import math
import os
import platform
import subprocess
import time
import urllib.parse
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTE_PATH = Path(os.environ.get("JARVIS_NOTE_PATH", str(ROOT / "data" / "hud_note.txt")))


class _CalcoloSicuro(ast.NodeVisitor):
    _binari = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.FloorDiv: lambda a, b: a // b,
        ast.Mod: lambda a, b: a % b,
        ast.Pow: lambda a, b: a ** b,
    }
    _unari = {ast.UAdd: lambda a: +a, ast.USub: lambda a: -a}

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Constant(self, node):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError("Sono ammessi solo numeri.")
        return node.value

    def visit_BinOp(self, node):
        op = self._binari.get(type(node.op))
        if op is None:
            raise ValueError("Operatore non consentito.")
        left, right = self.visit(node.left), self.visit(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 8:
            raise ValueError("Esponente troppo grande.")
        result = op(left, right)
        if isinstance(result, bool) or not isinstance(result, (int, float)):
            raise ValueError("Risultato non reale.")
        if not math.isfinite(float(result)) or abs(result) > 1e100:
            raise ValueError("Risultato fuori dai limiti.")
        return result

    def visit_UnaryOp(self, node):
        op = self._unari.get(type(node.op))
        if op is None:
            raise ValueError("Operatore non consentito.")
        return op(self.visit(node.operand))

    def generic_visit(self, node):
        raise ValueError("Espressione non consentita.")


def calcola_espressione(espressione: str):
    tree = ast.parse(str(espressione), mode="eval")
    if len(list(ast.walk(tree))) > 40:
        raise ValueError("Espressione troppo complessa.")
    return _CalcoloSicuro().visit(tree)


class DashboardHUD:
    """Funzioni di base per i widget HUD: ora, note, calcolo, meteo, notizie e rete."""

    def __init__(self, logger=None, note_path: Path | None = None):
        self.logger = logger
        self.note_path = Path(note_path) if note_path else NOTE_PATH

    @staticmethod
    def ora():
        now = dt.datetime.now()
        return now.strftime("Ora: %H:%M:%S — Data: %d/%m/%Y")

    def salva_nota(self, testo: str):
        testo = str(testo or "").strip()
        if not testo:
            return "Scrivi il testo della nota dopo 'nota'."
        if len(testo) > 5000:
            return "La nota supera il limite di 5000 caratteri."
        try:
            self.note_path.parent.mkdir(parents=True, exist_ok=True)
            self.note_path.write_text(testo + "\n", encoding="utf-8")
            return f"Nota salvata localmente in {self.note_path}."
        except OSError as exc:
            return f"Non sono riuscito a salvare la nota: {exc}"

    def leggi_nota(self):
        try:
            if not self.note_path.is_file():
                return "Non ci sono ancora note salvate."
            testo = self.note_path.read_text(encoding="utf-8").strip()
            return "Nota: " + (testo[:1500] or "(vuota)")
        except OSError as exc:
            return f"Non sono riuscito a leggere la nota: {exc}"

    @staticmethod
    def meteo(citta: str):
        citta = str(citta or "").strip() or "Napoli"
        url = "https://wttr.in/" + urllib.parse.quote(citta, safe="") + "?format=3"
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "JarvisHUD/1.0"})
            with urllib.request.urlopen(request, timeout=6) as response:
                value = response.read(1200).decode("utf-8", errors="replace").strip()
            return value if value else "Il servizio meteo non ha restituito dati."
        except Exception:
            return "Meteo non disponibile: verifica la connessione e riprova."

    @staticmethod
    def notizie():
        url = "https://feeds.bbci.co.uk/news/world/rss.xml"
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "JarvisHUD/1.0"})
            with urllib.request.urlopen(request, timeout=6) as response:
                payload = response.read(300_000)
            root = ET.fromstring(payload)
            items = root.findall("./channel/item")[:5]
            titles = [item.findtext("title", default="").strip() for item in items]
            titles = [title for title in titles if title]
            if not titles:
                return "Il feed notizie non contiene titoli."
            return "Ultime notizie: " + " | ".join(titles)
        except Exception:
            return "Notizie non disponibili: verifica la connessione e riprova."

    @staticmethod
    def test_velocita():
        try:
            import speedtest
        except Exception:
            return "Test completo non disponibile: installa facoltativamente 'speedtest-cli' e riprova."
        try:
            test = speedtest.Speedtest()
            test.get_best_server()
            download = test.download() / 1_000_000
            upload = test.upload() / 1_000_000
            ping = float(test.results.ping)
            return f"Rete: download {download:.1f} Mbps, upload {upload:.1f} Mbps, ping {ping:.0f} ms."
        except Exception:
            return "Test di velocità non riuscito: verifica la connessione e riprova."

    @staticmethod
    def apri_ologramma():
        """Apre il visualizzatore locale 3D; non scarica modelli o librerie."""
        viewer = ROOT / "interfaccia" / "ologramma_3d.html"
        if not viewer.is_file():
            return "Il visualizzatore 3D non è presente nella repository."
        try:
            from interfaccia.ologramma_3d_server import avvia_server
            url = avvia_server()
            opened = webbrowser.open(url)
            return "Visualizzatore 3D locale avviato con ponte gestuale." if opened else "Visualizzatore 3D disponibile a " + url
        except Exception:
            return "Non sono riuscito ad avviare il visualizzatore 3D locale."

    def gestisci_comando(self, comando: str):
        testo = " ".join(str(comando or "").strip().split())
        basso = testo.lower()
        if basso in ("apri ologramma 3d", "apri ologramma tridimensionale", "mostra modello 3d"):
            return self.apri_ologramma()
        if basso in ("che ora è", "che ore sono", "ora e data", "mostra ora e data"):
            return self.ora()
        if basso in ("leggi nota", "leggi le note", "mostra nota", "mostra le note"):
            return self.leggi_nota()
        if basso.startswith(("nota:", "scrivi nota ", "prendi nota ")):
            if ":" in testo[:12]:
                nota = testo.split(":", 1)[1].strip()
            else:
                nota = testo.split(" ", 2)[2].strip()
            return self.salva_nota(nota)
        if basso.startswith(("calcola ", "calcolatrice ")):
            expression = testo.split(" ", 1)[1].strip()
            try:
                return f"Risultato: {calcola_espressione(expression)}"
            except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
                return "Non posso calcolare questa espressione: usa soltanto numeri e operatori aritmetici."
        if basso == "meteo" or basso.startswith("meteo "):
            city = testo[5:].strip() if len(testo) > 5 else ""
            return self.meteo(city)
        if basso in ("notizie", "ultime notizie", "mostra notizie"):
            return self.notizie()
        if basso in ("test velocità rete", "test velocita rete", "misura velocità internet", "misura velocita internet"):
            return self.test_velocita()
        return None


__all__ = ["DashboardHUD", "calcola_espressione"]
