from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import secrets
import socket
import urllib.request
from pathlib import Path


class TrasferimentoJarvis:
    """Trasferimento portabile di Jarvis tra host compatibili.

    Il trasferimento separa il Core dai connettori della piattaforma. Il
    pacchetto contiene metadati e identità non sensibili; credenziali e memoria
    personale non vengono esportate automaticamente.
    """

    PROTOCOLLO = "JARVIS-MULTIDEVICE/1"
    VERSIONE = 2

    def __init__(self, logger=None, root=None):
        self.logger = logger
        self.root = Path(root or Path.home() / ".jarvis")
        self.root.mkdir(parents=True, exist_ok=True)
        self.identita_path = self.root / "identita_dispositivo.json"
        self.stato_path = self.root / "stato_trasferimento.json"
        self.identita = self._carica_identita()

    def _carica_identita(self):
        if self.identita_path.exists():
            try:
                return json.loads(self.identita_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        nome = socket.gethostname() or platform.node() or "dispositivo"
        identita = {"id": secrets.token_hex(12), "nome": nome, "piattaforma": platform.system() or "sconosciuta", "architettura": platform.machine() or "sconosciuta", "protocollo": self.PROTOCOLLO, "creato": dt.datetime.now().isoformat(timespec="seconds")}
        self.identita_path.write_text(json.dumps(identita, ensure_ascii=False, indent=2), encoding="utf-8")
        return identita

    def dispositivo(self):
        return dict(self.identita)

    def crea_pacchetto(self, gestore=None, destinazione=None):
        dispositivi = []
        if gestore:
            for nome in gestore.elenco():
                dispositivo = gestore.cerca(nome)
                dispositivi.append({"nome": nome, "modello": getattr(dispositivo, "modello", None), "capacita": gestore.capacita_dispositivo(nome), "base": bool(getattr(dispositivo, "base", False))})
        pacchetto = {"protocollo": self.PROTOCOLLO, "versione": self.VERSIONE, "creato": dt.datetime.now().isoformat(timespec="seconds"), "origine": self.dispositivo(), "dispositivi": dispositivi, "contenuto": {"identita": True, "preferenze": True, "memoria": "solo se esportata esplicitamente dall'utente", "credenziali": False}}
        raw = json.dumps(pacchetto, ensure_ascii=False, indent=2).encode("utf-8")
        pacchetto["checksum_sha256"] = hashlib.sha256(raw).hexdigest()
        path = Path(destinazione) if destinazione else self.root / "jarvis_trasferimento.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(pacchetto, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stato_path.write_text(json.dumps({"ultimo_pacchetto": str(path), "data": dt.datetime.now().isoformat()}, ensure_ascii=False, indent=2), encoding="utf-8")
        self._log("info", f"Pacchetto trasferimento Jarvis creato: {path}")
        return f"Pacchetto Jarvis creato in {path}."

    def importa_pacchetto(self, percorso):
        path = Path(os.path.expanduser(str(percorso)))
        if not path.exists():
            return "Pacchetto Jarvis non trovato."
        try:
            dati = json.loads(path.read_text(encoding="utf-8"))
            if dati.get("protocollo") != self.PROTOCOLLO:
                return "Pacchetto non compatibile con il protocollo Jarvis."
            origine = dati.get("origine") or {}
            self._log("info", f"Pacchetto ricevuto da {origine.get('nome', 'dispositivo sconosciuto')}")
            return f"Pacchetto Jarvis compatibile ricevuto da {origine.get('nome', 'dispositivo sconosciuto')}."
        except Exception:
            return "Pacchetto Jarvis non valido."

    def trasferisci_http(self, indirizzo, porta=8765, timeout=8):
        """Invia il manifesto a un Agente Jarvis compatibile sulla rete locale."""
        pacchetto = self.root / "jarvis_trasferimento.json"
        if not pacchetto.exists():
            self.crea_pacchetto()
        dati = pacchetto.read_bytes()
        url = f"http://{indirizzo}:{int(porta)}/jarvis/trasferimento"
        richiesta = urllib.request.Request(url, data=dati, method="POST", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(richiesta, timeout=timeout) as risposta:
                result = json.loads(risposta.read().decode("utf-8"))
            self._log("info", f"Trasferimento remoto completato verso {indirizzo}:{porta}")
            return result
        except Exception as errore:
            self._log("warning", f"Trasferimento remoto fallito verso {indirizzo}:{porta}: {errore}")
            return {"ok": False, "errore": str(errore)}

    def verifica_host(self, indirizzo, porta=8765, timeout=4):
        """Verifica se un dispositivo espone l'Agente Jarvis."""
        try:
            with urllib.request.urlopen(f"http://{indirizzo}:{int(porta)}/jarvis/handshake", timeout=timeout) as risposta:
                dati = json.loads(risposta.read().decode("utf-8"))
            return dati if dati.get("protocollo") == self.PROTOCOLLO else None
        except Exception:
            return None

    def codice_associazione(self):
        return f"Codice di associazione temporaneo: {secrets.token_urlsafe(12)}."

    def supporto(self):
        return {"protocollo": self.PROTOCOLLO, "versione": self.VERSIONE, "piattaforma": self.identita.get("piattaforma"), "architettura": self.identita.get("architettura"), "trasferimento_manifesto": True, "trasferimento_rete": True, "agente_portatile": True, "nota": "Il dispositivo destinatario deve eseguire un agente/connettore Jarvis compatibile."}

    def stato(self):
        return {"nome": "Trasferimento multi-dispositivo", "stato": "attivo", "protocollo": self.PROTOCOLLO, "versione": self.VERSIONE, "dispositivo": self.identita.get("nome"), "trasferimento_rete": True}

    def _log(self, livello, messaggio):
        if self.logger and hasattr(self.logger, livello):
            getattr(self.logger, livello)(messaggio)
