from __future__ import annotations

import datetime


class GestoreComandi:
    """Router centrale dei comandi vocali/testuali di Jarvis."""

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
            self.logger.info("Gestore comandi Jarvis 3.1 avviato.")
        return True

    def esegui(self, comando):
        if not comando or not comando.strip():
            return "Comando vuoto."
        comando = comando.strip().lower()
        if self.kernel and hasattr(self.kernel, "sicurezza"):
            if self.kernel.sicurezza.richiede_conferma(comando) and "confermo" not in comando:
                self.kernel.sicurezza.registra("Comando protetto richiesto", comando)
                return "Questo comando richiede conferma. Aggiungi 'confermo' per autorizzarlo."
        risposta = self._esegui_raw(comando)
        if self.kernel and hasattr(self.kernel, "contesto"):
            try:
                self.kernel.contesto.aggiorna(comando, risposta)
            except Exception:
                pass
        return risposta

    def _esegui_raw(self, comando):
        # Sistema
        if comando in ("stato sistema", "stato del sistema"):
            return str(self.kernel.stato_sistema_modulo.completo()) if self.kernel else "Sistema non disponibile."
        if "stato dispositivi" in comando:
            return str(self.dispositivi.stato_tutti()) if self.dispositivi else "Gestore dispositivi non disponibile."
        if "quali dispositivi" in comando:
            return str(self.dispositivi.elenco()) if self.dispositivi else "Nessun dispositivo registrato."

        # Ora/data
        if "che ore sono" in comando:
            return f"Sono le {datetime.datetime.now().strftime('%H:%M')}."
        if "che giorno è" in comando or "che data è" in comando:
            return f"Oggi è il {datetime.datetime.now().strftime('%d/%m/%Y')}."

        # Personalità
        if "buongiorno" in comando or "buonasera" in comando:
            return self.personalita.saluto() if self.personalita else "Sistema pronto."
        if "come stai" in comando:
            return self.personalita.come_stai() if self.personalita else "Tutti i sistemi sono operativi."
        if "aiutami" in comando:
            return self.personalita.aiuto() if self.personalita else "Posso gestire sistema, dispositivi e memoria."

        # Memoria e identità
        if comando.startswith("ricorda "):
            ricordo = comando[8:]
            if self.memoria:
                parti = ricordo.split(" è ", 1)
                if len(parti) == 2:
                    return self.memoria.ricorda(parti[0], parti[1])
            return "Non riesco a salvare il ricordo."
        if "cosa ricordi di me" in comando:
            return self.memoria.profilo.mostra_profilo() if self.memoria else "Memoria non disponibile."
        if comando.startswith("chiamami "):
            nome = comando[9:].strip()
            if self.kernel and hasattr(self.kernel, "preferenze"):
                return self.kernel.preferenze.imposta("nome_utente", nome)
            return f"Va bene, ti chiamerò {nome}."
        if "come mi chiamo" in comando:
            nome = self.kernel.preferenze.leggi("nome_utente") if self.kernel else None
            return f"Ti chiami {nome}." if nome else "Non conosco ancora il tuo nome."

        # Base/telefono
        if "stato motorola" in comando:
            d = self.prendi("motorola")
            return str(d.stato()) if d else "Motorola non disponibile."
        if "identifica motorola" in comando:
            d = self.prendi("motorola")
            return f"La base principale è {d.nome}. Modello: {d.modello}." if d else "Base Motorola non disponibile."
        if "sincronizza motorola" in comando:
            return self.dispositivi.sincronizza("motorola") if self.dispositivi else "Connessione non disponibile."
        if "torna al motorola" in comando or "ritorna alla base" in comando:
            d = self.prendi("motorola")
            if d:
                d.principale = True
                d.sessione_attiva = False
                return "Jarvis è tornato alla base Motorola."
            return "Base Motorola non disponibile."
        if "trasferisciti sul telefono" in comando:
            d = self.prendi("telefono")
            return d.attiva_sessione() if d else "Telefono non disponibile."
        if "stato telefono" in comando:
            d = self.prendi("telefono")
            return str(d.stato()) if d else "Telefono non disponibile."
        if "batteria telefono" in comando:
            d = self.prendi("telefono")
            return f"Batteria telefono: {d.batteria}%" if d else "Telefono non disponibile."
        if "wifi telefono" in comando:
            d = self.prendi("telefono")
            return ("Wi-Fi telefono attivo." if d.wifi else "Wi-Fi telefono spento.") if d else "Telefono non disponibile."
        if "bluetooth telefono" in comando:
            d = self.prendi("telefono")
            return ("Bluetooth telefono attivo." if d.bluetooth else "Bluetooth telefono spento.") if d else "Telefono non disponibile."

        # TV LG webOS
        tv = self.prendi("tv")
        if comando in ("stato tv", "stato televisione", "stato tv lg"):
            return str(tv.stato()) if tv else "TV non disponibile."
        if comando in ("collega tv", "connetti tv", "connetti televisione"):
            return tv.connetti() if tv else "TV non disponibile."
        if comando in ("spegni tv", "spegni televisione"):
            return tv.spegni() if tv else "TV non disponibile."
        if comando.startswith("volume tv "):
            try:
                return str(tv.volume(int(comando.split()[-1]))) if tv else "TV non disponibile."
            except ValueError:
                return "Indica un volume da 0 a 100."
        if comando in ("muta tv", "silenzia tv"):
            return str(tv.mute(True)) if tv else "TV non disponibile."
        if comando in ("riattiva audio tv", "togli muto tv"):
            return str(tv.mute(False)) if tv else "TV non disponibile."

        # App telefono
        if comando.startswith("apri "):
            d = self.prendi("telefono")
            return d.apri_app(comando[5:].strip()) if d else "Telefono non disponibile."
        if comando.startswith("chiudi "):
            d = self.prendi("telefono")
            return d.chiudi_app(comando[7:].strip()) if d else "Telefono non disponibile."

        # Smart home
        if comando.startswith("accendi "):
            d = self.prendi("smart_home")
            return d.accendi(comando[8:].strip()) if d else "Smart home non disponibile."
        if comando.startswith("spegni "):
            d = self.prendi("smart_home")
            return d.spegni(comando[7:].strip()) if d else "Smart home non disponibile."

        for nome, funzione in self.comandi_personalizzati.items():
            if nome in comando:
                return funzione()
        return "Non ho trovato un comando compatibile."

    def prendi(self, nome):
        return self.dispositivi.cerca(nome) if self.dispositivi else None

    def get_connessione(self):
        return self.kernel.modulo_dispositivi.get_connessione() if self.kernel else None

    def aggiungi_comando(self, nome, funzione):
        self.comandi_personalizzati[nome] = funzione
        return f"Comando {nome} aggiunto."

    def stato(self):
        return {"nome": "Gestore Comandi", "stato": "attivo" if self.attivo else "spento"}
