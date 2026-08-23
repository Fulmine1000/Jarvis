import threading
import time

from voce.wake_word import WakeWordJarvis


class MotoreAscolto:
    """Ascolto continuo: wake word -> comando -> risposta, senza doppia sintesi."""

    def __init__(self, modulo_voce):
        self.modulo_voce = modulo_voce
        self.nome = "Motore Ascolto"
        self.attivo = False
        self.thread = None
        self.wake_word = WakeWordJarvis()

    def avvia(self):
        if self.attivo:
            return True
        self.attivo = True
        self.log("Motore ascolto Jarvis avviato.")
        self.thread = threading.Thread(target=self.ciclo, name="JarvisAudio", daemon=True)
        self.thread.start()
        return True

    def ciclo(self):
        while self.attivo and getattr(self.modulo_voce, "ascolto_attivo", False):
            try:
                testo = self.modulo_voce.ascolta_comando()
                if not testo:
                    time.sleep(0.1)
                    continue
                risultato = self.wake_word.controlla(testo)
                if not risultato or not risultato.get("attivato", False):
                    continue
                comando = risultato.get("comando", "").strip()
                if not comando:
                    self.modulo_voce.rispondi("Sono qui.")
                    continue
                self.log(f"Comando ricevuto: {comando}")
                # Kernel.esegui_comando gestisce già la risposta vocale.
                self.modulo_voce.kernel.esegui_comando(comando)
                self.wake_word.disattiva()
            except Exception as errore:
                self.log(f"Errore motore ascolto: {errore}")
                time.sleep(1)
            time.sleep(0.2)

    def ferma(self):
        self.attivo = False
        self.wake_word.disattiva()
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
