# DEPRECATO — mantenuto per riferimento storico.
# Il sistema grafico ufficiale usa ``interfaccia/hud.py``.
import math
import tkinter as tk


class InterfacciaJarvis:
    def __init__(self):
        self.finestra = tk.Tk()
        self.finestra.title("J.A.R.V.I.S")
        self.finestra.geometry("800x800")
        self.finestra.configure(bg="black")
        self.canvas = tk.Canvas(self.finestra, width=800, height=800, bg="black", highlightthickness=0)
        self.canvas.pack()
        self.angolo = 0
        self.impulso = 0
        self.stato = self.canvas.create_text(400, 650, text="SYSTEM ONLINE", fill="cyan", font=("Helvetica", 18))
        self.animazione()

    def animazione(self):
        self.canvas.delete("hud")
        cx, cy = 400, 350
        for r in [250, 220, 180, 130]:
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="cyan", width=2, tags="hud")
        for i in range(24):
            angolo = i * math.pi / 12 + self.angolo
            r1, r2 = 260, 230
            x1, y1 = cx + math.cos(angolo)*r1, cy + math.sin(angolo)*r1
            x2, y2 = cx + math.cos(angolo)*r2, cy + math.sin(angolo)*r2
            self.canvas.create_line(x1, y1, x2, y2, fill="cyan", width=3, tags="hud")
        self.canvas.create_oval(cx-70, cy-70, cx+70, cy+70, outline="cyan", width=4, tags="hud")
        self.canvas.create_text(cx, cy, text="J.A.R.V.I.S", fill="cyan", font=("Helvetica", 28, "bold"), tags="hud")
        if self.impulso > 0:
            self.canvas.create_oval(cx-self.impulso, cy-self.impulso, cx+self.impulso, cy+self.impulso, outline="cyan", width=2, tags="hud")
            self.impulso += 8
            if self.impulso > 350:
                self.impulso = 0
        self.angolo += 0.03
        self.finestra.after(40, self.animazione)

    def cambia_stato(self, testo):
        self.canvas.itemconfig(self.stato, text=testo)

    def parla(self):
        self.impulso = 80

    def avvia(self):
        self.finestra.mainloop()
