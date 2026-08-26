from __future__ import annotations

import ast
import datetime as dt
import os
import platform
import shutil
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import webbrowser


class CapacitaJarvis:
    """Strato operativo locale di Jarvis.

    Tutte le azioni sensibili sono esplicite e/o protette dal router dei comandi.
    Non esiste esecuzione arbitraria di shell proveniente dalla voce.
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.attivo = True
        self.timer = {}

    def _log(self, livello, messaggio):
        if self.logger and hasattr(self.logger, livello):
            getattr(self.logger, livello)(messaggio)

    def sistema(self):
        info = {
            "sistema": platform.system(),
            "versione": platform.version(),
            "architettura": platform.machine(),
            "computer": platform.node(),
            "python": platform.python_version(),
            "processore": platform.processor() or "non disponibile",
        }
        try:
            import psutil
            info.update({
                "cpu_percentuale": psutil.cpu_percent(interval=0.1),
                "ram_percentuale": psutil.virtual_memory().percent,
                "disco_percentuale": psutil.disk_usage(os.path.expanduser("~")).percent,
            })
        except Exception:
            pass
        return info

    def calcola(self, espressione):
        """Calcolatrice sicura: solo numeri e operatori matematici."""
        tree = ast.parse(espressione.replace("^", "**"), mode="eval")
        consentiti = (ast.Expression, ast.Constant, ast.BinOp, ast.UnaryOp,
                      ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
                      ast.Mod, ast.Pow, ast.USub, ast.UAdd, ast.LShift,
                      ast.RShift)
        if any(not isinstance(n, consentiti) for n in ast.walk(tree)):
            raise ValueError("Espressione non consentita")
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and not isinstance(n.value, (int, float)):
                raise ValueError("Valore non consentito")
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow):
                if abs(getattr(n.right, "value", 0)) > 100:
                    raise ValueError("Esponente troppo grande")
        return eval(compile(tree, "<jarvis-calcolo>", "eval"), {"__builtins__": {}}, {})

    def apri_url(self, url):
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        return f"Apro {url}."

    def cerca_web(self, query):
        url = "https://www.google.com/search?" + urllib.parse.urlencode({"q": query})
        webbrowser.open(url)
        return f"Cerco sul web: {query}."

    def apri_app(self, nome):
        nome = nome.strip()
        sistema = platform.system()
        alias = {
            "browser": ["Safari", "Google Chrome", "Firefox"],
            "safari": ["Safari"],
            "chrome": ["Google Chrome"],
            "calcolatrice": ["Calculator", "Calcolatrice"],
            "note": ["Notes", "Note"],
            "finder": ["Finder"],
            "terminal": ["Terminal"],
        }
        candidati = alias.get(nome.lower(), [nome])
        if sistema == "Darwin":
            for app in candidati:
                try:
                    subprocess.Popen(["open", "-a", app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return f"Apro {app}."
                except Exception:
                    continue
        elif sistema == "Linux":
            try:
                subprocess.Popen([nome], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Avvio {nome}."
            except Exception:
                pass
        elif sistema == "Windows":
            try:
                os.startfile(nome)
                return f"Avvio {nome}."
            except Exception:
                pass
        return f"Non riesco ad aprire {nome} su questo sistema."

    def apri_cartella(self, percorso="~"):
        percorso = os.path.abspath(os.path.expanduser(percorso))
        if not os.path.exists(percorso):
            return "La cartella richiesta non esiste."
        if platform.system() == "Darwin":
            subprocess.Popen(["open", percorso])
        elif platform.system() == "Windows":
            os.startfile(percorso)
        else:
            subprocess.Popen(["xdg-open", percorso])
        return "Cartella aperta."

    def screenshot(self, percorso=None):
        percorso = percorso or os.path.join(os.path.expanduser("~"), "Desktop", "jarvis_screenshot.png")
        if platform.system() == "Darwin" and shutil.which("screencapture"):
            subprocess.run(["screencapture", "-x", percorso], check=False)
            return f"Screenshot salvato in {percorso}."
        if platform.system() == "Windows":
            return "Screenshot automatico non disponibile con i soli strumenti integrati di Jarvis."
        if shutil.which("gnome-screenshot"):
            subprocess.run(["gnome-screenshot", "-f", percorso], check=False)
            return f"Screenshot salvato in {percorso}."
        return "Screenshot non disponibile su questo sistema."

    def volume(self, valore):
        valore = max(0, min(100, int(valore)))
        if platform.system() == "Darwin":
            subprocess.run(["osascript", "-e", f"set volume output volume {valore}"], check=False)
            return f"Volume impostato al {valore} percento."
        return "Controllo volume diretto non disponibile su questo sistema."

    def silenzia(self):
        if platform.system() == "Darwin":
            subprocess.run(["osascript", "-e", "set volume with output muted"], check=False)
            return "Audio disattivato."
        return "Silenziamento diretto non disponibile su questo sistema."

    def timer_avvia(self, secondi, nome="timer"):
        secondi = max(1, int(secondi))
        nome = nome.strip() or "timer"
        token = object()
        self.timer[nome] = token

        def lavoro():
            time.sleep(secondi)
            if self.timer.get(nome) is token:
                self.timer.pop(nome, None)
                self._log("info", f"Timer terminato: {nome}")
                if platform.system() == "Darwin":
                    subprocess.run(["osascript", "-e", f'display notification "Timer {nome} terminato" with title "J.A.R.V.I.S."'], check=False)

        threading.Thread(target=lavoro, daemon=True).start()
        return f"Timer {nome} impostato per {secondi} secondi."

    def timer_annulla(self, nome="timer"):
        if nome in self.timer:
            self.timer.pop(nome, None)
            return f"Timer {nome} annullato."
        return f"Non c'è un timer chiamato {nome}."

    def meteo(self, localita):
        try:
            query = urllib.parse.quote(localita)
            with urllib.request.urlopen(f"https://wttr.in/{query}?format=3", timeout=8) as risposta:
                testo = risposta.read().decode("utf-8", errors="replace").strip()
            return testo or "Non ho ricevuto dati meteo."
        except Exception:
            return "Non riesco a recuperare il meteo in questo momento."

    def ora(self):
        """Restituisce l'ora in una forma naturale e chiara per la voce."""
        adesso = dt.datetime.now()
        ore = adesso.hour
        minuti = adesso.minute

        numeri = {
            0: "zero", 1: "uno", 2: "due", 3: "tre", 4: "quattro",
            5: "cinque", 6: "sei", 7: "sette", 8: "otto", 9: "nove",
            10: "dieci", 11: "undici", 12: "dodici", 13: "tredici",
            14: "quattordici", 15: "quindici", 16: "sedici", 17: "diciassette",
            18: "diciotto", 19: "diciannove", 20: "venti", 21: "ventuno",
            22: "ventidue", 23: "ventitré", 24: "ventiquattro", 25: "venticinque",
            26: "ventisei", 27: "ventisette", 28: "ventotto", 29: "ventinove",
            30: "trenta", 31: "trentuno", 32: "trentadue", 33: "trentatré",
            34: "trentaquattro", 35: "trentacinque", 36: "trentasei", 37: "trentasette",
            38: "trentotto", 39: "trentanove", 40: "quaranta", 41: "quarantuno",
            42: "quarantadue", 43: "quarantatré", 44: "quarantaquattro", 45: "quarantacinque",
            46: "quarantasei", 47: "quarantasette", 48: "quarantotto", 49: "quarantanove",
            50: "cinquanta", 51: "cinquantuno", 52: "cinquantadue", 53: "cinquantatré",
            54: "cinquantaquattro", 55: "cinquantacinque", 56: "cinquantasei", 57: "cinquantasette",
            58: "cinquantotto", 59: "cinquantanove",
        }

        return f"Sono le {numeri[ore]} e {numeri[minuti]}."

    def data(self):
        giorni = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
        oggi = dt.datetime.now()
        return f"Oggi è {giorni[oggi.weekday()]} {oggi.strftime('%d/%m/%Y')}."

    def stato(self):
        return {"nome": "Capacità operative", "stato": "attivo", "timer_attivi": list(self.timer)}
