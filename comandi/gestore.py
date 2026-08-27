from __future__ import annotations

import datetime
import re


class GestoreComandi:
    """Interprete dei comandi naturali di Jarvis."""

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
            self.logger.info("Gestore comandi Jarvis avviato.")
        return True

    def esegui(self, comando):
        if not comando or not comando.strip():
            return "Comando vuoto."
        originale = comando.strip()
        c = re.sub(r"\s+", " ", originale.lower())
        if c in ("esci", "chiudi", "stop", "spegni jarvis", "arresta jarvis"):
            if self.kernel:
                self.kernel.richiedi_arresto()
            return "Arresto di Jarvis richiesto."
        if self.kernel and self.kernel.sicurezza.richiede_conferma(c) and "confermo" not in c:
            self.kernel.sicurezza.registra("Comando protetto richiesto", originale)
            return "Questo comando richiede conferma. Aggiunga 'confermo' per autorizzarlo."
        try:
            risposta = self._esegui_raw(c)
        except Exception as errore:
            if self.logger:
                self.logger.error(f"Errore comando '{originale}': {errore}")
            risposta = "Ho incontrato un errore nell'esecuzione del comando."
        if self.kernel:
            try:
                self.kernel.contesto.aggiorna(originale, risposta)
            except Exception:
                pass
        return risposta

    def _esegui_raw(self, c):
        k = self.kernel
        cap = getattr(k, "capacita", None) if k else None
        d = self.dispositivi
        t = getattr(k, "trasferimento", None) if k else None
        if c in ("ciao", "salve", "ehi jarvis", "hey jarvis", "buongiorno", "buon pomeriggio", "buonasera"):
            return self.personalita.saluto() if self.personalita else "Salve. Tutti i sistemi sono pronti. Come posso assisterla?"
        if any(x in c for x in ("come stai", "come va", "tutto bene")):
            return self.personalita.come_stai() if self.personalita else "Tutti i sistemi sono operativi."
        if any(x in c for x in ("chi sei", "presentati", "come ti chiami")):
            return "Sono J.A.R.V.I.S., il suo assistente personale. Gestisco informazioni, memoria, voce, dispositivi, automazioni e capacità operative del sistema."
        if any(x in c for x in ("grazie", "ottimo", "perfetto")):
            return self.personalita.risposta_gentile() if self.personalita and hasattr(self.personalita, "risposta_gentile") else "È un piacere assisterla."
        if "aiutami" in c or c in ("aiuto", "cosa sai fare", "cosa puoi fare"):
            return self.personalita.aiuto() if self.personalita else "Posso gestire sistema, memoria, voce, web e dispositivi."
        if c in ("che ore sono", "ora"):
            return cap.ora() if cap else f"Sono le {datetime.datetime.now().strftime('%H:%M')}."
        if c in ("che giorno è", "che data è", "data"):
            return cap.data() if cap else f"Oggi è il {datetime.datetime.now().strftime('%d/%m/%Y')}."
        if c in ("stato sistema", "stato del sistema", "rapporto sistema", "diagnostica"):
            return k.diagnostica.riepilogo() if k else "Diagnostica non disponibile."
        if c in ("stato memoria", "memoria"):
            return str(k.memoria.stato()) if k else "Memoria non disponibile."
        if c in ("stato voce", "stato audio"):
            return str(k.modulo_voce.stato()) if k else "Voce non disponibile."
        if c in ("stato ai", "stato intelligenza artificiale"):
            return str(k.intelligenza.stato()) if k and hasattr(k, "intelligenza") else "AI non disponibile."
        if c in ("stato automazioni", "stato automazione"):
            return str(k.automazioni.stato()) if k else "Automazioni non disponibili."
        if c in ("stato visione", "stato camera"):
            return str(k.visione.stato()) if k else "Visione non disponibile."

        if c in ("stato trasferimento", "stato multi dispositivo", "stato multidispositivo"):
            return str(t.stato()) if t else "Modulo trasferimento non disponibile."
        if c in ("informazioni dispositivo", "info dispositivo", "questo dispositivo"):
            return str(t.dispositivo()) if t else "Informazioni dispositivo non disponibili."
        if c in ("supporto dispositivi", "dispositivi supportati", "supporto multi dispositivo"):
            return str(t.supporto()) if t else "Supporto multi-dispositivo non disponibile."
        if c in ("trasferisci jarvis", "prepara trasferimento", "prepara jarvis al trasferimento", "esporta jarvis"):
            return t.crea_pacchetto(d) if t else "Trasferimento non disponibile."
        if c in ("crea pacchetto jarvis", "crea pacchetto trasferimento"):
            return t.crea_pacchetto(d) if t else "Trasferimento non disponibile."
        if c in ("genera codice associazione", "codice associazione", "associa dispositivo"):
            return t.codice_associazione() if t else "Associazione dispositivi non disponibile."
        if c in ("rileva telefoni usb", "cerca telefono usb", "trova telefoni usb") and t:
            return str(t.rileva_usb())
        m = re.match(r"associa(?:\s+via\s+usb)?\s+(.+)$", c)
        if m and t:
            nome = m.group(1).strip()
            return str(t.primo_collegamento_usb(nome, nome))
        m = re.match(r"(?:trasferisciti|trasferisci jarvis)\s+(?:sul|su)\s+(.+)$", c)
        if m and t:
            nome = m.group(1).strip()
            risultato = t.trasferisci_sessione(nome=nome)
            if risultato.get("ok"):
                return f"Trasferimento temporaneo verso {nome} completato."
            if risultato.get("richiede_agente"):
                return f"{nome} è associato, ma deve avere l'Agente Jarvis attivo per completare il trasferimento senza cavo."
            return risultato.get("errore", "Trasferimento non completato.")
        if c in ("ritorna sul mac", "ritorna al mac", "torna sul mac", "torna al mac"):
            risultato = t.ritorna_al_mac() if t else {"ok": False, "errore": "Trasferimento non disponibile."}
            if risultato.get("ok"):
                return "Jarvis è tornato sul Mac."
            if risultato.get("richiede_usb"):
                return "Collega il telefono al Mac tramite USB per completare il ritorno."
            return risultato.get("errore", "Ritorno al Mac non completato.")
        m = re.match(r"(?:ritorna|torna)\s+(?:da|dal)\s+(.+)$", c)
        if m and t:
            nome = m.group(1).strip()
            risultato = t.ritorna_al_mac(nome=nome)
            if risultato.get("ok"):
                return f"Jarvis è tornato sul Mac da {nome}."
            if risultato.get("richiede_usb"):
                return f"{nome} è un dispositivo legacy. Collegalo al Mac tramite USB per completare il ritorno."
            return risultato.get("errore", "Ritorno al Mac non completato.")
        m = re.match(r"(?:importa|carica) pacchetto jarvis\s+(.+)$", c)
        if m and t:
            return t.importa_pacchetto(m.group(1).strip())

        if c in ("stato dispositivi", "stato dispositivi casa"):
            return str(d.stato_tutti()) if d else "Gestore dispositivi non disponibile."
        if c in ("quali dispositivi", "elenca dispositivi", "lista dispositivi"):
            return str(d.elenco()) if d else "Nessun dispositivo registrato."
        if c in ("rapporto dispositivi", "rapporto dispositivi casa"):
            return str(d.rapporto()) if d else "Gestore dispositivi non disponibile."
        m = re.match(r"(?:che cosa sa fare|cosa sa fare|capacità di|capacita di|funzioni di)\s+(.+)$", c)
        if m and d:
            nome = m.group(1).strip()
            dispositivo = d.cerca(nome)
            if not dispositivo:
                return "Dispositivo non trovato."
            capacita = d.capacita_dispositivo(nome)
            return f"{nome} supporta: {', '.join(capacita)}." if capacita else f"Non risultano capacità operative esposte per {nome}."
        m = re.match(r"(?:connetti|collega)\s+(.+)$", c)
        if m and d:
            return d.connetti(m.group(1).strip())
        m = re.match(r"(?:disconnetti|scollega)\s+(.+)$", c)
        if m and d:
            return d.disconnetti(m.group(1).strip())
        m = re.match(r"sincronizza\s+(.+)$", c)
        if m and d:
            return d.sincronizza(m.group(1).strip())
        if c in ("sincronizza tutto", "sincronizza dispositivi", "sincronizza casa") and d:
            risultati = []
            for nome in d.elenco():
                risultati.append(f"{nome}: {d.sincronizza(nome)}")
            return "Sincronizzazione completata. " + " ".join(risultati)

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
        if c.startswith("dimentica ") and self.memoria:
            return self.memoria.dimentica(c[10:].strip())
        if c.startswith("chiamami ") and k:
            return k.preferenze.imposta("nome_utente", c[9:].strip())
        if "come mi chiamo" in c and k:
            nome = k.preferenze.leggi("nome_utente")
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
        if c.startswith("apri "):
            app = c[5:].strip()
            if app:
                telefono_principale = self._telefono_principale()
                if telefono_principale:
                    return telefono_principale.apri_app(app)
                return "Nessun telefono principale attivo."
        if c.startswith("apri cartella"):
            return cap.apri_cartella() if cap else "Gestione cartelle non disponibile."
        if c == "apri finder":
            return cap.apri_cartella() if cap else "Gestione cartelle non disponibile."
        if c.startswith("chiudi "):
            app = c[7:].strip()
            if app:
                telefono_principale = self._telefono_principale()
                if telefono_principale:
                    return telefono_principale.chiudi_app(app)
                return "Nessun telefono principale attivo."
        if "fai uno screenshot" in c or "fai una schermata" in c:
            return cap.screenshot() if cap else "Screenshot non disponibile."
        m = re.search(r"(?:imposta|avvia|crea) (?:un )?timer (?:di )?(\d+)\s*(secondi|secondo|minuti|minuto|ore|ora)?", c)
        if m and cap:
            valore = int(m.group(1)); unita = m.group(2) or "secondi"
            moltiplicatore = 3600 if "or" in unita else 60 if "minut" in unita else 1
            return cap.timer_avvia(valore * moltiplicatore)
        if c.startswith("annulla timer") and cap:
            nome = c.replace("annulla timer", "", 1).strip() or "timer"
            return cap.timer_annulla(nome)
        m = re.search(r"(?:volume|audio) (?:a |del |al )?(\d{1,3})", c)
        if m and cap:
            return cap.volume(int(m.group(1)))
        if any(x in c for x in ("silenzia computer", "muta computer", "silenzia audio")) and cap:
            return cap.silenzia()
        if c in ("attiva hud", "accendi hud") and k and k.hud:
            k.hud.avvia(); return "HUD attivato."
        if c in ("spegni hud", "disattiva hud") and k and k.hud:
            k.hud.ferma(); return "HUD disattivato."
        if c in ("esegui diagnostica", "fai diagnostica") and k:
            return k.diagnostica.riepilogo()
        if c in ("elenca comandi", "lista comandi"):
            return self.personalita.aiuto() if self.personalita else "Posso gestire sistema, memoria, voce, web e dispositivi."
        if c.startswith("pianifica ") and k:
            m = re.match(r"pianifica (?:un )?timer (?:di )?(\d+)\s*(secondi|secondo|minuti|minuto)$", c)
            if m:
                secondi = int(m.group(1)) * (60 if "minut" in m.group(2) else 1)
                return k.capacita.timer_avvia(secondi, "pianificato")
        for nome, funzione in self.comandi_personalizzati.items():
            if nome in c:
                return funzione()
        if k and hasattr(k, "intelligenza"):
            risposta_ai = k.intelligenza.rispondi(c)
            if risposta_ai:
                return risposta_ai
        return "Non ho trovato un comando compatibile."

    def _telefono_principale(self):
        if not self.dispositivi:
            return None
        for dispositivo in self.dispositivi.dispositivi.values():
            if getattr(dispositivo, "principale", False):
                return dispositivo
        return None

    def ferma(self):
        self.attivo = False
        if self.logger:
            self.logger.info("Gestore comandi Jarvis fermato.")
        return True

    def stato(self):
        return {"nome": "Gestore Comandi", "stato": "attivo" if self.attivo else "spento", "comandi_personalizzati": len(self.comandi_personalizzati)}
