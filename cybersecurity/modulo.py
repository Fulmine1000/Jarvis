"""Strumenti di cybersecurity difensiva per Jarvis.

Le analisi sono statiche e non eseguono i file. I controlli di rete attivi
sono limitati a un singolo IPv4 privato con conferma esplicita.
"""
from __future__ import annotations

import hashlib
import ipaddress
import os
import platform
import re
import socket
from pathlib import Path
from typing import Optional


class CybersecurityJarvis:
    PORTE_CONSENTITE = (22, 53, 80, 443, 445, 548, 631, 8000, 8080, 8443)
    MASSIMO_TIMEOUT = 0.35
    MASSIMO_FILE_BYTES = 5 * 1024 * 1024
    MASSIMO_FILE_AUDIT = 500
    ESCLUSIONI_DIRECTORY = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache"}
    ESTENSIONI_TESTO = {".py", ".js", ".ts", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env", ".sh", ".php", ".html", ".xml", ".txt", ".md", ".conf"}
    PATTERN_SEGRETI = (
        ("possibile chiave privata", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
        ("possibile token GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
        ("possibile chiave AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("possibile segreto assegnato a variabile", re.compile(r"""(?i)\b(?:api[_-]?key|secret|password|passwd|access[_-]?token)\b\s*[:=]\s*['"][^'"]{8,}['"]""")),
    )
    PATTERN_RISCHIO = (
        ("esecuzione di comandi di sistema", re.compile(r"(?i)\b(?:os\.system|subprocess\.(?:run|Popen|call)|shell=True)\b")),
        ("possibile esecuzione dinamica", re.compile(r"\b(?:eval|exec)\s*\(")),
        ("possibile disattivazione TLS", re.compile(r"(?i)(?:verify\s*=\s*False|CERT_NONE)")),
        ("possibile richiesta di privilegi elevati", re.compile(r"(?i)\b(?:sudo|chmod\s+777)\b")),
    )

    def __init__(self, logger=None):
        self.logger = logger
        self._host_in_attesa: Optional[str] = None
        self._ultimo_risultato = None

    def stato(self):
        return {
            "modulo": "Cybersecurity Jarvis",
            "stato": "pronto",
            "sistema": platform.system(),
            "modalita": ["inventario rete passivo", "verifica TCP limitata con conferma", "hash SHA-256", "analisi statica file/progetti", "analisi log locali"],
            "porte_consentite": list(self.PORTE_CONSENTITE),
            "host_in_attesa_di_conferma": self._host_in_attesa,
            "hardware_radio_nfc_ir": "richiede accessori esterni compatibili",
            "limiti": ["nessuna scansione di subnet", "nessun exploit o brute force", "i file non vengono eseguiti", "solo sistemi autorizzati"],
        }

    def analizza_rete_locale(self):
        nome = socket.gethostname()
        indirizzi = set()
        try:
            for risultato in socket.getaddrinfo(nome, None, type=socket.SOCK_STREAM):
                indirizzo = risultato[4][0].split("%", 1)[0]
                try:
                    ip = ipaddress.ip_address(indirizzo)
                    if not ip.is_unspecified and not ip.is_multicast:
                        indirizzi.add(str(ip))
                except ValueError:
                    continue
        except OSError:
            pass
        try:
            import psutil
            interfacce = sorted(psutil.net_if_addrs().keys())
        except Exception:
            interfacce = []
        risultato = {"host": nome, "indirizzi_locali": sorted(indirizzi), "interfacce": interfacce, "tipo_controllo": "sola lettura; nessun pacchetto inviato ad altri host"}
        self._ultimo_risultato = risultato
        self._log("Inventario rete locale completato (sola lettura).")
        return risultato

    @staticmethod
    def _valida_host_privato(host):
        try:
            ip = ipaddress.ip_address(str(host).strip())
        except ValueError:
            return None, "Indirizzo non valido: inserisca un IP numerico, non un nome host."
        if not (ip.is_private or ip.is_loopback or ip.is_link_local):
            return None, "Per sicurezza sono ammessi solo IP privati, loopback o link-local."
        if ip.version != 4:
            return None, "Per ora il controllo è limitato a un singolo indirizzo IPv4."
        return str(ip), None

    def richiedi_scansione_host(self, host):
        ip, errore = self._valida_host_privato(host)
        if errore:
            return errore
        self._host_in_attesa = ip
        porte = ", ".join(str(p) for p in self.PORTE_CONSENTITE)
        return (f"Pronto a verificare il solo host {ip}, esclusivamente sulle porte TCP {porte}. "
                "La verifica invia tentativi di connessione e richiede autorizzazione. "
                f"Per procedere dica: confermo scansione {ip}. Per annullare dica annulla scansione.")

    def annulla_scansione(self):
        self._host_in_attesa = None
        return "Verifica cybersecurity annullata."

    def conferma_scansione_host(self, host):
        ip, errore = self._valida_host_privato(host)
        if errore:
            return errore
        if not self._host_in_attesa or ip != self._host_in_attesa:
            return "Nessuna verifica corrispondente in attesa. Prima chieda 'scansiona host IP' e poi confermi lo stesso IP."
        self._host_in_attesa = None
        aperte = []
        for porta in self.PORTE_CONSENTITE:
            try:
                with socket.create_connection((ip, porta), timeout=self.MASSIMO_TIMEOUT):
                    aperte.append(porta)
            except (OSError, TimeoutError):
                continue
        risultato = {"host": ip, "porte_tcp_raggiungibili": aperte, "porte_verificate": list(self.PORTE_CONSENTITE)}
        self._ultimo_risultato = risultato
        self._log(f"Verifica TCP limitata eseguita su host autorizzato indicato dall'utente: {ip}.")
        if aperte:
            return f"Verifica completata su {ip}. Porte TCP raggiungibili: {', '.join(str(p) for p in aperte)}. Questo risultato non prova da solo una vulnerabilità."
        return f"Verifica completata su {ip}: nessuna porta consentita ha accettato una connessione. Firewall e timeout possono influenzare il risultato."

    def capacita_hardware(self):
        return {
            "usb_seriale": "possibile con adattatore e driver compatibili; non viene aperto automaticamente",
            "nfc": "nessun lettore NFC generico integrato da assumere presente",
            "sub_ghz": "richiede radio esterna compatibile; nessuna trasmissione attiva implementata",
            "infrarossi": "richiede emettitore/ricevitore IR esterno compatibile",
            "prossimo_passaggio": "collegare un accessorio specifico e aggiungere un driver dedicato con test",
        }

    def hash_file(self, percorso):
        """Calcola SHA-256 senza eseguire o modificare il file."""
        try:
            path = Path(os.path.expanduser(str(percorso).strip())).resolve()
            if not path.is_file():
                return {"ok": False, "errore": "Il percorso non indica un file regolare."}
            dimensione = path.stat().st_size
            if dimensione > self.MASSIMO_FILE_BYTES:
                return {"ok": False, "errore": f"File troppo grande (limite {self.MASSIMO_FILE_BYTES} byte)."}
            digest = hashlib.sha256()
            with path.open("rb") as file:
                for blocco in iter(lambda: file.read(65536), b""):
                    digest.update(blocco)
            risultato = {"ok": True, "file": str(path), "dimensione_byte": dimensione, "sha256": digest.hexdigest()}
            self._log(f"Calcolato hash SHA-256 per file locale: {path}")
            return risultato
        except (OSError, ValueError) as errore:
            return {"ok": False, "errore": f"Impossibile leggere il file: {errore}"}

    def analizza_file(self, percorso):
        """Cerca indicatori statici e segreti accidentali; non interpreta il file."""
        base = self.hash_file(percorso)
        if not base.get("ok"):
            return base
        path = Path(base["file"])
        risultato = dict(base)
        risultato.update({"indicatori": [], "avvertenze": [], "analisi": "statica; nessun codice eseguito"})
        if path.suffix.lower() not in self.ESTENSIONI_TESTO:
            risultato["avvertenze"].append("Formato non testuale o non supportato: è stato calcolato solo l'hash.")
            return risultato
        try:
            righe = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as errore:
            risultato["avvertenze"].append(f"Impossibile leggere il testo: {errore}")
            return risultato
        for numero, linea in enumerate(righe, 1):
            for descrizione, pattern in self.PATTERN_SEGRETI:
                if pattern.search(linea):
                    risultato["indicatori"].append({"tipo": "possibile segreto", "descrizione": descrizione, "riga": numero})
            for descrizione, pattern in self.PATTERN_RISCHIO:
                if pattern.search(linea):
                    risultato["avvertenze"].append({"descrizione": descrizione, "riga": numero})
        risultato["conteggio_righe"] = len(righe)
        risultato["indicatori"] = risultato["indicatori"][:100]
        risultato["avvertenze"] = risultato["avvertenze"][:100]
        self._log(f"Analisi statica completata per file locale: {path}")
        return risultato

    def controlla_progetto(self, percorso):
        """Analizza un albero locale con limiti sul numero di file."""
        try:
            radice = Path(os.path.expanduser(str(percorso).strip())).resolve()
            if not radice.is_dir():
                return {"ok": False, "errore": "Il percorso non indica una cartella esistente."}
            file_esaminati, file_con_hash = 0, 0
            problemi, errori = [], []
            for cartella, directory, nomi in os.walk(str(radice), followlinks=False):
                directory[:] = sorted(d for d in directory if d not in self.ESCLUSIONI_DIRECTORY and not d.startswith("."))
                for nome in sorted(nomi):
                    path = Path(cartella) / nome
                    if path.is_symlink() or not path.is_file():
                        continue
                    file_esaminati += 1
                    if file_esaminati > self.MASSIMO_FILE_AUDIT:
                        errori.append(f"Raggiunto il limite di {self.MASSIMO_FILE_AUDIT} file; analisi interrotta.")
                        break
                    analisi = self.analizza_file(str(path))
                    if not analisi.get("ok"):
                        errori.append(f"{path}: {analisi.get('errore', 'errore')}")
                        continue
                    file_con_hash += 1
                    for item in analisi.get("indicatori", []):
                        problemi.append({"file": str(path), **item})
                    for item in analisi.get("avvertenze", []):
                        if isinstance(item, dict):
                            problemi.append({"file": str(path), "tipo": "avvertenza", **item})
                if file_esaminati > self.MASSIMO_FILE_AUDIT:
                    break
            risultato = {"ok": True, "cartella": str(radice), "file_esaminati": min(file_esaminati, self.MASSIMO_FILE_AUDIT), "file_con_hash": file_con_hash, "problemi": problemi[:300], "errori": errori, "nota": "controllo euristico statico: verificare manualmente i risultati; nessun file eseguito"}
            self._ultimo_risultato = risultato
            self._log(f"Controllo statico progetto completato: {radice} ({file_con_hash} file).")
            return risultato
        except OSError as errore:
            return {"ok": False, "errore": f"Impossibile esaminare la cartella: {errore}"}

    def analizza_log(self, percorso):
        """Conta indicatori in un log locale, senza modificarlo."""
        try:
            path = Path(os.path.expanduser(str(percorso).strip())).resolve()
            if not path.is_file():
                return {"ok": False, "errore": "Il percorso non indica un file di log esistente."}
            if path.stat().st_size > self.MASSIMO_FILE_BYTES:
                return {"ok": False, "errore": f"Log troppo grande (limite {self.MASSIMO_FILE_BYTES} byte)."}
            patterns = {
                "errori": re.compile(r"(?i)\b(error|exception|failed|denied|fatal)\b"),
                "autenticazioni_fallite": re.compile(r"(?i)(failed password|authentication failure|invalid user|login failed)"),
                "possibili_blocchi": re.compile(r"(?i)(too many requests|rate.?limit|blocked|forbidden|429)"),
            }
            conteggi = {nome: 0 for nome in patterns}
            esempi = {nome: [] for nome in patterns}
            with path.open("r", encoding="utf-8", errors="replace") as file:
                for numero, linea in enumerate(file, 1):
                    for nome, pattern in patterns.items():
                        if pattern.search(linea):
                            conteggi[nome] += 1
                            if len(esempi[nome]) < 3:
                                esempi[nome].append({"riga": numero, "testo": linea.strip()[:240]})
            risultato = {"ok": True, "file": str(path), "conteggi": conteggi, "esempi": esempi, "nota": "indicatori euristici; non provano da soli un attacco"}
            self._log(f"Analisi log locale completata: {path}")
            return risultato
        except OSError as errore:
            return {"ok": False, "errore": f"Impossibile leggere il log: {errore}"}

    def _log(self, messaggio):
        if not self.logger:
            return
        try:
            self.logger.info(messaggio)
        except Exception:
            pass
