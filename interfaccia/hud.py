"""HUD ufficiale J.A.R.V.I.S. — interfaccia grafica avanzata.

L'HUD usa esclusivamente Tkinter/Canvas e viene disegnato in tempo reale.
Il design punta a un aspetto più realistico da computer di bordo: pannelli
tecnici, telemetria, griglia prospettica, scansione, particelle e un nucleo
centrale reattivo a ascolto/parlato.
"""

from __future__ import annotations

import datetime
import math
import os
import shutil
import socket
import threading
import time
import tkinter as tk


class HUDJarvis:
    # Palette tecnica: blu/ciano con accenti verdi e gialli.
    CYAN = "#67F7FF"
    CYAN_DIM = "#2A899A"
    BLUE = "#238FCB"
    BLUE_DARK = "#0B3D58"
    WHITE = "#E8FCFF"
    TEXT = "#A9D5DC"
    YELLOW = "#F5D84A"
    GREEN = "#25F06B"
    RED = "#FF5E6C"
    BG = "#01060A"
    GRID = "#06202A"
    PANEL = "#031018"
    PANEL_2 = "#061722"
    DIM = "#0A3444"

    def __init__(self, kernel=None, width=1500, height=900):
        self.nome = "J.A.R.V.I.S. HUD"
        self.versione = "definitiva"
        self.kernel = kernel
        self.width = width
        self.height = height

        self.attivo = False
        self.ascolto = False
        self.parlando = False
        self.dati = {}
        self.eventi = []

        # Stato dell'animazione.
        self.angolo = 0.0
        self.angolo2 = 0.0
        self.angolo3 = 0.0
        self.scan_angle = 0.0
        self._phase = 0.0
        self.pulse = 0.0
        self._avvio_timestamp = time.monotonic()

        self._thread = None
        self._ready = threading.Event()
        self._stop = threading.Event()
        self.finestra = None
        self.canvas = None

    # ------------------------------------------------------------------
    # Ciclo di vita
    # ------------------------------------------------------------------
    def avvia(self):
        """Avvia l'HUD come modulo autonomo."""
        if self.attivo:
            return True
        self._stop.clear()
        self._ready.clear()
        self._thread = threading.Thread(
            target=self._run_tk,
            name="JarvisHUD",
            daemon=True,
        )
        self._thread.start()
        self._ready.wait(timeout=3)
        return self.finestra is not None

    def _run_tk(self):
        self.attivo = True
        self._stop.clear()
        self._avvio_timestamp = time.monotonic()
        try:
            self.finestra = tk.Tk()
            self.finestra.title("J.A.R.V.I.S. — HUD")
            self.finestra.geometry(f"{self.width}x{self.height}")
            self.finestra.minsize(1100, 700)
            self.finestra.configure(bg=self.BG)
            self.finestra.protocol("WM_DELETE_WINDOW", self.ferma)

            self.canvas = tk.Canvas(
                self.finestra,
                bg=self.BG,
                highlightthickness=0,
                bd=0,
            )
            self.canvas.pack(fill="both", expand=True)
            self._ready.set()
            self._animazione()
            self.finestra.mainloop()
        except Exception as errore:
            self.registra_evento(f"HUD: {errore}")
            self._ready.set()
        finally:
            self.attivo = False
            self._stop.set()
            self.finestra = None
            self.canvas = None

    def ferma(self):
        self.attivo = False
        self._stop.set()
        try:
            if self.finestra:
                self.finestra.after_idle(self.finestra.destroy)
        except Exception:
            pass

    def collega_kernel(self, kernel):
        self.kernel = kernel
        self.registra_evento("Kernel collegato")

    def aggiorna(self, dati):
        self.dati = dati or {}

    def aggiorna_kernel(self):
        if self.kernel and hasattr(self.kernel, "stato_sistema"):
            try:
                self.dati = self.kernel.stato_sistema() or {}
            except Exception:
                pass

    def registra_evento(self, messaggio):
        self.eventi.append(
            (datetime.datetime.now().strftime("%H:%M:%S"), str(messaggio))
        )
        self.eventi = self.eventi[-30:]

    def imposta_ascolto(self, attivo=True):
        self.ascolto = bool(attivo)
        if self.ascolto:
            self.pulse = max(self.pulse, 18)

    def imposta_parlato(self, attivo=True):
        self.parlando = bool(attivo)
        if self.parlando:
            self.pulse = max(self.pulse, 30)

    def parla(self):
        self.imposta_parlato(True)

    # ------------------------------------------------------------------
    # Animazione
    # ------------------------------------------------------------------
    def _animazione(self):
        if not self.attivo or not self.canvas or self._stop.is_set():
            return

        self.aggiorna_kernel()
        self._phase += 0.055
        self._disegna()

        self.angolo = (self.angolo + 0.018) % (math.pi * 2)
        self.angolo2 = (self.angolo2 - 0.010) % (math.pi * 2)
        self.angolo3 = (self.angolo3 + 0.005) % (math.pi * 2)
        self.scan_angle = (self.scan_angle + 0.032) % (math.pi * 2)

        if self.ascolto or self.parlando:
            self.pulse = (self.pulse + 3.2) % 78
        elif self.pulse > 0:
            self.pulse *= 0.91
            if self.pulse < 1:
                self.pulse = 0

        try:
            if self.finestra and self.attivo and not self._stop.is_set():
                self.finestra.after(33, self._animazione)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Rendering principale
    # ------------------------------------------------------------------
    def _disegna(self):
        c = self.canvas
        c.delete("all")

        w = max(c.winfo_width(), 1100)
        h = max(c.winfo_height(), 700)
        cx = w * 0.50
        cy = h * 0.485
        r = min(w * 0.235, h * 0.325)

        self._sfondo(c, w, h)
        self._topbar(c, w)
        self._pannelli_laterali(c, w, h)
        self._central_hud(c, cx, cy, r)
        self._bottom_bar(c, w, h)

    # ------------------------------------------------------------------
    # Sfondo e struttura
    # ------------------------------------------------------------------
    def _sfondo(self, c, w, h):
        # Linee orizzontali da monitor tecnico.
        for y in range(44, h, 36):
            c.create_line(0, y, w, y, fill="#03151D", width=1)

        # Griglia verticale discreta.
        for x in range(24, w, 72):
            c.create_line(x, 44, x, h - 42, fill="#02121A", width=1)

        # Griglia prospettica nella parte bassa.
        horizon = h * 0.70
        for i in range(1, 10):
            y = horizon + (i * i) * 5.0
            if y < h - 42:
                c.create_line(0, y, w, y, fill=self.GRID, width=1)

        for x in range(-w, w * 2, 100):
            c.create_line(w / 2, horizon, x, h - 42, fill="#041922", width=1)

        # Micro-particelle in movimento: danno profondità senza appesantire.
        for i in range(34):
            px = (i * 173 + self._phase * (12 + i % 5) * 8) % w
            py = (i * 71 + math.sin(self._phase * 0.4 + i) * 18) % (h - 70) + 45
            size = 1 if i % 4 else 2
            c.create_oval(px, py, px + size, py + size, fill=self.DIM, outline="")

        # Angoli di mira ai quattro lati.
        self._corner_mark(c, 12, 48, 1, 1)
        self._corner_mark(c, w - 12, 48, -1, 1)
        self._corner_mark(c, 12, h - 48, 1, -1)
        self._corner_mark(c, w - 12, h - 48, -1, -1)

    @staticmethod
    def _corner_mark(c, x, y, sx, sy):
        c.create_line(x, y, x + sx * 24, y, fill="#0C4E60", width=1)
        c.create_line(x, y, x, y + sy * 24, fill="#0C4E60", width=1)
        c.create_line(x + sx * 5, y + sy * 5, x + sx * 14, y + sy * 5, fill="#17677B", width=1)

    def _topbar(self, c, w):
        uptime = int(time.monotonic() - self._avvio_timestamp)
        hh, rem = divmod(uptime, 3600)
        mm, ss = divmod(rem, 60)

        c.create_text(
            24, 20, anchor="w",
            text="J.A.R.V.I.S.",
            fill=self.WHITE,
            font=("Helvetica", 13, "bold"),
        )
        c.create_text(
            108, 20, anchor="w",
            text="NEURAL COMMAND INTERFACE",
            fill=self.CYAN_DIM,
            font=("Helvetica", 8, "bold"),
        )

        c.create_text(
            w * 0.42, 20,
            text="●  SYSTEM ONLINE",
            fill=self.GREEN,
            font=("Helvetica", 9, "bold"),
        )
        c.create_text(
            w * 0.61, 20,
            text=f"UPTIME {hh:02d}:{mm:02d}:{ss:02d}",
            fill=self.TEXT,
            font=("Helvetica", 8),
        )
        c.create_text(
            w - 24, 20, anchor="e",
            text="USER // SIMONE",
            fill=self.CYAN,
            font=("Helvetica", 9, "bold"),
        )
        c.create_line(12, 42, w - 12, 42, fill="#0A4A5C", width=1)
        c.create_line(24, 44, 220, 44, fill=self.CYAN, width=2)

    # ------------------------------------------------------------------
    # Pannelli
    # ------------------------------------------------------------------
    def _pannelli_laterali(self, c, w, h):
        left = (18, 58, 306, h - 62)
        right = (w - 306, 58, w - 18, h - 62)

        self._pannello(c, *left, "SYSTEM TELEMETRY")
        self._telemetria(c, 34, 98)
        self._mini_status(c, 34, 250)
        self._activity_graph(c, 34, 322, 290, 420)
        self._pannello_interno(c, 34, 450, 290, 600, "CORE MATRIX")
        self._core_matrix(c, 48, 480)
        self._pannello_interno(c, 34, 620, 290, h - 84, "QUICK ACCESS")
        self._quick_access(c, 48, 648)

        self._pannello(c, *right, "ENVIRONMENT / DEVICES")
        self._datetime_panel(c, w - 284, 98)
        self._weather_panel(c, w - 284, 190)
        self._pannello_interno(c, w - 284, 280, w - 34, 430, "CONNECTED DEVICES")
        self._devices_panel(c, w - 268, 312)
        self._pannello_interno(c, w - 284, 450, w - 34, 600, "VOICE CHANNEL")
        self._voice_panel(c, w - 268, 482)
        self._pannello_interno(c, w - 284, 620, w - 34, h - 84, "LIVE EVENT STREAM")
        self._event_stream(c, w - 268, 650, w - 48, h - 100)

    def _pannello(self, c, x1, y1, x2, y2, titolo):
        if y2 <= y1:
            return
        c.create_rectangle(x1, y1, x2, y2, fill=self.PANEL, outline="#0B5264", width=1)
        c.create_line(x1 + 12, y1 + 30, x2 - 42, y1 + 30, fill="#0A3D4B", width=1)
        c.create_text(
            x1 + 14, y1 + 15, anchor="w",
            text=titolo,
            fill=self.WHITE,
            font=("Helvetica", 9, "bold"),
        )
        c.create_line(x2 - 34, y1, x2, y1 + 34, fill=self.CYAN_DIM, width=1)
        c.create_line(x1, y2 - 25, x1 + 25, y2, fill="#0B5264", width=1)
        c.create_line(x2 - 25, y2, x2, y2 - 25, fill="#0B5264", width=1)

    def _pannello_interno(self, c, x1, y1, x2, y2, titolo):
        c.create_rectangle(x1, y1, x2, y2, fill=self.PANEL_2, outline="#0A3B4A", width=1)
        c.create_text(x1 + 9, y1 + 12, anchor="w", text=titolo, fill=self.CYAN_DIM, font=("Helvetica", 7, "bold"))
        c.create_line(x1 + 8, y1 + 22, x2 - 8, y1 + 22, fill="#0A3340", width=1)

    # ------------------------------------------------------------------
    # Telemetria
    # ------------------------------------------------------------------
    def _telemetria(self, c, x, y):
        for i, (name, value) in enumerate(self._system_metrics()):
            yy = y + i * 34
            c.create_text(x, yy, anchor="w", text=name, fill=self.TEXT, font=("Helvetica", 8, "bold"))
            c.create_text(x + 248, yy, anchor="e", text=f"{value:03d}%", fill=self.CYAN, font=("Helvetica", 8, "bold"))
            c.create_rectangle(x, yy + 9, x + 248, yy + 15, fill="#031A23", outline="#0A3947", width=1)
            fill_width = 248 * max(0, min(100, value)) / 100
            if fill_width > 0:
                c.create_rectangle(x + 1, yy + 10, x + fill_width, yy + 14, fill=self.BLUE, outline="")
            # marker mobile.
            marker_x = x + fill_width
            c.create_line(marker_x, yy + 7, marker_x, yy + 17, fill=self.CYAN, width=1)

    def _system_metrics(self):
        cpu = 0
        try:
            loads = os.getloadavg()
            cpu = int(min(100, max(0, (loads[0] / max(1, os.cpu_count() or 1)) * 100)))
        except Exception:
            pass

        ram = int(self.dati.get("ram", self.dati.get("RAM", 0)) or 0)
        ram = max(0, min(100, ram))

        disk = 0
        try:
            usage = shutil.disk_usage(os.path.expanduser("~"))
            disk = int((usage.used / usage.total) * 100) if usage.total else 0
        except Exception:
            pass

        network = 100 if self._network_online() else 0
        return [("CPU LOAD", cpu), ("MEMORY", ram), ("STORAGE", disk), ("NETWORK", network)]

    @staticmethod
    def _network_online():
        try:
            sock = socket.create_connection(("1.1.1.1", 53), timeout=0.15)
            sock.close()
            return True
        except Exception:
            return False

    def _mini_status(self, c, x, y):
        c.create_text(x, y, anchor="w", text="SECURITY", fill=self.TEXT, font=("Helvetica", 8, "bold"))
        c.create_text(x + 248, y, anchor="e", text="ACTIVE", fill=self.GREEN, font=("Helvetica", 8, "bold"))
        c.create_text(x, y + 24, anchor="w", text="MEMORY CORE", fill=self.TEXT, font=("Helvetica", 8, "bold"))
        c.create_text(x + 248, y + 24, anchor="e", text="SYNCED", fill=self.GREEN, font=("Helvetica", 8, "bold"))
        c.create_text(x, y + 48, anchor="w", text="AI ENGINE", fill=self.TEXT, font=("Helvetica", 8, "bold"))
        c.create_text(x + 248, y + 48, anchor="e", text="READY", fill=self.GREEN, font=("Helvetica", 8, "bold"))

    def _activity_graph(self, c, x1, y1, x2, y2):
        self._pannello_interno(c, x1, y1, x2, y2, "PROCESS ACTIVITY")
        base = y2 - 17
        points = []
        width = int(x2 - x1 - 20)
        for i in range(width):
            wave = math.sin(i * 0.16 + self._phase * 3.0) * 8
            wave += math.sin(i * 0.043 - self._phase) * 6
            if self.ascolto or self.parlando:
                wave += math.sin(i * 0.45 + self._phase * 4) * 8
            yy = base - 26 - wave
            points.extend((x1 + 10 + i, yy))
        if len(points) >= 4:
            c.create_line(*points, fill=self.CYAN, width=1, smooth=True)
        c.create_line(x1 + 10, base, x2 - 10, base, fill="#0A3442", width=1)
        for i in range(5):
            xx = x1 + 14 + i * ((x2 - x1 - 28) / 4)
            c.create_line(xx, y1 + 30, xx, y2 - 12, fill="#08232C", width=1)

    def _core_matrix(self, c, x, y):
        names = ["MEMORY", "SECURITY", "NETWORK", "AI ENGINE", "DEVICES", "HUD"]
        for i, name in enumerate(names):
            yy = y + i * 17
            c.create_oval(x, yy - 3, x + 6, yy + 3, fill=self.GREEN, outline="")
            c.create_text(x + 14, yy, anchor="w", text=name, fill=self.TEXT, font=("Helvetica", 7))
            c.create_text(276, yy, anchor="e", text="ONLINE", fill=self.GREEN, font=("Helvetica", 7, "bold"))

    def _quick_access(self, c, x, y):
        items = [("FILES", "□"), ("WEB", "◎"), ("CAM", "◈"), ("APP", "▦"),
                 ("NOTES", "✎"), ("CALC", "▣"), ("SET", "⚙"), ("TERM", ">_")]
        for i, (name, icon) in enumerate(items):
            col = i % 4
            row = i // 4
            xx = x + col * 59
            yy = y + row * 48
            c.create_rectangle(xx, yy, xx + 45, yy + 28, outline="#0E6479", fill="#04151D", width=1)
            c.create_text(xx + 22, yy + 14, text=icon, fill=self.CYAN, font=("Helvetica", 11, "bold"))
            c.create_text(xx + 22, yy + 38, text=name, fill="#78AEB6", font=("Helvetica", 6, "bold"))

    # ------------------------------------------------------------------
    # Pannello destro
    # ------------------------------------------------------------------
    def _datetime_panel(self, c, x, y):
        now = datetime.datetime.now()
        c.create_text(x, y, anchor="w", text=now.strftime("%H:%M:%S"), fill=self.CYAN, font=("Helvetica", 25, "bold"))
        c.create_text(x, y + 34, anchor="w", text=now.strftime("%A, %d %B %Y"), fill=self.TEXT, font=("Helvetica", 8))
        c.create_text(x + 248, y + 4, anchor="e", text="LOCAL", fill=self.CYAN_DIM, font=("Helvetica", 7, "bold"))

    def _weather_panel(self, c, x, y):
        c.create_text(x, y, anchor="w", text="WEATHER", fill=self.CYAN_DIM, font=("Helvetica", 7, "bold"))
        c.create_text(x, y + 22, anchor="w", text="CLOUD DATA READY", fill=self.GREEN, font=("Helvetica", 8, "bold"))
        c.create_text(x + 248, y + 22, anchor="e", text="ONLINE", fill=self.GREEN, font=("Helvetica", 7, "bold"))
        c.create_text(x, y + 42, anchor="w", text="Previsioni disponibili su richiesta", fill="#789DA4", font=("Helvetica", 7))

    def _devices_panel(self, c, x, y):
        names = [
            ("COMPUTER", "CONNECTED"),
            ("PHONE", "CONNECTED"),
            ("LG TV / webOS", "READY"),
            ("SMART HOME", "ONLINE"),
            ("BLUETOOTH", "READY"),
            ("WI-FI", "ONLINE"),
        ]
        for i, (name, status) in enumerate(names):
            yy = y + i * 18
            c.create_oval(x, yy - 3, x + 6, yy + 3, fill=self.GREEN, outline="")
            c.create_text(x + 14, yy, anchor="w", text=name, fill=self.TEXT, font=("Helvetica", 7))
            c.create_text(x + 234, yy, anchor="e", text=status, fill=self.GREEN, font=("Helvetica", 7, "bold"))

    def _voice_panel(self, c, x, y):
        state = "LISTENING" if self.ascolto else "SPEAKING" if self.parlando else "STANDBY"
        color = self.YELLOW if self.ascolto else self.CYAN if self.parlando else self.GREEN
        c.create_oval(x, y - 5, x + 10, y + 5, outline=color, width=2)
        c.create_text(x + 18, y, anchor="w", text=state, fill=color, font=("Helvetica", 10, "bold"))
        c.create_text(x + 248, y, anchor="e", text="AUDIO CHANNEL", fill=self.CYAN_DIM, font=("Helvetica", 7))
        self._wave(c, x, y + 24, x + 248, y + 53)
        c.create_text(x, y + 66, anchor="w", text="Wake word: JARVIS", fill="#7BABB2", font=("Helvetica", 7))
        c.create_text(x + 248, y + 66, anchor="e", text="READY", fill=self.GREEN, font=("Helvetica", 7, "bold"))

    def _event_stream(self, c, x1, y1, x2, y2):
        eventi = self.eventi[-6:]
        if not eventi:
            eventi = [(datetime.datetime.now().strftime("%H:%M:%S"), "HUD online")]
        yy = y1
        for ora, messaggio in reversed(eventi):
            if yy > y2:
                break
            text = str(messaggio).replace("\n", " ")
            if len(text) > 30:
                text = text[:27] + "..."
            c.create_text(x1, yy, anchor="w", text=ora, fill=self.CYAN_DIM, font=("Helvetica", 6, "bold"))
            c.create_text(x1 + 48, yy, anchor="w", text=text, fill=self.TEXT, font=("Helvetica", 6))
            yy += 18

    # ------------------------------------------------------------------
    # Nucleo centrale
    # ------------------------------------------------------------------
    def _central_hud(self, c, cx, cy, r):
        # Aureole concentriche con effetto di profondità.
        breathe = math.sin(self._phase * 0.8) * 3
        for extra, color, width in [
            (46 + breathe, "#082B38", 1),
            (35 + breathe * 0.7, "#0A5364", 1),
            (23 + breathe * 0.4, self.BLUE_DARK, 2),
        ]:
            rr = r + extra
            c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=color, width=width)

        # Halo durante attività vocale.
        if self.ascolto or self.parlando:
            for extra, width in [(58 + self.pulse, 1), (68 + self.pulse * 0.55, 1)]:
                rr = r + extra
                c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline="#12677A", width=width)

        # Sistema circolare principale.
        self._segment_ring(c, cx, cy, r + 16, 72, self.angolo, self.CYAN)
        self._segment_ring(c, cx, cy, r + 2, 54, self.angolo2, "#3DBBD0")
        self._segment_ring(c, cx, cy, r - 15, 44, self.angolo3, self.BLUE)
        self._segment_ring(c, cx, cy, r * 0.78, 32, -self.angolo2, "#14566C")

        self._ticks(c, cx, cy, r + 9)
        self._radial_data(c, cx, cy, r + 32)
        self._rotor(c, cx, cy, r * 0.72, self.angolo, 12)
        self._rotor(c, cx, cy, r * 0.58, -self.angolo2, 8)

        # Scanner rotante, con linea e arco di rilevamento.
        scan_r = r + 25
        start = math.degrees(self.scan_angle)
        c.create_arc(
            cx - scan_r, cy - scan_r, cx + scan_r, cy + scan_r,
            start=start, extent=30, style="arc", outline=self.CYAN, width=2,
        )
        sx, sy = self._polar(cx, cy, scan_r, self.scan_angle)
        c.create_line(cx, cy, sx, sy, fill="#0D6B7D", width=1)

        # Accento giallo: indicatore di stato/attività.
        yellow_start = (120 + math.degrees(self.angolo2) * 0.25) % 360
        c.create_arc(
            cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2,
            start=yellow_start, extent=58, style="arc", outline=self.YELLOW, width=5,
        )

        # Core centrale.
        core = r * 0.48
        self._reactor(c, cx, cy, core)

        # Testo stabile al centro.
        c.create_text(cx, cy - 8, text="J.A.R.V.I.S.", fill=self.WHITE,
                      font=("Helvetica", max(25, int(r * 0.105)), "bold"))
        c.create_text(cx, cy + 30, text="JUST A RATHER VERY INTELLIGENT SYSTEM",
                      fill="#62B7C6", font=("Helvetica", 7, "bold"))
        c.create_text(cx, cy + 50, text="NEURAL CORE // ONLINE",
                      fill=self.GREEN, font=("Helvetica", 7, "bold"))

        status = self._stato()
        status_color = self.GREEN if status == "SYSTEM ONLINE" else self.YELLOW
        c.create_text(cx, cy + r + 48, text=status, fill=status_color,
                      font=("Helvetica", 13, "bold"))
        c.create_text(cx, cy + r + 68,
                      text="VOICE CONTROL READY" if not self.ascolto and not self.parlando else "ACTIVE VOICE CHANNEL",
                      fill="#729DA5", font=("Helvetica", 7, "bold"))

    def _reactor(self, c, cx, cy, core):
        # Disco scuro per separare il nucleo dal resto dell'HUD.
        c.create_oval(cx - core, cy - core, cx + core, cy + core,
                      fill="#020B11", outline="#1B778A", width=2)
        c.create_oval(cx - core + 13, cy - core + 13, cx + core - 13, cy + core - 13,
                      outline="#0E3E4C", width=2)
        c.create_oval(cx - core * 0.73, cy - core * 0.73,
                      cx + core * 0.73, cy + core * 0.73,
                      outline="#15596A", width=1)

        # Segmenti interni simili a un reattore digitale.
        for i in range(12):
            a = self.angolo3 + i * (math.pi * 2 / 12)
            inner = core * 0.60
            outer = core * 0.80
            x1, y1 = self._polar(cx, cy, inner, a)
            x2, y2 = self._polar(cx, cy, outer, a)
            c.create_line(x1, y1, x2, y2,
                          fill=self.CYAN if i % 3 == 0 else "#175061", width=2)

        # Punto centrale pulsante.
        if self.ascolto:
            pulse_size = 15 + self.pulse * 0.18
            pulse_color = self.YELLOW
        elif self.parlando:
            pulse_size = 17 + self.pulse * 0.22
            pulse_color = self.CYAN
        else:
            pulse_size = 11 + math.sin(self._phase * 2) * 2
            pulse_color = self.CYAN_DIM

        c.create_oval(cx - pulse_size, cy - pulse_size, cx + pulse_size, cy + pulse_size,
                      fill="#031821", outline=pulse_color, width=2)
        c.create_oval(cx - 5, cy - 5, cx + 5, cy + 5,
                      fill=pulse_color, outline="")

        if self.pulse:
            rr = core * 0.48 + self.pulse
            c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr,
                          outline="#248BA0", width=1)

    def _segment_ring(self, c, cx, cy, radius, segments, angle, color):
        step = 360 / segments
        gap = max(1.5, step * 0.24)
        box = (cx - radius, cy - radius, cx + radius, cy + radius)
        for i in range(segments):
            if i % 2 == 0 or i % 7 == 0:
                start = math.degrees(angle) + i * step + gap * 0.5
                extent = step - gap
                c.create_arc(*box, start=start, extent=extent, style="arc", outline=color, width=2)

    def _ticks(self, c, cx, cy, radius):
        for i in range(72):
            a = self.angolo2 + i * (math.pi * 2 / 72)
            length = 12 if i % 6 == 0 else 6
            inner = radius
            outer = radius + length
            x1, y1 = self._polar(cx, cy, inner, a)
            x2, y2 = self._polar(cx, cy, outer, a)
            color = self.CYAN if i % 12 == 0 else "#155466"
            width = 2 if i % 12 == 0 else 1
            c.create_line(x1, y1, x2, y2, fill=color, width=width)

    def _rotor(self, c, cx, cy, radius, angle, count):
        for i in range(count):
            a = angle + i * (math.pi * 2 / count)
            p1 = self._polar(cx, cy, radius - 8, a)
            p2 = self._polar(cx, cy, radius + 5, a)
            c.create_line(*p1, *p2, fill="#2A8092", width=1)

    def _radial_data(self, c, cx, cy, radius):
        labels = ["MEM", "SEC", "NET", "AI", "DEV", "IO"]
        for i, label in enumerate(labels):
            a = self.angolo3 + i * (math.pi * 2 / len(labels))
            tx, ty = self._polar(cx, cy, radius, a)
            c.create_text(tx, ty, text=label, fill="#3D8998", font=("Helvetica", 6, "bold"))

    # ------------------------------------------------------------------
    # Audio waveform
    # ------------------------------------------------------------------
    def _wave(self, c, x1, y1, x2, y2):
        width = max(1, int(x2 - x1))
        center = (y1 + y2) / 2
        pts = []
        active = self.ascolto or self.parlando
        activity = 1.75 if active else 0.70
        for i in range(width):
            envelope = 0.35 + 0.65 * abs(math.sin(i * 0.035 + self._phase))
            amp = (3 + 9 * envelope) * activity
            wave = math.sin(i * 0.22 + self._phase * 5) * amp
            pts.extend((x1 + i, center + wave))
        if len(pts) >= 4:
            c.create_line(*pts, fill=self.CYAN, width=1, smooth=True)
        c.create_line(x1, center, x2, center, fill="#0A303B", width=1)

    # ------------------------------------------------------------------
    # Barra inferiore / console
    # ------------------------------------------------------------------
    def _bottom_bar(self, c, w, h):
        y1 = h - 43
        c.create_line(12, y1, w - 12, y1, fill="#0A4A5C", width=1)
        c.create_text(24, h - 22, anchor="w", text="JARVIS CORE", fill=self.CYAN_DIM,
                      font=("Helvetica", 7, "bold"))
        c.create_text(w * 0.28, h - 22, text="● MEMORY", fill=self.GREEN,
                      font=("Helvetica", 7, "bold"))
        c.create_text(w * 0.40, h - 22, text="● SECURITY", fill=self.GREEN,
                      font=("Helvetica", 7, "bold"))
        c.create_text(w * 0.53, h - 22, text="● DEVICES", fill=self.GREEN,
                      font=("Helvetica", 7, "bold"))
        c.create_text(w * 0.66, h - 22, text="● VOICE", fill=self.YELLOW if self.ascolto else self.GREEN,
                      font=("Helvetica", 7, "bold"))
        c.create_text(w - 24, h - 22, anchor="e", text="READY // AWAITING COMMAND",
                      fill=self.TEXT, font=("Helvetica", 7))

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def _stato(self):
        if self.kernel is not None:
            return "SYSTEM ONLINE"
        return "SYSTEM STANDBY"

    @staticmethod
    def _polar(cx, cy, radius, angle):
        return cx + math.cos(angle) * radius, cy + math.sin(angle) * radius


if __name__ == "__main__":
    hud = HUDJarvis()
    hud.registra_evento("HUD standalone avviato")
    hud.avvia()
