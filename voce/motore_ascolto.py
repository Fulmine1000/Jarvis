import threading
import time

from voce.wake_word import WakeWordJarvis


class MotoreAscolto:
    """Ascolto continuo: wake word -> comando -> risposta."""

    DUPLICATO_TIMEOUT = 1.5
    RISPOSTE_ECO = {"sono qui", "sono qui.", "sono qui!"}

    def __init__(self, modulo_voce):
        self.modulo_voce = modulo_voce
        self.nome = "Motore Ascolto"
        self.attivo = False
        self.thread = None
        self.wake_word = WakeWordJarvis()
        self._ultimo_testo = None
        self._ultimo_testo_timestamp = 0.0
        self._duplicate_lock = threading.Lock()

    def avvia(self):
        if self.attivo:
            return True
        self.attivo = True
        self._reset_duplicato()
        self.log("Motore ascolto Jarvis avviato.")
        self.thread = threading.Thread(target=self.ciclo, name="JarvisAudio", daemon=True)
        self.thread.start()
        return True

    @staticmethod
    def _normalizza_testo(testo):
        return " ".join(str(testo or "").lower().strip().split())

    def _e_duplicato_immediato(self, testo):
        normalizzato = self._normalizza_testo(testo)
        if not normalizzato:
            return False
        adesso = time.monotonic()
        with self._duplicate_lock:
            duplicato = (
                normalizzato == self._ultimo_testo
                and adesso - self._ultimo_testo_timestamp < self.DUPLICATO_TIMEOUT
            )
            self._ultimo_testo = normalizzato
            self._ultimo_testo_timestamp = adesso
            return duplicato

    def _reset_duplicato(self):
        with self._duplicate_lock:
            self._ultimo_testo = None
            self._ultimo_testo_timestamp = 0.0

    def _e_eco_jarvis(self, testo):
        """Ignora la frase prodotta da Jarvis e riascoltata dal microfono."""
        return self._normalizza_testo(testo) in self.RISPOSTE_ECO

    def _mostra_hud(self):
        """Porta l'HUD in primo piano dal Main Thread di Tkinter."""
        hud = getattr(self.modulo_voce.kernel, "hud", None)
        if not hud or not getattr(hud, "finestra", None):
            return
        try:
            hud.finestra.after(0, self._mostra_hud_main_thread, hud)
        except Exception as errore:
            self.log(f"Impossibile mostrare HUD: {errore}")

    @staticmethod
    def _mostra_hud_main_thread(hud):
        try:
            hud.finestra.deiconify()
            hud.finestra.lift()
            hud.finestra.attributes("-topmost", True)
            hud.finestra.after(250, lambda: hud.finestra.attributes("-topmost", False))
            hud.finestra.focus_force()
            hud.registra_evento("Wake word rilevata: HUD attivato")
        except Exception:
            pass

    def ciclo(self):
        while self.attivo and getattr(self.modulo_voce, "ascolto_attivo", False):
            try:
                testo = self.modulo_voce.ascolta_comando()
                if not testo:
                    time.sleep(0.1)
                    continue

                normalizzato = self._normalizza_testo(testo)

                if self._e_eco_jarvis(normalizzato):
                    self.log("Eco della risposta Jarvis ignorata: Sono qui.")
                    self._reset_duplicato()
                    continue

                if self._e_duplicato_immediato(normalizzato):
                    self.log(f"Trascrizione duplicata ignorata: {normalizzato}")
                    continue

                risultato = self.wake_word.controlla(normalizzato)
                if not risultato or not risultato.get("attivato", False):
                    continue

                # La finestra HUD viene mostrata quando viene riconosciuta
                # la wake word, senza richiedere alcun comando nel terminale.
                self._mostra_hud()

                comando = risultato.get("comando", "").strip()
                if not comando:
                    self.modulo_voce.rispondi("Sono qui.")
                    continue

                self.log(f"Comando ricevuto: {comando}")
                self.modulo_voce.kernel.esegui_comando(comando)
                self.wake_word.disattiva()
                self._reset_duplicato()

            except Exception as errore:
                self.log(f"Errore motore ascolto: {errore}")
                time.sleep(1)
            time.sleep(0.2)

    def ferma(self):
        self.attivo = False
        self.wake_word.disattiva()
        self._reset_duplicato()
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None
        self.log("Motore ascolto fermato.")
        return True

    def riavvia(self):
        self.ferma()
        time.sleep(0.2)
        return self.avvia()

    def log(self, messaggio):
        try:
            if self.modulo_voce and self.modulo_voce.kernel and self.modulo_voce.kernel.logger:
                self.modulo_voce.kernel.logger.info(messaggio)
            else:
                print(messaggio)
        except Exception:
            print(messaggio)

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo" if self.attivo else "spento",
            "thread": self.thread.is_alive() if self.thread else False,
            "wake_word": self.wake_word.stato(),
        }


def main():
    """Avvio standalone: `python -m voce.motore_ascolto` mantiene Jarvis in ascolto."""
    from core.kernel import KernelJarvis

    kernel = KernelJarvis()
    try:
        if not kernel.avvia():
            return 1

        voce = kernel.modulo_voce
        if not getattr(voce, "ascolto_attivo", False):
            print("Audio non disponibile: impossibile avviare l'ascolto vocale.")
            return 1

        print("Jarvis in ascolto. Di' 'Ehi Jarvis' oppure 'Hey Jarvis'. Premi Ctrl+C per uscire.")
        while kernel.stato == "Operativo" and not kernel.arresto_richiesto:
            time.sleep(0.5)
        return 0
    except KeyboardInterrupt:
        print("\nArresto richiesto.")
        return 0
    finally:
        kernel.arresta()


if __name__ == "__main__":
    raise SystemExit(main())
