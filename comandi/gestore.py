from __future__ import annotations

import datetime
import re


class GestoreComandi:
    """Interprete naturale dei comandi vocali e testuali di Jarvis."""

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
            self.logger.info("Gestore comandi Jarvis definitivo avviato.")
        return True

    def esegui(self, comando):
        if not comando or not comando.strip():
            return "Comando vuoto."
        originale = comando.strip()
        comando = re.sub(r"\s+", " ", originale.lower())
        if self.kernel and hasattr(self.kernel, "sicurezza"):
            if self.kernel.sicurezza.richiede_conferma(comando) and "confermo" not in comando:
                self.kernel.sicurezza.registra("Comando protetto richiesto", comando)
                return "Questo comando richiede conferma. Aggiunga 'confermo' per autorizzarlo."
        try:
            risposta = self._esegui_raw(comando)
        except Exception as errore:
            if self.logger:
                self.logger.error(f"Errore comando '{originale}': {errore}")
            risposta = "Ho incontrato un errore nell'esecuzione del comando."
        if self.kernel and hasattr(self.kernel, "contesto"):
            try:
                self.kernel.contesto.aggiorna(originale, risposta)
            except Exception:
                pass
        return risposta

    def _esegui_raw(self, c):
        k = self.kernel
        cap = getattr(k, "capacita", None) if k else None

        if c in ("ciao", "salve", "ehi jarvis", "hey jarvis", "buongiorno", "buon pomeriggio", "buonasera"):
            return self.personalita.saluto() if self.personalita else "Salve. Tutti i sistemi sono pronti. Come posso assisterla?"
        if any(x in c for x in ("come stai", "come va", "tutto bene")):
            return self.personalita.come_stai() if self.personalita else "Tutti i sistemi sono operativi."
        if any(x in c for x in ("chi sei", "presentati", "come ti chiami")):
            return "Sono J.A.R.V.I.S., il suo assistente personale. Gestisco informazioni, memoria, voce, dispositivi e capacità operative del sistema."
        if any(x in c for x in ("grazie", "ottimo", "perfetto")):
            return self.personalita.risposta_gentile() if self.personalita and hasattr(self.personalita, "risposta_gentile") else "È un piacere assisterla."
        if any(x in c for x in ("ti voglio bene", "sei fantastico", "sei bravo")):
            return "È molto gentile. Sono qui per lei."
        if "aiutami" in c or c in ("aiuto", "cosa sai fare", "cosa puoi fare"):
            return self.personalita.aiuto() if self.personalita else "Posso gestire sistema, memoria, voce, web e dispositivi."

        if "che ore sono" in c or c == "ora":
            return cap.ora() if cap else f"Sono le {datetime.datetime.now().strftime('%H:%M')}."
        if "che giorno è" in c or "che data è" in c or c == "data":
            return cap.data() if cap else f"Oggi è il {datetime.datetime.now().strftime('%d/%m/%Y')}."

        if c in ("stato sistema", "stato del sistema", "rapporto sistema", "diagnostica"):
            if not k:
                return "Sistema non disponibile."
            s = k.stato_sistema()
            return (f"Diagnostica completata. Jarvis {s['stato']}, versione {s['versione']}. "
                    f"Voce: {'attiva' if s['voce_disponibile'] else 'solo testo'}. "
                    f"Dispositivi registrati: {len(s['dispositivi'].get('dispositivi', []))}. Capacità operative attive.")
        if "stato dispositivi" in c:
            return str(self.dispositivi.stato_tutti()) if self.dispositivi else "Gestore dispositivi non disponibile."
        if "quali dispositivi" in c or "elenca dispositivi" in c:
            return str(self.dispositivi.elenco()) if self.dispositivi else "Nessun dispositivo registrato."
        if c in ("stato computer", "stato del computer", "informazioni computer"):
            return str(cap.sistema()) if cap else "Informazioni di sistema non disponibili."

        if c.startswith("ricorda "):
            ricordo = c[8:].strip()
            if self.memoria:
                parti = ricordo.split(" è ", 1)
                if len(parti) == 2:
                    return self.memoria.ricorda(parti[0], parti[1])
                return self.memoria.ricorda("nota", ricordo)
            return "Memoria non disponibile."
        if any(x in c for x in ("cosa ricordi di me", "cosa ricordi", "ricordi qualcosa")):
            return self.memoria.profilo.mostra_profilo() if self.memoria else "Memoria non disponibile."
        if c.startswith("chiamami "):
            nome = c[9:].strip()
            return k.preferenze.imposta("nome_utente", nome) if k else f"Va bene, la chiamerò {nome}."
        if "come mi chiamo" in c:
            nome = k.preferenze.leggi("nome_utente") if k else None
            return f"La chiamo {nome}." if nome else "Non conosco ancora il suo nome."

        if c.startswith(("calcola ", "quanto fa ")):
            espr = re.sub(r"^(calcola|quanto fa)\s+", "", c)
            try:
                return f"Il risultato è {cap.calcola(espr)}." if cap else "Calcolatrice non disponibile."
            except Exception:
                return "Non riesco a calcolare questa espressione."

        if c.startswith("cerca ") or c.startswith("cerca sul web "):
            q = re.sub(r"^cerca( sul web)?\s+", "", c)
            return cap.cerca_web(q) if cap else "Ricerca web non disponibile."
        if c.startswith("apri sito "):
            return cap.apri_url(c[10:].strip()) if cap else "Browser non disponibile."
        if c.startswith("apri https://") or c.startswith("apri http://"):
            return cap.apri_url(c[5:].strip()) if cap else "Browser non disponibile."

        if c.startswith("meteo") or c.startswith("tempo a "):
            localita = c[5:].strip() if c.startswith("meteo") else c[9:].strip()
            return cap.meteo(localita or "Napoli") if cap else "Servizio meteo non disponibile."

        if c.startswith("apri app "):
            return cap.apri_app(c[9:].strip()) if cap else "Apertura app non disponibile."
        if c.startswith("apri ") and not any(x in c for x in ("tv", "telefono", "app")):
            return cap.apri_app(c[5:].strip()) if cap else "Apertura app non disponibile."
        if c in ("apri cartella", "apri la cartella", "apri finder"):
            return cap.apri_cartella() if cap else "Gestione cartelle non disponibile."
        if "fai uno screenshot" in c or "fai una schermata" in c:
            return cap.screenshot() if cap else "Screenshot non disponibile."

        m = re.search(r"(?:imposta|avvia|crea) (?:un )?timer (?:di )?(\d+)\s*(secondi|secondo|minuti|minuto|ore|ora)?", c)
        if m and cap:
            valore = int(m.group(1)); unita = m.group(2) or "secondi"
            moltiplicatore = 3600 if "or" in unita else 60 if "minut" in unita else 1
            return cap.timer_avvia(valore * moltiplicatore)
        if "annulla timer" in c and cap:
            return cap.timer_annulla()

        m = re.search(r"(?:volume|audio) (?:a |del |al )?(\d{1,3})", c)
        if m and cap:
            return cap.volume(int(m.group(1)))
        if any(x in c for x in ("silenzia computer", "muta computer", "silenzia audio")) and cap:
            return cap.silenzia()

        if "stato motorola" in c:
            d = self.prendi("motorola"); return str(d.stato()) if d else "Base Motorola non disponibile."
        if "identifica motorola" in c:
            d = self.prendi("motorola"); return f"La base principale è {d.nome}. Modello: {d.modello}." if d else "Base Motorola non disponibile."
        if "sincronizza motorola" in c:
            return self.dispositivi.sincronizza("motorola") if self.dispositivi else "Connessione non disponibile."
        if "torna al motorola" in c or "ritorna alla base" in c:
            d = self.prendi("motorola")
            if d:
                d.principale = True; d.sessione_attiva = False
                return "Jarvis è tornato alla base Motorola."
            return "Base Motorola non disponibile."
        if "trasferisciti sul telefono" in c:
            d = self.prendi("telefono"); return d.attiva_sessione() if d else "Telefono non disponibile."
        if "stato telefono" in c:
            d = self.prendi("telefono"); return str(d.stato()) if d else "Telefono non disponibile."
        if "batteria telefono" in c:
            d = self.prendi("telefono"); return f"Batteria telefono: {d.batteria}%" if d else "Telefono non disponibile."
        if "wifi telefono" in c:
            d = self.prendi("telefono"); return ("Wi-Fi telefono attivo." if d.wifi else "Wi-Fi telefono spento.") if d else "Telefono non disponibile."
        if "bluetooth telefono" in c:
            d = self.prendi("telefono"); return ("Bluetooth telefono attivo." if d.bluetooth else "Bluetooth telefono spento.") if d else "Telefono non disponibile."

        tv = self.prendi("tv")
        if c in ("stato tv", "stato televisione", "stato tv lg"):
            return str(tv.stato()) if tv else "TV non disponibile."
        if c in ("collega tv", "connetti tv", "connetti televisione"):
            return tv.connetti() if tv else "TV non disponibile."
        if c in ("spegni tv", "spegni televisione"):
            return tv.spegni() if tv else "TV non disponibile."
        if c in ("accendi tv", "accendi televisione"):
            return tv.accendi() if tv and hasattr(tv, "accendi") else "Accensione TV non disponibile."
        if c.startswith("volume tv "):
            try: return str(tv.volume(int(c.split()[-1]))) if tv else "TV non disponibile."
            except ValueError: return "Indichi un volume da 0 a 100."
        if c in ("muta tv", "silenzia tv"):
            return str(tv.mute(True)) if tv else "TV non disponibile."
        if c in ("riattiva audio tv", "togli muto tv"):
            return str(tv.mute(False)) if tv else "TV non disponibile."

        if c.startswith("apri telefono "):
            d = self.prendi("telefono"); return d.apri_app(c[14:].strip()) if d else "Telefono non disponibile."
        if c.startswith("chiudi "):
            d = self.prendi("telefono"); return d.chiudi_app(c[7:].strip()) if d else "Telefono non disponibile."

        if c.startswith("accendi "):
            d = self.prendi("smart_home"); return d.accendi(c[8:].strip()) if d else "Smart home non disponibile."
        if c.startswith("spegni "):
            d = self.prendi("smart_home"); return d.spegni(c[7:].strip()) if d else "Smart home non disponibile."

        for nome, funzione in self.comandi_personalizzati.items():
            if nome in c:
                return funzione()

        # Se esiste un LLM locale, usalo solo per la conversazione libera.
        if k and hasattr(k, "dialogo"):
            risposta_ai = k.dialogo.rispondi(c)
            if risposta_ai:
                return risposta_ai
        return self.personalita.non_capito(c) if self.personalita and hasattr(self.personalita, "non_capito") else "Non ho trovato un comando compatibile."

    def prendi(self, nome):
        return self.dispositivi.cerca(nome) if self.dispositivi else None

    def get_connessione(self):
        return self.kernel.modulo_dispositivi.get_connessione() if self.kernel else None

    def aggiungi_comando(self, nome, funzione):
        self.comandi_personalizzati[nome] = funzione
        return f"Comando {nome} aggiunto."

    def stato(self):
        return {"nome": "Gestore Comandi", "stato": "attivo" if self.attivo else "spento", "comandi_personalizzati": len(self.comandi_personalizzati)}
