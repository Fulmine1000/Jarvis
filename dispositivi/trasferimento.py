from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import secrets
import shutil
import socket
import subprocess
import urllib.request
from pathlib import Path


class TrasferimentoJarvis:
    """Gestore del trasferimento temporaneo di Jarvis tra dispositivi.

    Il trasferimento è una migrazione di sessione, non una copia definitiva del
    Core. I dispositivi moderni possono essere associati una prima volta via
    USB e successivamente raggiunti via rete locale; i dispositivi legacy
    richiedono USB anche per il ritorno al Mac.
    """

    PROTOCOLLO = "JARVIS-MULTIDEVICE/2"
    VERSIONE = 3
    MODERNO = "moderno"
    LEGACY = "legacy"

    def __init__(self, logger=None, root=None):
        self.logger = logger
        self.root = Path(root or Path.home() / ".jarvis")
        self.root.mkdir(parents=True, exist_ok=True)
        self.identita_path = self.root / "identita_dispositivo.json"
        self.stato_path = self.root / "stato_trasferimento.json"
        self.dispositivi_path = self.root / "dispositivi_associati.json"
        self.identita = self._carica_identita()
        self.dispositivi_associati = self._carica_dispositivi()
        self.host_attivo = None

    def _log(self, livello, messaggio):
        if self.logger and hasattr(self.logger, livello):
            getattr(self.logger, livello)(messaggio)

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
        self.identita_path.write_text(json.dumps(identita, ensure_ascii=False, indent=2), encoding="utf-8")
        return identita

    def _carica_dispositivi(self):
        if self.dispositivi_path.exists():
            try:
                dati = json.loads(self.dispositivi_path.read_text(encoding="utf-8"))
                return dati if isinstance(dati, dict) else {}
            except Exception:
                pass
        return {}

    def _salva_dispositivi(self):
        self.dispositivi_path.write_text(
            json.dumps(self.dispositivi_associati, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def dispositivo(self):
        return dict(self.identita)

    def associa_usb(self, device_id, nome, modello="sconosciuto", versione_android=None):
        """Registra un telefono dopo una prima associazione fisica via USB."""
        categoria = self.classifica_telefono(modello, versione_android)
        self.dispositivi_associati[device_id] = {
            "id": device_id,
            "nome": nome,
            "modello": modello,
            "categoria": categoria,
            "versione_android": versione_android,
            "associato": dt.datetime.now().isoformat(timespec="seconds"),
            "autorizzato": True,
            "wireless": categoria == self.MODERNO,
        }
        self._salva_dispositivi()
        self._log("info", f"Dispositivo associato via USB: {nome} ({categoria})")
        return self.dispositivi_associati[device_id]

    def classifica_telefono(self, modello="", versione_android=None):
        """Classifica un telefono come moderno o legacy senza assumere una marca."""
        if versione_android:
            try:
                return self.MODERNO if int(str(versione_android).split(".")[0]) >= 10 else self.LEGACY
            except (ValueError, TypeError):
                pass
        testo = f"{modello}".lower()
        indicatori_legacy = ("nexus s", "galaxy nexus", "android 2", "android 3", "android 4", "android 5", "android 6", "android 7", "android 8", "android 9")
        return self.LEGACY if any(x in testo for x in indicatori_legacy) else self.MODERNO

    def dispositivo_associato(self, device_id=None, nome=None):
        if device_id and device_id in self.dispositivi_associati:
            return self.dispositivi_associati[device_id]
        if nome:
            nome = nome.strip().lower()
            for dispositivo in self.dispositivi_associati.values():
                if dispositivo.get("nome", "").lower() == nome or dispositivo.get("modello", "").lower() == nome:
                    return dispositivo
        return None

    def rileva_usb(self):
        """Rileva dispositivi Android esposti via ADB sul Mac, se disponibile."""
        adb = shutil.which("adb")
        if not adb:
            return []
        try:
            risultato = subprocess.run(
                [adb, "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
        except Exception as errore:
            self._log("warning", f"ADB non disponibile: {errore}")
            return []
        dispositivi = []
        for riga in risultato.stdout.splitlines()[1:]:
            riga = riga.strip()
            if not riga or riga.startswith("*"):
                continue
            parti = riga.split()
            if len(parti) < 2 or parti[1] != "device":
                continue
            dati = {"id": parti[0], "stato": parti[1]}
            for parte in parti[2:]:
                if ":" in parte:
                    chiave, valore = parte.split(":", 1)
                    dati[chiave] = valore
            dispositivi.append(dati)
        return dispositivi

    def primo_collegamento_usb(self, nome, modello="sconosciuto", versione_android=None):
        """Associa il primo telefono compatibile rilevato via USB."""
        rilevati = self.rileva_usb()
        if not rilevati:
            return {"ok": False, "errore": "Nessun dispositivo Android autorizzato via ADB."}
        device = rilevati[0]
        profilo = self.associa_usb(device["id"], nome, modello, versione_android)
        return {"ok": True, "dispositivo": profilo}

    def puo_trasferire_wireless(self, device_id=None, nome=None):
        dispositivo = self.dispositivo_associato(device_id, nome)
        return bool(dispositivo and dispositivo.get("autorizzato") and dispositivo.get("wireless"))

    def trasferisci_sessione(self, device_id=None, nome=None, indirizzo=None, porta=8765):
        """Prepara una migrazione temporanea.

        Se l'host moderno espone l'Agente Jarvis, prova il trasferimento di rete.
        Altrimenti restituisce uno stato esplicito senza fingere che il telefono
        abbia ricevuto il Core.
        """
        dispositivo = self.dispositivo_associato(device_id, nome)
        if not dispositivo:
            return {"ok": False, "errore": "Telefono non associato. Eseguire prima l'associazione USB."}
        if dispositivo.get("categoria") == self.LEGACY and not self.rileva_usb():
            return {"ok": False, "errore": "Questo telefono legacy richiede il collegamento USB."}
        if dispositivo.get("categoria") == self.MODERNO and not indirizzo:
            return {
                "ok": False,
                "richiede_agente": True,
                "errore": "Telefono associato: serve l'Agente Jarvis sul telefono per completare il trasferimento wireless.",
            }
        if indirizzo:
            verifica = self.verifica_host(indirizzo, porta)
            if not verifica:
                return {"ok": False, "errore": "Agente Jarvis non raggiungibile sul telefono."}
            risultato = self.trasferisci_http(indirizzo, porta)
            if risultato.get("ok", False):
                self.host_attivo = dispositivo["id"]
            return risultato
        return {"ok": False, "errore": "Trasporto di trasferimento non disponibile."}

    def ritorna_al_mac(self, device_id=None, nome=None, indirizzo=None, porta=8765):
        dispositivo = self.dispositivo_associato(device_id, nome)
        if not dispositivo:
            return {"ok": False, "errore": "Telefono non associato."}
        if dispositivo.get("categoria") == self.LEGACY and not self.rileva_usb():
            return {"ok": False, "richiede_usb": True, "errore": "Collegare il telefono legacy al Mac tramite USB per completare il ritorno."}
        if indirizzo:
            try:
                url = f"http://{indirizzo}:{int(porta)}/jarvis/ritorno"
                richiesta = urllib.request.Request(url, data=b"{}", method="POST", headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(richiesta, timeout=8) as risposta:
                    risultato = json.loads(risposta.read().decode("utf-8"))
                if risultato.get("ok"):
                    self.host_attivo = None
                return risultato
            except Exception as errore:
                return {"ok": False, "errore": str(errore)}
        self.host_attivo = None
        return {"ok": True, "azione": "sessione_ritornata_al_mac", "nota": "Il Core resta sul Mac; il telefono deve disattivare il proprio agente."}

    def crea_pacchetto(self, gestore=None, destinazione=None):
        dispositivi = []
        if gestore:
            for nome in gestore.elenco():
                dispositivo = gestore.cerca(nome)
                dispositivi.append({"nome": nome, "modello": getattr(dispositivo, "modello", None), "capacita": gestore.capacita_dispositivo(nome), "base": bool(getattr(dispositivo, "base", False))})
        pacchetto = {
            "protocollo": self.PROTOCOLLO,
            "versione": self.VERSIONE,
            "creato": dt.datetime.now().isoformat(timespec="seconds"),
            "origine": self.dispositivo(),
            "dispositivi": dispositivi,
            "contenuto": {"identita": True, "preferenze": True, "memoria": "solo se esportata esplicitamente dall'utente", "credenziali": False},
        }
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
        try:
            with urllib.request.urlopen(f"http://{indirizzo}:{int(porta)}/jarvis/handshake", timeout=timeout) as risposta:
                dati = json.loads(risposta.read().decode("utf-8"))
            return dati if dati.get("protocollo") == self.PROTOCOLLO else None
        except Exception:
            return None

    def codice_associazione(self):
        return f"Codice di associazione temporaneo: {secrets.token_urlsafe(12)}."

    def supporto(self):
        return {
            "protocollo": self.PROTOCOLLO,
            "versione": self.VERSIONE,
            "trasferimento_usb_prima_associazione": True,
            "trasferimento_wireless_dopo_associazione": True,
            "telefoni_legacy_usb": True,
            "sessione_temporanea": True,
            "core_permanente_sul_mac": True,
            "nota": "Per il trasferimento reale il telefono deve eseguire un Agente Jarvis compatibile.",
        }

    def stato(self):
        return {
            "nome": "Trasferimento multi-dispositivo",
            "stato": "attivo",
            "protocollo": self.PROTOCOLLO,
            "versione": self.VERSIONE,
            "dispositivo": self.identita.get("nome"),
            "host_attivo": self.host_attivo,
            "dispositivi_associati": self.dispositivi_associati,
            "trasferimento_usb": True,
            "trasferimento_wireless": True,
            "sessione_temporanea": True,
        }
