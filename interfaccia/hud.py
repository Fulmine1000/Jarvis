"""HUD grafico ufficiale J.A.R.V.I.S.

Design di riferimento: interfaccia circolare futuristica blu/ciano con anelli
concentrici, tacche radiali, segmenti dinamici, accento giallo e nucleo centrale.
Il modulo resta utilizzabile anche senza kernel: in quel caso mostra lo stato
locale dell'HUD.
"""

from __future__ import annotations

import datetime
import math
import random
import tkinter as tk


class HUDJarvis:
    """HUD desktop animato in stile Jarvis, senza dipendenze grafiche esterne."""

    CYAN = "#67F7FF"
    CYAN_SOFT = "#31BFD0"
    BLUE = "#238FCB"
    BLUE_DARK = "#0B2637"
    WHITE = "#DDFBFF"
    YELLOW = "#F5D84A"
    BG = "#020A10"

    def __init__(self, kernel=None, width=1000, height=760):
        self.nome = "J.A.R.V.I.S. HUD"
        self.attivo = False
        self.dati = {}
        self.eventi = []
        self.kernel = kernel
        self.width = width
        self.height = height
        self.angolo = 0.0
        self.pulse = 0.0
        self.ascolto = False
        self.parlando = False
        self._after_id = None
        self.finestra = None
        self.canvas = None

    def avvia(self):
        if self.attivo:
            return True
        self.attivo = True
        self.registra_evento("HUD avviato")
        if self.finestra is None:
            self._crea_finestra()
        self._animazione()
        return True

    def _crea_finestra(self):
        self.finestra = tk.Tk()
        self.finestra.title("J.A.R.V.I.S.")
        self.finestra.geometry(f"{self.width}x{self.height}")
        self.finestra.minsize(720, 600)
        self.finestra.configure(bg=self.BG)
        self.finestra.protocol("WM_DELETE_WINDOW", self.ferma)
        self.canvas = tk.Canvas(
            self.finestra,
            bg=self.BG,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

    def ferma(self):
        self.attivo = False
        self.registra_evento("HUD spento")
        if self._after_id and self.finestra:
            try:
                self.finestra.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = None
        if self.finestra:
            try:
                self.finestra.destroy()
            except Exception:
                pass
        self.finestra = None
        self.canvas = None

    def collega_kernel(self, kernel):
        self.kernel = kernel
        self.registra_evento("Kernel collegato")

    def aggiorna(self, dati):
        self.dati = dati or {}

    def aggiorna_kernel(self):
        if self.kernel and hasattr(self.kernel, "stato_sistema"):
            try:
                self.dati = self.kernel.stato_sistema()
            except Exception as errore:
                self.registra_evento(f"Errore aggiornamento kernel: {errore}")

    def registra_evento(self, messaggio):
        self.eventi.append({
            "ora": datetime.datetime.now().strftime("%H:%M:%S"),
            "evento": str(messaggio),
        })
        self.eventi = self.eventi[-50:]

    def imposta_ascolto(self, attivo=True):
        self.ascolto = bool(attivo)
        self.pulse = 25 if attivo else 0

    def imposta_parlato(self, attivo=True):
        self.parlando = bool(attivo)
        if attivo:
            self.pulse = max(self.pulse, 45)

    def parla(self):
        """Compatibilità con il vecchio modulo: attiva un impulso centrale."""
        self.imposta_parlato(True)

    def _animazione(self):
        if not self.attivo or not self.canvas:
            return
        self.aggiorna_kernel()
        self._disegna()
        self.angolo = (self.angolo + 0.018) % (math.pi * 2)
        if self.pulse > 0:
            self.pulse += 4
            if self.pulse > 150:
                self.pulse = 0
        if self.parlando and self.pulse == 0:
            self.parlando = False
        self._after_id = self.finestra.after(33, self._animazione)

    def _disegna(self):
        c = self.canvas
        c.delete("all")
        w = max(c.winfo_width(), self.width)
        h = max(c.winfo_height(), self.height)
        cx = w * 0.50
        cy = h * 0.48
        radius = min(w, h) * 0.34

        # Sfondo tecnico: griglia sottile e pannelli fantasma.
        self._griglia(c, w, h)
        self._pannelli(c, w, h)

        # Aura esterna.
        for extra, color, width in [
            (34, "#0D3545", 2),
            (26, "#125064", 2),
            (18, self.BLUE, 2),
        ]:
            r = radius + extra
            c.create_oval(cx-r, cy-r, cx+r, cy+r, outline=color, width=width)

        # Anello principale segmentato.
        self._anello_segmentato(c, cx, cy, radius + 3, 72, self.CYAN)
        self._anello_segmentato(c, cx, cy, radius - 22, 48, self.BLUE, offset=0.08)

        # Tacche radiali esterne.
        for i in range(64):
            a = self.angolo * 0.32 + i * (2 * math.pi / 64)
            r1 = radius + 10
            r2 = radius + (25 if i % 4 == 0 else 17)
            x1, y1 = self._polar(cx, cy, r1, a)
            x2, y2 = self._polar(cx, cy, r2, a)
            color = self.CYAN if i % 4 == 0 else self.CYAN_SOFT
            c.create_line(x1, y1, x2, y2, fill=color, width=2)

        # Rotori interni contrapposti.
        self._rotore(c, cx, cy, radius * 0.78, self.angolo, clockwise=True)
        self._rotore(c, cx, cy, radius * 0.67, -self.angolo * 1.25, clockwise=False)

        # Arco di stato giallo, come nell'immagine di riferimento.
        start = 135
        extent = 72
        c.create_arc(
            cx-radius+10, cy-radius+10, cx+radius-10, cy+radius-10,
            start=start, extent=extent, style="arc", outline=self.YELLOW, width=8,
        )
        for i in range(7):
            a = math.radians(start + i * (extent / 6))
            rr = radius - 4
            x, y = self._polar(cx, cy, rr, a)
            c.create_oval(x-3, y-3, x+3, y+3, fill=self.YELLOW, outline="")

        # Nucleo centrale.
        core_r = radius * 0.49
        c.create_oval(cx-core_r, cy-core_r, cx+core_r, cy+core_r,
                      fill="#03121B", outline=self.CYAN_SOFT, width=3)
        c.create_oval(cx-core_r+12, cy-core_r+12, cx+core_r-12, cy+core_r-12,
                      outline="#174C60", width=2)
        c.create_oval(cx-core_r*0.72, cy-core_r*0.72,
                      cx+core_r*0.72, cy+core_r*0.72,
                      outline="#2A7E96", width=1)

        # Impulso quando ascolta/parla.
        if self.ascolto or self.parlando or self.pulse:
            rr = core_r * 0.70 + self.pulse
            c.create_oval(cx-rr, cy-rr, cx+rr, cy+rr,
                          outline=self.CYAN, width=2)

        # Marchi cardinali e indicatori.
        self._indicatori(c, cx, cy, core_r)

        # Logo centrale.
        c.create_text(cx, cy-6, text="J.A.R.V.I.S.", fill=self.WHITE,
                      font=("Helvetica", max(22, int(radius * 0.105)), "bold"))
        stato = self._stato_testo()
        c.create_text(cx, cy+42, text=stato, fill=self.CYAN,
                      font=("Helvetica", 11, "bold"))

        # HUD informativo laterale, senza coprire il nucleo.
        self._info(c, w, h)

    def _griglia(self, c, w, h):
        spacing = 42
        for x in range(0, int(w), spacing):
            c.create_line(x, 0, x, h, fill="#061821", width=1)
        for y in range(0, int(h), spacing):
            c.create_line(0, y, w, y, fill="#061821", width=1)
        # Linee diagonali tecniche.
        for i in range(-int(h), int(w), 120):
            c.create_line(i, 0, i + h, h, fill="#071B25", width=1)

    def _pannelli(self, c, w, h):
        # Pannelli decorativi trasparenti simulati con contorni sottili.
        boxes = [
            (24, 34, 230, 112),
            (w-250, 42, w-28, 126),
            (28, h-142, 250, h-35),
            (w-270, h-158, w-28, h-38),
        ]
        for x1, y1, x2, y2 in boxes:
            c.create_rectangle(x1, y1, x2, y2, outline="#0B303C", width=1)
            c.create_line(x1, y1+18, x1+80, y1+18, fill="#174B5B", width=2)
            for y in range(int(y1+34), int(y2-8), 13):
                c.create_line(x1+12, y, x2-12, y, fill="#09232E", width=1)

    def _anello_segmentato(self, c, cx, cy, r, segments, color, offset=0):
        step = 360 / segments
        for i in range(segments):
            if i % 3 == 1:
                continue
            start = i * step + math.degrees(offset)
            c.create_arc(cx-r, cy-r, cx+r, cy+r,
                         start=start, extent=step*0.68,
                         style="arc", outline=color, width=2)

    def _rotore(self, c, cx, cy, r, angle, clockwise=True):
        direction = 1 if clockwise else -1
        for i in range(10):
            a = angle * direction + i * (2 * math.pi / 10)
            a2 = a + direction * 0.18
            x1, y1 = self._polar(cx, cy, r*0.88, a)
            x2, y2 = self._polar(cx, cy, r, a2)
            c.create_line(x1, y1, x2, y2, fill="#35AFC3", width=2)

    def _indicatori(self, c, cx, cy, r):
        labels = [(0, "A"), (90, "S"), (180, "D"), (270, "SYS")]
        for deg, label in labels:
            a = math.radians(deg)
            x, y = self._polar(cx, cy, r*0.92, a)
            c.create_text(x, y, text=label, fill="#57C9D8",
                          font=("Helvetica", 8, "bold"))

    def _info(self, c, w, h):
        sistema = self.dati.get("stato", "OFFLINE")
        memoria = self.dati.get("memoria", {})
        voce = self.dati.get("voce", {})
        stato_memoria = memoria.get("stato", "N/D") if isinstance(memoria, dict) else "N/D"
        voce_attiva = voce.get("stato", "N/D") if isinstance(voce, dict) else "N/D"
        colore = self.CYAN if str(sistema).lower() in ("operativo", "online", "avvio") else self.YELLOW

        c.create_text(35, h/2-80, anchor="w", text="SYSTEM STATUS",
                      fill=self.CYAN, font=("Helvetica", 10, "bold"))
        c.create_text(35, h/2-52, anchor="w", text=f"CORE   {sistema}",
                      fill=colore, font=("Helvetica", 9))
        c.create_text(35, h/2-30, anchor="w", text=f"MEMORY {stato_memoria}",
                      fill="#8EDAE3", font=("Helvetica", 9))
        c.create_text(35, h/2-8, anchor="w", text=f"VOICE  {voce_attiva}",
                      fill="#8EDAE3", font=("Helvetica", 9))

        ora = datetime.datetime.now().strftime("%H:%M:%S")
        c.create_text(w-35, h/2-80, anchor="e", text="J.A.R.V.I.S. CORE",
                      fill=self.CYAN, font=("Helvetica", 10, "bold"))
        c.create_text(w-35, h/2-52, anchor="e", text=f"TIME   {ora}",
                      fill="#8EDAE3", font=("Helvetica", 9))
        c.create_text(w-35, h/2-30, anchor="e", text="SECURITY  ACTIVE",
                      fill="#8EDAE3", font=("Helvetica", 9))
        c.create_text(w-35, h/2-8, anchor="e", text="NETWORK   READY",
                      fill="#8EDAE3", font=("Helvetica", 9))

    def _stato_testo(self):
        if self.ascolto:
            return "LISTENING"
        if self.parlando:
            return "SPEAKING"
        stato = self.dati.get("stato", "OFFLINE")
        return "SYSTEM ONLINE" if str(stato).lower() == "operativo" else str(stato).upper()

    @staticmethod
    def _polar(cx, cy, r, angle):
        return cx + math.cos(angle) * r, cy + math.sin(angle) * r

    def mostra(self):
        """Compatibilità: avvia l'HUD grafico."""
        return self.avvia()

    def cambia_stato(self, testo):
        self.dati["stato"] = testo

    def stato(self):
        return {
            "attivo": self.attivo,
            "dati": self.dati,
            "ascolto": self.ascolto,
            "parlando": self.parlando,
            "eventi": self.eventi[-10:],
        }


if __name__ == "__main__":
    hud = HUDJarvis()
    hud.aggiorna({"nome": "J.A.R.V.I.S.", "versione": "definitiva", "stato": "Operativo"})
    hud.avvia()
    hud.finestra.mainloop()
