from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import secrets
import socket
from pathlib import Path


class TrasferimentoJarvis:
    """Livello portatile per usare Jarvis su più dispositivi.

    Non presume che il dispositivo remoto possa eseguire Python: crea un
    profilo di identità/capacità condivisibile e mantiene separati i dati
    trasferibili dalle capacità specifiche della piattaforma.
    """

    PROTOCOLLO = "JARVIS-MULTIDEVICE/1"

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
        identita = {
            "id": secrets.token_hex(12),
            "nome": nome,
            "piattaforma": platform.system() or "sconosciuta",
            "architettura": platform.machine() or "sconosciuta",
            "protocollo": self.PROTOCOLLO,
            "creato": dt.datetime.now().isoformat(timespec="seconds"),
        }
        self.identita_path.write_text(
            json.dumps(identita, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return identita

    def dispositivo(self):
        """Descrizione portatile del dispositivo corrente."""
        return dict(self.identita)

    def crea_pacchetto(self, gestore=None, destinazione=None):
        """Crea un manifesto trasferibile, senza copiare segreti o credenziali."""
        dispositivi = []
        if gestore:
            for nome in gestore.elenco():
                dispositivo = gestore.cerca(nome)
                dispositivi.append({
                    "nome": nome,
                    "modello": getattr(dispositivo, "modello", None),
                    "capacita": gestore.capacita_dispositivo(nome),
                    "base": bool(getattr(dispositivo, "base", False)),
                })
        pacchetto = {
            "protocollo": self.PROTOCOLLO,
            "versione": 1,
            "creato": dt.datetime.now().isoformat(timespec="seconds"),
            "origine": self.dispositivo(),
            "dispositivi": dispositivi,
            "contenuto": {
                "identita": True,
                "preferenze": True,
                "memoria": "solo se esportata esplicitamente dall'utente",
                "credenziali": False,
            },
        }
        path = Path(destinazione) if destinazione else self.root / "jarvis_trasferimento.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(pacchetto, ensure_ascii=False, indent=2).encode("utf-8")
        pacchetto["checksum_sha256"] = hashlib.sha256(raw).hexdigest()
        path.write_text(json.dumps(pacchetto, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stato_path.write_text(
            json.dumps({"ultimo_pacchetto": str(path), "data": dt.datetime.now().isoformat()}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._log("info", f"Pacchetto trasferimento Jarvis creato: {path}")
        return f"Pacchetto Jarvis creato in {path}."

    def importa_pacchetto(self, percorso):
        """Valida un manifesto Jarvis e ne importa solo metadati non sensibili."""
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

    def codice_associazione(self):
        """Genera un codice temporaneo per un futuro collegamento remoto."""
        codice = secrets.token_urlsafe(12)
        return f"Codice di associazione temporaneo: {codice}."

    def supporto(self):
        return {
            "protocollo": self.PROTOCOLLO,
            "piattaforma": self.identita.get("piattaforma"),
            "architettura": self.identita.get("architettura"),
            "trasferimento_manifesto": True,
            "connessione_remota": False,
            "nota": "La connessione remota richiede un connettore/agente compatibile sul dispositivo destinatario.",
        }

    def stato(self):
        return {
            "nome": "Trasferimento multi-dispositivo",
            "stato": "attivo",
            "protocollo": self.PROTOCOLLO,
            "dispositivo": self.identita.get("nome"),
        }

    def _log(self, livello, messaggio):
        if self.logger and hasattr(self.logger, livello):
            getattr(self.logger, livello)(messaggio)
