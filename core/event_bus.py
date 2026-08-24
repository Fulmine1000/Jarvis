import threading


class EventBus:
    """Bus eventi locale per il coordinamento dei componenti Jarvis."""

    def __init__(self):
        self.eventi = {}
        self._lock = threading.RLock()

    def registra(self, evento, funzione):
        if not callable(funzione):
            raise TypeError("La funzione dell'evento deve essere chiamabile.")
        with self._lock:
            self.eventi.setdefault(str(evento), []).append(funzione)

    def emetti(self, evento, dati=None):
        with self._lock:
            funzioni = list(self.eventi.get(str(evento), []))
        risultati = []
        for funzione in funzioni:
            try:
                risultati.append(funzione(dati))
            except Exception as errore:
                risultati.append(None)
        return risultati

    def rimuovi(self, evento, funzione):
        with self._lock:
            handlers = self.eventi.get(str(evento), [])
            if funzione in handlers:
                handlers.remove(funzione)
                if not handlers:
                    self.eventi.pop(str(evento), None)
                return True
        return False

    def pulisci(self, evento=None):
        with self._lock:
            if evento is None:
                self.eventi.clear()
            else:
                self.eventi.pop(str(evento), None)

    def conta(self, evento=None):
        with self._lock:
            if evento is None:
                return sum(len(v) for v in self.eventi.values())
            return len(self.eventi.get(str(evento), []))
