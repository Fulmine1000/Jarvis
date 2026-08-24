"""Compatibilità del gestore comandi storico di Jarvis.

Il sistema ufficiale usa ``moduli.comandi_modulo``; questa implementazione
mantiene l'API precedente e delega allo stesso kernel quando disponibile.
"""

from datetime import datetime


class GestoreComandi:
    def __init__(self, memoria=None, personalita=None, dispositivi=None, kernel=None, logger=None):
        self.memoria = memoria
        self.personalita = personalita
        self.dispositivi = dispositivi
        self.kernel = kernel
        self.logger = logger
        self.attivo = False
        self.comandi_personalizzati = {}

    def avvia(self):
        self.attivo = True
        if self.logger:
            self.logger.info("Gestore comandi avviato.")
        return True

    def ferma(self):
        self.attivo = False
        return True

    def esegui(self, comando):
        comando = str(comando or "").strip().lower()
        if not comando:
            return "Comando vuoto."

        if comando in {"stato sistema", "stato"} and self.kernel:
            return str(self.kernel.stato_sistema())

        if "che ore sono" in comando:
            return f"Sono le {datetime.now():%H:%M}."

        if "che giorno è" in comando or comando == "data":
            return f"Oggi è il {datetime.now():%d/%m/%Y}."

        if "stato dispositivi" in comando and self.dispositivi:
            return str(self.dispositivi.stato_tutti())

        if "quali dispositivi" in comando and self.dispositivi:
            return str(self.dispositivi.elenco())

        if comando.startswith("ricorda "):
            testo = comando[8:]
            parti = testo.split(" è ", 1)
            if len(parti) == 2 and self.memoria:
                return self.memoria.ricorda(parti[0], parti[1])
            return "Non riesco a salvare il ricordo."

        if "cosa ricordi di me" in comando and self.memoria:
            return self.memoria.profilo.mostra_profilo()

        for nome, funzione in self.comandi_personalizzati.items():
            if nome.lower() in comando:
                return funzione()

        return "Non ho trovato un comando compatibile."

    def aggiungi_comando(self, nome, funzione):
        self.comandi_personalizzati[str(nome)] = funzione
        return f"Comando {nome} aggiunto."

    def stato(self):
        return {
            "nome": "Gestore Comandi",
            "stato": "attivo" if self.attivo else "spento",
        }
