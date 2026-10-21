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
        c = self._normalizza_comando_vocale(originale)
        if c in ("esci", "chiudi", "stop", "spegni jarvis", "arresta jarvis"):
            if self.kernel:
                self.kernel.richiedi_arresto()
            return "Arresto di Jarvis richiesto."
        if self.kernel and self.kernel.sicurezza.richiede_conferma(c) and "confermo" not in c:
            self.kernel.sicurezza.registra("Comando protetto richiesto", originale)
            return "Questo comando richiede conferma. Aggiunga 'confermo' per autorizzarlo."
        try:
            risposta = self._esegui_controllo_telefono_video(originale)
            if risposta is None:
                risposta = self._esegui_studio_presentazioni(originale)
            if risposta is None:
                risposta = self._esegui_comandi_documenti(originale)
            if risposta is None:
                risposta = self._esegui_ricerca_web(originale)
            if risposta is None:
                risposta = self._esegui_cybersecurity_file_command(originale)
            if risposta is None:
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

    @staticmethod
    def _normalizza_comando_vocale(comando):
        """Corregge solo errori vocali comuni senza alterare il significato.

        Vosk può produrre piccole deformazioni fonetiche. Le correzioni qui
        presenti sono volutamente conservative e servono soprattutto a
        trasformare una domanda riconoscibile in una frase che il cervello IA
        possa comprendere. Non usiamo fuzzy matching sui comandi operativi,
        perché potrebbe eseguire un'azione diversa da quella pronunciata.
        """
        c = re.sub(r"\s+", " ", str(comando or "").strip().lower())

        correzioni = (
            (r"^briga di\s+", "spiegami "),
            (r"^briga\s+", "spiegami "),
            (r"^spiega mi\s+", "spiegami "),
            (r"^mi spiega\s+", "mi spieghi "),
            (r"^che cosa e\s+", "che cos'è "),
            (r"^cosa e\s+", "cosa è "),
            (r"^(che\s+)?giorno\s+(?:è|e)(?:\s+oggi)?$", "che giorno è"),
            (r"^(che\s+)?data\s+(?:è|e)(?:\s+oggi)?$", "che data è"),
            (r"^(che\s+)?giorno\s+oggi$", "che giorno è"),
            (r"^(che\s+)?data\s+oggi$", "che data è"),
            (r"^che\s+ore\s+(?:sono|e)(?:\s+adesso|\s+ora)?$", "che ore sono"),
        )
        for pattern, sostituzione in correzioni:
            nuovo = re.sub(pattern, sostituzione, c, count=1)
            if nuovo != c:
                c = nuovo
                break

        return c.strip()

    def _esegui_controllo_telefono_video(self, comando_originale):
        """Comandi telefonici singoli e orchestrazione multi-dispositivo esplicita."""
        try:
            from dispositivi.controllo_android_multi import ControlloAndroidMulti
            multi = ControlloAndroidMulti(logger=self.logger)
            risposta_multi = multi.gestisci_comando(comando_originale)
            if risposta_multi is not None:
                return risposta_multi
        except Exception as errore:
            if self.logger:
                self.logger.warning(f"Controllo Android multi-dispositivo non disponibile: {errore}")
        try:
            from dispositivi.controllo_android import ControlloAndroidVideo
            controller = ControlloAndroidVideo(logger=self.logger)
            return controller.gestisci_comando(comando_originale)
        except Exception as errore:
            if self.logger:
                self.logger.warning(f"Controllo telefono Android non disponibile: {errore}")
            return None

    def _esegui_comandi_documenti(self, comando_originale):
        """Lettura e ricerca letterale nei documenti, senza eseguire il contenuto."""
        testo = str(comando_originale or "").strip()
        try:
            from moduli.gestore_documenti import GestoreDocumentiJarvis
        except Exception:
            return None

        match = re.match(r"^(?:leggi|apri e leggi) (?:il )?(?:file|documento) (.+)$", testo, re.IGNORECASE)
        if match:
            return GestoreDocumentiJarvis().leggi_file(match.group(1).strip())

        match = re.match(
            r"^(?:cerca|trova) (?:nel file|nel documento) (.+?) (?:la parola|il testo|parola|testo) (.+)$",
            testo,
            re.IGNORECASE,
        )
        if match:
            percorso = match.group(1).strip().strip('"').strip("'")
            termine = match.group(2).strip().strip('"').strip("'")
            return GestoreDocumentiJarvis().cerca_nel_file(percorso, termine)
        return None

    def _esegui_ricerca_web(self, comando_originale):
        """Ricerca online esplicita con risultati e URL delle fonti."""
        testo = str(comando_originale or "").strip()
        match = re.match(
            r"^(?:cerca\s+(?:sul\s+web|online|su\s+internet)|"
            r"ricerca\s+(?:sul\s+web|web|online)|"
            r"fai\s+una\s+ricerca\s+(?:su\s+internet|online|sul\s+web))\s+(.+)$",
            testo,
            re.IGNORECASE,
        )
        if not match:
            return None
        query = match.group(1).strip().strip('"').strip("'")
        if not query:
            return "Mi indichi l'argomento da cercare online."
        try:
            from moduli.ricerca_web import cerca_web
        except Exception:
            return "Il modulo di ricerca web non è disponibile."
        return cerca_web(query)

    def _esegui_cybersecurity_file_command(self, comando_originale):
        """Comandi file cybersecurity; conserva le maiuscole del percorso."""
        k = self.kernel
        cyber = getattr(k, "cybersecurity", None) if k else None
        if not cyber:
            return None
        testo = str(comando_originale or "").strip()
        comandi = (
            # Hash: accetta forme naturali con "hash SHA-256 di/del" e
            # "calcola SHA-256 di/del"; il percorso conserva maiuscole e spazi.
            (r"^(?:calcola\s+)?(?:l['’]\s*)?hash(?:\s+sha[\s-]?256)?\s+(?:di|del|della)\s+(.+)$", "hash"),
            (r"^calcola\s+sha[\s-]?256\s+(?:di|del|della)\s+(.+)$", "hash"),
            (r"^(?:analizza file|controlla file)\s+(.+)$", "file"),
            (r"^(?:controlla progetto|analizza progetto|audit progetto)\s+(.+)$", "progetto"),
            (r"^(?:analizza log|controlla log)\s+(.+)$", "log"),
        )
        for pattern, tipo in comandi:
            match = re.match(pattern, testo, re.IGNORECASE)
            if not match:
                continue
            percorso = match.group(1).strip().strip('"').strip("'").strip("“”‘’")
            if tipo == "hash":
                # Alcune formulazioni vocali includono "il file" o "un file"
                # prima del percorso effettivo.
                percorso = re.sub(r"^(?:un\s+)?file\s+", "", percorso, flags=re.IGNORECASE)
            if tipo == "hash" and (
                not percorso
                or re.fullmatch(
                    r"(?:un\s+)?file(?:\s+esistente)?|un\s+file\s+(?:locale|sul\s+mac)",
                    percorso,
                    re.IGNORECASE,
                )
            ):
                return "Per calcolare l'hash SHA-256, pronunci o scriva il percorso completo del file, per esempio: calcola hash SHA-256 di /Users/utente/Desktop/esempio.txt."
            if tipo == "hash":
                risultato = cyber.hash_file(percorso)
                if not risultato.get("ok"):
                    return risultato.get("errore", "Impossibile calcolare l'hash.")
                return "SHA-256 di " + risultato["file"] + ": " + risultato["sha256"]
            if tipo == "file":
                risultato = cyber.analizza_file(percorso)
            elif tipo == "progetto":
                risultato = cyber.controlla_progetto(percorso)
            else:
                risultato = cyber.analizza_log(percorso)
            if not risultato.get("ok"):
                return risultato.get("errore", "Analisi non completata.")
            if tipo == "file":
                return (f"Analisi statica completata per {risultato['file']}. "
                        f"Possibili segreti: {len(risultato.get('indicatori', []))}; "
                        f"avvertenze euristiche: {len(risultato.get('avvertenze', []))}. "
                        "Non ho eseguito il file.")
            if tipo == "progetto":
                return (f"Controllo statico completato. File esaminati: {risultato['file_esaminati']}; "
                        f"indicatori e avvertenze: {len(risultato['problemi'])}. "
                        "Il controllo è euristico, non una certificazione di sicurezza.")
            conteggi = risultato["conteggi"]
            return (f"Analisi log completata. Errori: {conteggi['errori']}; "
                    f"autenticazioni fallite: {conteggi['autenticazioni_fallite']}; "
                    f"possibili blocchi o limiti: {conteggi['possibili_blocchi']}.")
        return None

    def _esegui_studio_presentazioni(self, comando_originale):
        """Integra lo studio PowerPoint opzionale senza bloccare gli altri comandi."""
        testo = str(comando_originale or "").strip()
        match = re.match(
            r"^(?:crea\s+presentazione|crea\s+powerpoint)\s+(?:da\s+file|dal\s+file)\s+(.+)$",
            testo,
            re.IGNORECASE,
        )
        try:
            from moduli.studio_presentazioni import StudioPresentazioniJarvis
        except Exception:
            return None

        studio = StudioPresentazioniJarvis()
        match_riassunto = re.match(
            r"^riassumi\s+(?:il\s+)?file\s+(.+)$",
            testo,
            re.IGNORECASE,
        )
        if match_riassunto:
            dialogo = getattr(self.kernel, "dialogo", None) if self.kernel else None
            return studio.riassumi_file(match_riassunto.group(1).strip(), dialogo=dialogo)
        if match:
            return studio.crea_da_file(match.group(1).strip())

        match = re.match(
            r"^(?:crea\s+presentazione|crea\s+powerpoint)\s+da\s+testo\s+(.+)$",
            testo,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            contenuto = match.group(1).strip()
            titolo = "Presentazione Jarvis"
            intestazione = re.match(r"^#\s+([^\n]+)", contenuto)
            if intestazione:
                titolo = intestazione.group(1).strip()
            return studio.crea_da_contenuto(contenuto, titolo)

        match = re.match(
            r"^(?:crea\s+presentazione|crea\s+powerpoint)\s+su\s+(.+)$",
            testo,
            re.IGNORECASE,
        )
        if match:
            tema = match.group(1).strip()
            try:
                from moduli.ricerca_web import cerca_web
                ricerca = cerca_web(tema, limite=5)
            except Exception:
                ricerca = "Ricerca web non disponibile."
            righe = ricerca.splitlines()
            righe_fonti = [riga.strip() for riga in righe if riga.strip() and (re.match(r"^\\d+\\.\\s+", riga.strip()) or riga.strip().startswith("http://") or riga.strip().startswith("https://") or (riga.startswith("   ") and not riga.strip().startswith("Le informazioni")))]
            if righe_fonti and "Non ho trovato risultati" not in ricerca and "Non riesco a completare" not in ricerca:
                punti = "\\n".join("- " + riga.strip() for riga in righe_fonti)
                contenuto = (
                    f"# {tema}\\nPresentazione preparata da Jarvis a partire dai risultati web disponibili.\\n"
                    f"## Risultati raccolti\\n{punti}\\n"
                    "## Valutazione delle fonti\\n- Verificare data, autore e attendibilità delle pagine prima di usare i dati.\\n"
                    "- I risultati di ricerca sono indizi iniziali e non sostituiscono la lettura delle fonti originali."
                )
            else:
                contenuto = (
                    f"# Obiettivo e contesto\\nDefinire l'obiettivo della presentazione su {tema}.\\n"
                    f"## Aspetti principali\\n- Concetti fondamentali da verificare\\n"
                    f"- Dati e fonti da raccogliere\\n"
                    f"## Esempi e applicazioni\\n- Esempi pertinenti a {tema} da documentare\\n"
                    f"## Conclusioni\\n- Sintesi dei risultati verificati e domande aperte"
                )
            return studio.crea_da_contenuto(contenuto, tema)

        return None

    def _mostra_ricordi_personali(self):
        """Unisce profilo, ricordi espliciti e nome configurato in una risposta."""
        if not self.memoria:
            return "Memoria non disponibile."

        parti = []
        profilo = ""
        try:
            profilo = self.memoria.profilo.mostra_profilo()
            if profilo and profilo.strip().lower() not in {
                "profilo vuoto.",
                "profilo vuoto",
            }:
                parti.append(profilo.strip())
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
            pass

        try:
            ricordi = self.memoria.elenco_ricordi()
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
            ricordi = {}

        if isinstance(ricordi, dict):
            # Le informazioni su Simone sono consentite solo nel profilo
            # canonico; non presentare altri appunti come dati personali.
            etichette = {
                "colore_preferito": "colore preferito",
                "nome_utente": "nome",
                "animale_preferito": "animale preferito",
            }
            for chiave, dato in ricordi.items():
                if str(chiave).strip().lower().replace("-", "_") not in etichette:
                    continue
                valore = dato.get("valore") if isinstance(dato, dict) else dato
                if valore is None or not str(valore).strip():
                    continue
                etichetta = etichette[str(chiave).strip().lower().replace("-", "_")]
                frase = f"Ricordo anche {etichetta}: {valore}."
                if frase not in " ".join(parti):
                    parti.append(frase)

        # Il nome può essere salvato nelle preferenze anziché nel profilo.
        try:
            nome = self.kernel.preferenze.leggi("nome_utente") if self.kernel else None
            nome_profilo = self.memoria.profilo.leggi("nome_utente")
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
            nome = None
            nome_profilo = None
        if nome and not nome_profilo:
            parti.append(f"Il suo nome è {nome}.")

        if not parti:
            return "Al momento non ho informazioni personali salvate."
        return " ".join(parti)

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
        if re.fullmatch(r"(?:che\s+)?(?:giorno|data)(?:\s+(?:è|e))?(?:\s+oggi)?", c):
            return cap.data() if cap else f"Oggi è il {datetime.datetime.now().strftime('%d/%m/%Y')}."
        if c in ("che giorno è", "che data è", "data"):
            return cap.data() if cap else f"Oggi è il {datetime.datetime.now().strftime('%d/%m/%Y')}."
        # Cybersecurity difensiva: inventario passivo per default; le verifiche
        # TCP richiedono una richiesta esplicita e una seconda conferma vocale.
        cyber = getattr(k, "cybersecurity", None) if k else None
        if c in ("stato cybersecurity", "cybersecurity", "strumenti cybersecurity", "modalità cybersecurity", "modalita cybersecurity"):
            if not cyber:
                return "Modulo cybersecurity non disponibile."
            stato = cyber.stato()
            return ("Modulo cybersecurity pronto. Sistema " + stato["sistema"] +
                    ". Inventario rete in sola lettura; verifiche TCP su un singolo IP privato con conferma. " +
                    "NFC, radio sub-GHz e infrarossi richiedono accessori esterni compatibili.")
        if c in ("analizza la mia rete", "analizza rete locale", "analizza la rete", "inventario rete", "stato rete locale") and cyber:
            risultato = cyber.analizza_rete_locale()
            indirizzi = ", ".join(risultato["indirizzi_locali"]) or "nessun indirizzo rilevato"
            interfacce = ", ".join(risultato["interfacce"]) or "interfacce non disponibili"
            return f"Inventario locale completato. Computer: {risultato['host']}. Indirizzi: {indirizzi}. Interfacce: {interfacce}. Non ho eseguito scansioni di altri dispositivi."
        if c in ("capacità hardware", "capacita hardware", "hardware flipper", "stato hardware cybersecurity") and cyber:
            hw = cyber.capacita_hardware()
            return ("Hardware: USB seriale possibile con adattatore e driver; NFC: " + hw["nfc"] +
                    "; radio sub-GHz: " + hw["sub_ghz"] + "; infrarossi: " + hw["infrarossi"] + ".")
        if c in ("annulla scansione", "annulla verifica cybersecurity") and cyber:
            return cyber.annulla_scansione()
        m = re.match(r"scansiona host\s+(.+)$", c)
        if m and cyber:
            return cyber.richiedi_scansione_host(m.group(1).strip())
        m = re.match(r"confermo scansione\s+(.+)$", c)
        if m and cyber:
            return cyber.conferma_scansione_host(m.group(1).strip())

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
            # Canonicalizza alcune formulazioni personali comuni prima del
            # salvataggio, così i ricordi sono leggibili e facili da ritrovare.
            ricordo = re.sub(
                r"^(?:che )?il mio colore preferito è ",
                "colore_preferito è ",
                ricordo,
            )
            ricordo = re.sub(
                r"^(?:che )?mi chiamo ",
                "nome_utente è ",
                ricordo,
            )
            if self.memoria:
                parti = ricordo.split(" è ", 1)
                if len(parti) == 2:
                    return self.memoria.ricorda(parti[0], parti[1])
                return self.memoria.ricorda("nota", ricordo)
            return "Memoria non disponibile."
        if any(x in c for x in ("cosa ricordi di me", "cosa ricordi", "ricordi qualcosa")):
            return self._mostra_ricordi_personali()
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
            app = c[9:].strip()
            if app and cap:
                return cap.apri_app(app)
            return "Apertura app non disponibile."
        if c.startswith("apri "):
            app = c[5:].strip()
            if app:
                telefono_principale = self._telefono_principale()
                if telefono_principale:
                    return telefono_principale.apri_app(app)
                return cap.apri_app(app) if cap else "Apertura app non disponibile."
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
                return cap.chiudi_app(app) if cap else "Chiusura app non disponibile."
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

        # Stringhe manifestamente tecniche o di test non vanno inoltrate al
        # modello: l'IA potrebbe trasformarle arbitrariamente in una risposta.
        if re.fullmatch(r"[a-zàèéìòù0-9_\-]+", c) and ("_" in c or any(ch.isdigit() for ch in c)):
            return "Non ho trovato un comando compatibile."

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
