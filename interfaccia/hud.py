"""HUD ufficiale J.A.R.V.I.S. — interfaccia grafica animata.

L'HUD resta una normale interfaccia Tkinter: nessun video o immagine esterna.
Il movimento è generato in tempo reale, soprattutto attorno al nucleo
J.A.R.V.I.S., così il nome centrale rimane leggibile mentre il sistema
circolare continua a muoversi.
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
    CYAN = "#67F7FF"
    BLUE = "#238FCB"
    WHITE = "#DDFBFF"
    YELLOW = "#F5D84A"
    GREEN = "#25F06B"
    BG = "#02080D"
    GRID = "#061821"
    PANEL = "#041018"
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

        # Angoli separati: gli anelli ruotano a velocità e direzioni diverse.
        self.angolo = 0.0
        self.angolo2 = 0.0
        self.angolo3 = 0.0
        self.angolo4 = 0.0
        self.pulse = 0.0
        self._phase = 0.0
        self._avvio_timestamp = time.monotonic()

        self._thread = None
        self._ready = threading.Event()
        self._stop = threading.Event()
        self.finestra = None
        self.canvas = None

    def avvia(self):
        """Avvia l'HUD quando viene usato come modulo autonomo."""
        if self.attivo:
            return True
        self._stop.clear()
        self._ready.clear()
        self._thread = threading.Thread(
            target=self._run_tk, name="JarvisHUD", daemon=True
        )
        self._thread.start()
        self._ready.wait(timeout=3)
        return self.finestra is not None

    def _run_tk(self):
        """Crea e gestisce Tkinter nel thread chiamante."""
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
        if attivo:
            self.pulse = max(self.pulse, 15)

    def imposta_parlato(self, attivo=True):
        self.parlando = bool(attivo)
        if attivo:
            self.pulse = max(self.pulse, 35)

    def parla(self):
        self.imposta_parlato(True)

    def _animazione(self):
        if not self.attivo or not self.canvas or self._stop.is_set():
            return

        self.aggiorna_kernel()
        self._phase += 0.10
        self._disegna()

        # Rotazione continua e indipendente degli elementi concentrici.
        self.angolo = (self.angolo + 0.024) % (math.pi * 2)
        self.angolo2 = (self.angolo2 - 0.015) % (math.pi * 2)
        self.angolo3 = (self.angolo3 + 0.008) % (math.pi * 2)
        self.angolo4 = (self.angolo4 - 0.004) % (math.pi * 2)

        if self.ascolto or self.parlando:
            self.pulse = (self.pulse + 4.5) % 88
        elif self.pulse > 0:
            self.pulse *= 0.90
            if self.pulse < 1:
                self.pulse = 0

        try:
            if self.finestra and self.attivo and not self._stop.is_set():
                self.finestra.after(33, self._animazione)
        except Exception:
            pass

    def _disegna(self):
        c = self.canvas
        c.delete("all")
        w = max(c.winfo_width(), 1100)
        h = max(c.winfo_height(), 700)
        cx, cy = w * 0.50, h * 0.485
        r = min(w * 0.255, h * 0.355)

        self._griglia(c, w, h)
        self._topbar(c, w)

        left_bottom = max(625, h - 105)
        right_bottom = max(625, h - 105)

        self._pannello(c, 20, 55, 300, 210, "SYSTEM STATUS")
        self._system_values(c, 38, 88)
        self._pannello(c, 20, 280, 300, 425, "VOICE STATUS")
        self._wave(c, 45, 350, 270, 385)
        voice = "LISTENING..." if self.ascolto else "SPEAKING..." if self.parlando else "VOICE READY"
        c.create_text(157, 415, text=voice, fill=self.CYAN, font=("Helvetica", 13, "bold"))
        self._pannello(c, 20, 445, 300, 615, "CORE SYSTEMS")
        self._core_values(c, 40, 478)
        self._pannello(c, 20, 635, 300, left_bottom, "SHORTCUTS")
        self._shortcuts(c, 42, 655)

        self._pannello(c, w - 320, 55, w - 20, 205, "DATE & TIME")
        self._datetime_panel(c, w - 300, 95)
        self._pannello(c, w - 320, 225, w - 20, 405, "WEATHER")
        self._weather_panel(c, w - 300, 270)
        self._pannello(c, w - 320, 425, w - 20, 625, "ACTIVE DEVICES")
        self._devices_panel(c, w - 300, 465)
        self._pannello(c, w - 320, 645, w - 20, right_bottom, "VOICE INPUT")
        self._wave(c, w - 300, 700, w - 45, 735)
        c.create_text(
            w - 173,
            770,
            text="Hey Jarvis...",
            fill=self.CYAN,
            font=("Helvetica", 12),
        )

        # Nucleo centrale: il nome resta stabile, mentre tutto il sistema
        # circolare intorno ad esso è animato.
        self._central_hud(c, cx, cy, r)

        self._bottom_nav(c, w, h)
        self._console(c, 325, h - 86, w - 325, h - 18)

    def _central_hud(self, c, cx, cy, r):
        # Aureole molto sottili: danno profondità senza trasformare l'HUD
        # in un'interfaccia da videogioco.
        breathe = math.sin(self._phase * 0.55) * 2.0
        for extra, color, width in [
            (37 + breathe, "#0A3444", 2),
            (25 + breathe * 0.6, self.BLUE, 2),
            (9 + breathe * 0.3, self.CYAN, 2),
        ]:
            rr = r + extra
            c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=color, width=width)

        # Anello principale segmentato: movimento costante, non a scatti.
        self._segment_ring(c, cx, cy, r + 17, 72, self.angolo, self.CYAN)
        self._segment_ring(c, cx, cy, r - 5, 54, self.angolo2, "#42CBE0")
        self._segment_ring(c, cx, cy, r * 0.79, 42, self.angolo3, self.BLUE)
        self._segment_ring(c, cx, cy, r * 0.66, 30, self.angolo4, "#17627A")

        # Tacche esterne rotanti.
        self._ticks(c, cx, cy, r + 8)
        self._rotor(c, cx, cy, r * 0.70, self.angolo, 12)
        self._rotor(c, cx, cy, r * 0.59, self.angolo2, 9)

        # Indicatore giallo: piccolo arco di stato che gira lentamente.
        yellow_start = (128 + math.degrees(self.angolo2) * 0.22) % 360
        c.create_arc(
            cx - r + 2,
            cy - r + 2,
            cx + r - 2,
            cy + r - 2,
            start=yellow_start,
            extent=66,
            style="arc",
            outline=self.YELLOW,
            width=6,
        )
        for i in range(8):
            a = math.radians(yellow_start + i * 9)
            x, y = self._polar(cx, cy, r - 3, a)
            c.create_oval(x - 3, y - 3, x + 3, y + 3, fill=self.YELLOW, outline="")

        core = r * 0.48
        c.create_oval(
            cx - core,
            cy - core,
            cx + core,
            cy + core,
            fill="#031019",
            outline="#39B8CD",
            width=3,
        )
        c.create_oval(
            cx - core + 15,
            cy - core + 15,
            cx + core - 15,
            cy + core - 15,
            outline="#164C5D",
            width=2,
        )
        c.create_oval(
            cx - core * 0.68,
            cy - core * 0.68,
            cx + core * 0.68,
            cy + core * 0.68,
            outline="#23778A",
            width=1,
        )

        if self.pulse:
            # Il pulse compare e scompare verso l'esterno: durante ascolto
            # e parlato rende evidente che il nucleo sta lavorando.
            pr = core * 0.65 + self.pulse
            c.create_oval(
                cx - pr,
                cy - pr,
                cx + pr,
                cy + pr,
                outline=self.CYAN,
                width=2,
            )

        # Nome centrale volutamente fermo.
        c.create_text(
            cx,
            cy - 5,
            text="J.A.R.V.I.S.",
            fill=self.WHITE,
            font=("Helvetica", max(24, int(r * 0.105)), "bold"),
        )
        c.create_text(
            cx,
            cy + 35,
            text="JUST A RATHER VERY INTELLIGENT SYSTEM",
            fill="#69C7D5",
            font=("Helvetica", 8, "bold"),
        )
        c.create_text(
            cx,
            cy + 59,
            text="VERSION DEFINITIVA",
            fill="#69C7D5",
            font=("Helvetica", 8),
        )

        status = self._stato()
        c.create_text(
            cx,
            cy + r + 30,
            text=status,
            fill=self.GREEN if status == "SYSTEM ONLINE" else self.CYAN,
            font=("Helvetica", 14, "bold"),
        )
        c.create_text(
            cx,
            cy + r + 51,
            text=(
                "TUTTI I SISTEMI OPERATIVI"
                if status == "SYSTEM ONLINE"
                else "IN ATTESA DI ISTRUZIONI"
            ),
            fill="#7FAEB5",
            font=("Helvetica", 8, "bold"),
        )

    def _topbar(self, c, w):
        uptime = int(time.monotonic() - self._avvio_timestamp)
        hh, rem = divmod(uptime, 3600)
        mm, ss = divmod(rem, 60)
        stato = "ONLINE" if self.dati else "STARTING"
        c.create_text(
            22,
            18,
            anchor="w",
            text="J.A.R.V.I.S.  DEFINITIVA",
            fill=self.WHITE,
            font=("Helvetica", 11, "bold"),
        )
        c.create_text(
            w * 0.28,
            18,
            text="// STATUS: ",
            fill="#777F83",
            font=("Helvetica", 9),
        )
        c.create_text(
            w * 0.32,
            18,
            text=stato,
            fill=self.GREEN,
            font=("Helvetica", 9, "bold"),
        )
        c.create_text(
            w * 0.52,
            18,
            text=f"// TEMPO DI ATTIVITÀ: {hh:02d}:{mm:02d}:{ss:02d}",
            fill="#72C8D5",
            font=("Helvetica", 9),
        )
        c.create_text(
            w - 22,
            18,
            anchor="e",
            text="// UTENTE: SIMONE",
            fill=self.CYAN,
            font=("Helvetica", 9, "bold"),
        )
        c.create_line(10, 36, w - 10, 36, fill="#0B5669", width=1)

    def _pannello(self, c, x1, y1, x2, y2, titolo):
        if y2 <= y1:
            return
        c.create_rectangle(x1, y1, x2, y2, outline="#0C6B82", width=1)
        c.create_line(x1, y1 + 26, x2 - 35, y1 + 26, fill="#0B5264", width=1)
        c.create_text(
            x1 + 15,
            y1 + 14,
            text=titolo,
            anchor="w",
            fill=self.WHITE,
            font=("Helvetica", 10, "bold"),
        )
        c.create_line(x2 - 35, y1, x2, y1 + 35, fill=self.CYAN, width=1)
        c.create_line(x1, y2 - 18, x1 + 28, y2, fill="#0C6B82", width=1)

    def _system_values(self, c, x, y):
        values = self._system_metrics()
        for i, (name, value) in enumerate(values):
            yy = y + i * 27
            c.create_text(x, yy, anchor="w", text=name, fill="#D1EEF2", font=("Helvetica", 8))
            c.create_rectangle(x + 55, yy - 6, x + 190, yy + 3, outline="#124A5A", width=1)
            bar = max(0, min(100, value))
            c.create_rectangle(
                x + 56,
                yy - 5,
                x + 56 + 1.33 * bar,
                yy + 2,
                fill=self.BLUE,
                outline="",
            )
            c.create_text(x + 235, yy, text=f"{bar}%", fill=self.CYAN, font=("Helvetica", 8))

    def _system_metrics(self):
        cpu = 0
        try:
            loads = os.getloadavg()
            cpu = int(min(100, max(0, (loads[0] / max(1, os.cpu_count() or 1)) * 100)))
        except Exception:
            pass

        ram = 0
        try:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            total = pages * page_size
            # macOS non espone sempre la memoria usata in modo portabile;
            # usiamo un indicatore prudente quando non è disponibile.
            ram = int(self.dati.get("ram", self.dati.get("RAM", 0)) or 0)
            if not ram and total:
                ram = 0
        except Exception:
            pass

        disk = 0
        try:
            usage = shutil.disk_usage(os.path.expanduser("~"))
            disk = int((usage.used / usage.total) * 100) if usage.total else 0
        except Exception:
            pass

        network = 100 if self._network_online() else 0
        return [("CPU", cpu), ("RAM", ram), ("DISK", disk), ("NETWORK", network)]

    @staticmethod
    def _network_online():
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=0.15).close()
            return True
        except Exception:
            return False

    def _core_values(self, c, x, y):
        names = ["MEMORY", "SECURITY", "NETWORK", "AI ENGINE", "DEVICES", "HUD INTERFACE"]
        for i, name in enumerate(names):
            yy = y + i * 21
            c.create_text(x, yy, anchor="w", text=name, fill="#C4E8ED", font=("Helvetica", 8))
            c.create_text(275, yy, anchor="e", text="ONLINE", fill=self.GREEN, font=("Helvetica", 8, "bold"))

    def _shortcuts(self, c, x, y):
        names = ["FILE", "WEB", "CAMERA", "APP", "NOTES", "CALC", "SETTINGS", "TERMINAL"]
        icons = ["□", "◉", "◈", "▦", "✎", "▣", "⚙", ">_"]
        for i, name in enumerate(names):
            col, row = i % 4, i // 4
            xx, yy = x + col * 62, y + row * 55
            c.create_rectangle(xx, yy, xx + 40, yy + 28, outline="#1484A0", width=1)
            c.create_text(xx + 20, yy + 14, text=icons[i], fill=self.CYAN, font=("Helvetica", 13, "bold"))
            c.create_text(xx + 20, yy + 40, text=name, fill="#9DD8DF", font=("Helvetica", 6))

    def _datetime_panel(self, c, x, y):
        now = datetime.datetime.now()
        c.create_text(x, y, anchor="w", text=now.strftime("%H:%M:%S"), fill=self.CYAN, font=("Helvetica", 24, "bold"))
        c.create_text(x, y + 35, anchor="w", text=now.strftime("%A, %d %B %Y"), fill="#B9DDE2", font=("Helvetica", 8))

    def _weather_panel(self, c, x, y):
        c.create_text(x, y, anchor="w", text="☁  METEO", fill=self.CYAN, font=("Helvetica", 12, "bold"))
        c.create_text(x, y + 28, anchor="w", text="DATI ONLINE", fill=self.GREEN, font=("Helvetica", 8))
        c.create_text(x, y + 54, anchor="w", text="Previsioni disponibili su richiesta", fill="#86B7BE", font=("Helvetica", 7))

    def _devices_panel(self, c, x, y):
        names = ["PC PRINCIPALE", "SMARTPHONE", "LG TV (webOS)", "SMART HOME", "BLUETOOTH", "WI-FI"]
        for i, name in enumerate(names):
            yy = y + i * 23
            c.create_text(x, yy, anchor="w", text=name, fill="#B9DDE2", font=("Helvetica", 8))
            c.create_text(x + 250, yy, anchor="e", text="ONLINE", fill=self.GREEN, font=("Helvetica", 8, "bold"))

    def _wave(self, c, x1, y1, x2, y2):
        pts = []
        width = max(1, int(x2 - x1))
        center = (y1 + y2) / 2
        activity = 1.55 if self.ascolto or self.parlando else 0.72
        for i in range(width):
            amp = (4 + 8 * abs(math.sin((i + self.angolo * 80) * 0.19))) * activity
            yy = center + math.sin(i * 0.33 + self.angolo * 9) * amp
            pts.extend([x1 + i, yy])
        if len(pts) >= 4:
            c.create_line(*pts, fill=self.CYAN, width=2, smooth=True)

    def _console(self, c, x1, y1, x2, y2):
        c.create_rectangle(x1, y1, x2, y2, outline="#0A586B", width=1)
        lines = [
            ">> INIZIALIZZAZIONE JARVIS... COMPLETATA",
            ">> CARICAMENTO MODULI... COMPLETATO",
            ">> SISTEMI ONLINE",
            ">> PRONTO PER ISTRUZIONI",
        ]
        for i, line in enumerate(lines):
            c.create_text(x1 + 12, y1 + 12 + i * 13, anchor="nw", text=line, fill=self.GREEN, font=("Courier", 7))

    def _bottom_nav(self, c, w, h):
        names = ["⌂  HOME", "▤  MEMORIA", "▣  DISPOSITIVI", "♧  RETE", "♢  SICUREZZA", "✣  PLUGIN", "⚙  IMPOSTAZIONI"]
        gap = 5
        width = (w - 30 - (len(names) - 1) * gap) / len(names)
        y1, y2 = h - 58, h - 20
        for i, name in enumerate(names):
            x1 = 15 + i * (width + gap)
            x2 = x1 + width
            c.create_rectangle(x1, y1, x2, y2, outline="#0D7A93", width=1)
            c.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=name, fill=self.CYAN, font=("Helvetica", 8, "bold"))

    def _griglia(self, c, w, h):
        for x in range(0, int(w), 45):
            c.create_line(x, 0, x, h, fill=self.GRID)
        for y in range(0, int(h), 45):
            c.create_line(0, y, w, y, fill=self.GRID)
        for i in range(-int(h), int(w), 140):
            c.create_line(i, 0, i + h, h, fill="#071B25")

    def _segment_ring(self, c, cx, cy, r, count, rotation, color):
        step = 2 * math.pi / count
        for i in range(count):
            if i % 3 == 1:
                continue
            a = rotation + i * step
            c.create_arc(
                cx - r,
                cy - r,
                cx + r,
                cy + r,
                start=math.degrees(a),
                extent=math.degrees(step * 0.62),
                style="arc",
                outline=color,
                width=2,
            )

    def _ticks(self, c, cx, cy, r):
        for i in range(64):
            a = self.angolo * 0.15 + i * 2 * math.pi / 64
            r2 = r + (17 if i % 4 == 0 else 10)
            x1, y1 = self._polar(cx, cy, r, a)
            x2, y2 = self._polar(cx, cy, r2, a)
            c.create_line(x1, y1, x2, y2, fill=self.CYAN if i % 4 == 0 else "#2D94A6", width=2)

    def _rotor(self, c, cx, cy, r, rotation, count):
        for i in range(count):
            a = rotation + i * 2 * math.pi / count
            x1, y1 = self._polar(cx, cy, r * 0.87, a)
            x2, y2 = self._polar(cx, cy, r, a + 0.14)
            c.create_line(x1, y1, x2, y2, fill="#3DB8C9", width=2)

    @staticmethod
    def _polar(cx, cy, r, a):
        return cx + math.cos(a) * r, cy + math.sin(a) * r

    def _stato(self):
        if self.parlando:
            return "SPEAKING"
        if self.ascolto:
            return "LISTENING"
        stato = self.dati.get("stato", "Operativo")
        return "SYSTEM ONLINE" if stato == "Operativo" else str(stato).upper()

    def mostra(self):
        return self.avvia() if not self.attivo else True

    def cambia_stato(self, testo):
        self.dati["stato"] = testo

    def stato(self):
        return {
            "nome": self.nome,
            "versione": self.versione,
            "attivo": self.attivo,
            "ascolto": self.ascolto,
            "parlando": self.parlando,
            "dati": self.dati,
            "eventi": self.eventi[-10:],
        }


if __name__ == "__main__":
    hud = HUDJarvis()
    hud.avvia()
    if hud._thread:
        hud._thread.join()
