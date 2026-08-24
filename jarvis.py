"""Launcher compatibile di Jarvis.

Il punto di ingresso ufficiale resta ``main.py``; questo launcher mantiene
la compatibilità con gli avvii precedenti senza riferimenti a versioni legacy.
"""

import time

from core.kernel import KernelJarvis
from interfaccia.hud import HUDJarvis


class JarvisOS:
    """Avvia e gestisce una sessione completa di Jarvis."""

    def __init__(self):
        self.kernel = KernelJarvis()
        self.hud = HUDJarvis()

    def avvia(self):
        print("""
================================
        J.A.R.V.I.S.
        VERSIONE DEFINITIVA
================================
""")

        risultato = self.kernel.avvia()
        if not risultato:
            print("Errore durante l'avvio.")
            return False

        self.hud.collega_kernel(self.kernel)
        self.hud.avvia()
        self.hud.aggiorna_kernel()
        self.hud.mostra()
        print("J.A.R.V.I.S. operativo.")
        return True

    def esegui(self):
        while True:
            try:
                comando = input("\nTu: ").strip()
                if comando.lower() in {"esci", "chiudi", "stop"}:
                    self.arresta()
                    break
                risposta = self.kernel.esegui_comando(comando)
                print("\nJ.A.R.V.I.S.:", risposta or "Comando non riconosciuto.")
            except KeyboardInterrupt:
                self.arresta()
                break

    def arresta(self):
        self.hud.ferma()
        self.kernel.arresta()
        print("J.A.R.V.I.S. spento.")


if __name__ == "__main__":
    jarvis = JarvisOS()
    if jarvis.avvia():
        time.sleep(1)
        jarvis.esegui()
