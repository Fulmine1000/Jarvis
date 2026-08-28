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
import threading
import time
import urllib.request
from pathlib import Path


class TrasferimentoJarvis:
    """Gestisce il trasferimento della sessione Jarvis tramite USB/ADB.

    Il Core Python resta sul Mac. Il telefono riceve la sessione operativa e
    una HUD locale; quando il cavo viene scollegato la sessione locale rimane
    attiva e può continuare a funzionare offline. Al ricollegamento USB il
    bridge viene ripristinato automaticamente.
    """

    PROTOCOLLO = "JARVIS-MULTIDEVICE/2"
    VERSIONE = 5
    MODERNO = "moderno"
    LEGACY = "legacy"
    HOST_PORTA_TELEFONO = 18765
    PORTA_REVERSE_MAC = 8766

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
        self._monitor_attivo = False
        self._monitor_thread = None
        self._ultimo_usb = None

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
        identita = {"id": secrets.token_hex(12), "nome": nome, "piattaforma": platform.system() or "sconosciuta", "architettura": platform.machine() or "sconosciuta", "protocollo": self.PROTOCOLLO, "creato": dt.datetime.now().isoformat(timespec="seconds")}
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
        self.dispositivi_path.write_text(json.dumps(self.dispositivi_associati, ensure_ascii=False, indent=2), encoding="utf-8")

    def dispositivo(self):
        return dict(self.identita)

    def associa_usb(self, device_id, nome, modello="sconosciuto", versione_android=None):
        categoria = self.classifica_telefono(modello, versione_android)
        self.dispositivi_associati[device_id] = {"id": device_id, "nome": nome, "modello": modello, "categoria": categoria, "versione_android": versione_android, "associato": dt.datetime.now().isoformat(timespec="seconds"), "autorizzato": True, "wireless": categoria == self.MODERNO}
        self._salva_dispositivi()
        self._log("info", f"Dispositivo associato via USB: {nome} ({categoria})")
        return self.dispositivi_associati[device_id]

    def classifica_telefono(self, modello="", versione_android=None):
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
        adb = shutil.which("adb")
        if not adb:
            return []
        try:
            risultato = subprocess.run([adb, "devices", "-l"], capture_output=True, text=True, timeout=8, check=False)
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
        rilevati = self.rileva_usb()
        if not rilevati:
            return {"ok": False, "errore": "Nessun dispositivo Android autorizzato via ADB."}
        device = rilevati[0]
        profilo = self.associa_usb(device["id"], nome, modello, versione_android)
        return {"ok": True, "dispositivo": profilo}

    def _forward_usb(self, device_id, porta=8765):
        adb = shutil.which("adb")
        if not adb:
            return False
        try:
            risultato = subprocess.run([adb, "-s", device_id, "forward", f"tcp:{self.HOST_PORTA_TELEFONO}", f"tcp:{porta}"], capture_output=True, text=True, timeout=8, check=False)
            if risultato.returncode != 0:
                self._log("warning", f"ADB forward fallito: {risultato.stderr.strip()}")
                return False
            return True
        except Exception as errore:
            self._log("warning", f"ADB forward non disponibile: {errore}")
            return False

    def _reverse_usb(self, device_id, porta_mac=8765):
        adb = shutil.which("adb")
        if not adb:
            return False
        try:
            risultato = subprocess.run([adb, "-s", device_id, "reverse", f"tcp:{self.PORTA_REVERSE_MAC}", f"tcp:{porta_mac}"], capture_output=True, text=True, timeout=8, check=False)
            if risultato.returncode != 0:
                self._log("warning", f"ADB reverse fallito: {risultato.stderr.strip()}")
                return False
            return True
        except Exception as errore:
            self._log("warning", f"ADB reverse non disponibile: {errore}")
            return False

    def _prepara_bridge_usb(self, dispositivo, porta_mac=8765):
        device_id = dispositivo["id"]
        forward = self._forward_usb(device_id, porta_mac)
        reverse = self._reverse_usb(device_id, porta_mac)
        return forward and reverse

    def _url_dispositivo(self, dispositivo, indirizzo=None, porta=8765):
        if indirizzo:
            return f"http://{indirizzo}:{int(porta)}"
        if self._forward_usb(dispositivo["id"], porta):
            return f"http://127.0.0.1:{self.HOST_PORTA_TELEFONO}"
        return None

    def trasferisci_sessione(self, device_id=None, nome=None, indirizzo=None, porta=8765, core_endpoint=None):
        dispositivo = self.dispositivo_associato(device_id, nome)
        if not dispositivo:
            return {"ok": False, "errore": "Telefono non associato. Eseguire prima l'associazione USB."}
        if not indirizzo and not self._prepara_bridge_usb(dispositivo, porta):
            return {"ok": False, "richiede_usb": True, "errore": "Collegare il telefono al Mac tramite USB e autorizzare ADB."}
        base = self._url_dispositivo(dispositivo, indirizzo, porta)
        if not base:
            return {"ok": False, "richiede_usb": True, "errore": "Bridge USB non disponibile."}
        handshake = self.verifica_host(base, timeout=5)
        if not handshake:
            return {"ok": False, "errore": "Agente Jarvis non raggiungibile sul telefono."}
        if not indirizzo:
            self._reverse_usb(dispositivo["id"], porta)
        payload = {"protocollo": self.PROTOCOLLO, "versione": self.VERSIONE, "sessione": True, "modalita": "usb", "core_endpoint": core_endpoint, "reverse_endpoint": f"http://127.0.0.1:{self.PORTA_REVERSE_MAC}", "origine": self.dispositivo(), "dispositivo": dispositivo}
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            richiesta = urllib.request.Request(base + "/jarvis/sessione", data=raw, method="POST", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(richiesta, timeout=8) as risposta:
                result = json.loads(risposta.read().decode("utf-8"))
            if result.get("ok"):
                self.host_attivo = dispositivo["id"]
                self._log("info", f"Sessione Jarvis trasferita via USB a {dispositivo.get('nome', dispositivo['id'])}.")
            return result
        except Exception as errore:
            return {"ok": False, "errore": str(errore)}

    def ritorna_al_mac(self, device_id=None, nome=None, indirizzo=None, porta=8765):
        dispositivo = self.dispositivo_associato(device_id, nome)
        if not dispositivo:
            return {"ok": False, "errore": "Telefono non associato."}
        base = self._url_dispositivo(dispositivo, indirizzo, porta)
        if not base:
            return {"ok": False, "richiede_usb": True, "errore": "Collegare il telefono al Mac tramite USB per completare il ritorno."}
        try:
            richiesta = urllib.request.Request(base + "/jarvis/ritorno", data=b"{}", method="POST", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(richiesta, timeout=8) as risposta:
                result = json.loads(risposta.read().decode("utf-8"))
            if result.get("ok"):
                self.host_attivo = None
                self._log("info", "Jarvis è tornato al Mac tramite USB.")
            return result
        except Exception as errore:
            return {"ok": False, "errore": str(errore)}

    def _richiesta_ritorno_usb(self, dispositivo, porta=8765):
        base = self._url_dispositivo(dispositivo, None, porta)
        if not base:
            return False
        try:
            with urllib.request.urlopen(base + "/jarvis/ritorno_richiesto", timeout=2) as risposta:
                dati = json.loads(risposta.read().decode("utf-8"))
            return bool(dati.get("requested"))
        except Exception:
            return False

    def _notifica_usb(self, dispositivo, collegato, porta=8765):
        base = self._url_dispositivo(dispositivo, None, porta)
        if not base:
            return False
        raw = json.dumps({"connected": bool(collegato), "transport": "usb"}).encode("utf-8")
        try:
            richiesta = urllib.request.Request(base + "/jarvis/usb", data=raw, method="POST", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(richiesta, timeout=2) as risposta:
                return json.loads(risposta.read().decode("utf-8")).get("ok", False)
        except Exception:
            return False

    def avvia_monitor_usb(self, intervallo=2.0, porta=8765):
        if self._monitor_attivo:
            return
        self._monitor_attivo = True
        self._monitor_thread = threading.Thread(target=self._loop_monitor_usb, args=(float(intervallo), int(porta)), daemon=True, name="JarvisUSBMonitor")
        self._monitor_thread.start()
        self._log("info", "Monitor USB telefono attivo.")

    def ferma_monitor_usb(self):
        self._monitor_attivo = False

    def _loop_monitor_usb(self, intervallo, porta):
        while self._monitor_attivo:
            try:
                rilevati = self.rileva_usb()
                ids = {d["id"] for d in rilevati}
                if self.host_attivo and self.host_attivo not in ids:
                    self._ultimo_usb = False
                for device in rilevati:
                    if device["id"] not in self.dispositivi_associati:
                        continue
                    if self._ultimo_usb is not True:
                        self._prepara_bridge_usb(device, porta)
                        self._notifica_usb(device, True, porta)
                        self._ultimo_usb = True
                        self._log("info", f"Telefono USB riconnesso: {device['id']}.")
                    if self.host_attivo == device["id"] and self._richiesta_ritorno_usb(device, porta):
                        self.ritorna_al_mac(device_id=device["id"], porta=porta)
                time.sleep(intervallo)
            except Exception as errore:
                self._log("warning", f"Monitor USB: {errore}")
                time.sleep(intervallo)

    def crea_pacchetto(self, gestore=None, destinazione=None):
        pacchetto = {"protocollo": self.PROTOCOLLO, "versione": self.VERSIONE, "creato": dt.datetime.now().isoformat(timespec="seconds"), "origine": self.dispositivo(), "contenuto": {"tipo": "sessione", "trasporto": "usb", "core": "NON COPIATO", "memoria": "NON COPIATA", "credenziali": False}}
        raw = json.dumps(pacchetto, ensure_ascii=False, indent=2).encode("utf-8")
        pacchetto["checksum_sha256"] = hashlib.sha256(raw).hexdigest()
        path = Path(destinazione) if destinazione else self.root / "jarvis_sessione.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(pacchetto, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stato_path.write_text(json.dumps({"ultimo_pacchetto": str(path), "data": dt.datetime.now().isoformat()}, ensure_ascii=False, indent=2), encoding="utf-8")
        return f"Manifesto sessione Jarvis creato in {path}."

    def importa_pacchetto(self, percorso):
        path = Path(os.path.expanduser(str(percorso)))
        if not path.exists(): return "Manifesto non trovato."
        try:
            dati = json.loads(path.read_text(encoding="utf-8"))
            return "Manifesto sessione Jarvis compatibile ricevuto." if dati.get("protocollo") == self.PROTOCOLLO else "Manifesto non compatibile."
        except Exception:
            return "Manifesto non valido."

    def verifica_host(self, indirizzo, porta=8765, timeout=4):
        url = indirizzo if str(indirizzo).startswith("http://") else f"http://{indirizzo}:{int(porta)}"
        try:
            with urllib.request.urlopen(url.rstrip("/") + "/jarvis/handshake", timeout=timeout) as risposta:
                dati = json.loads(risposta.read().decode("utf-8"))
            return dati if dati.get("protocollo") == self.PROTOCOLLO else None
        except Exception:
            return None

    def codice_associazione(self):
        return f"Codice di associazione temporaneo: {secrets.token_urlsafe(12)}."

    def supporto(self):
        return {"protocollo": self.PROTOCOLLO, "versione": self.VERSIONE, "sessione_senza_copia_core": True, "prima_associazione_usb": True, "trasporto_principale": "USB/ADB", "offline_sul_telefono": True, "ritorno_automatico_usb": True, "core_permanente_sul_mac": True}

    def stato(self):
        return {"nome": "Sessione multi-dispositivo Jarvis", "stato": "attivo", "protocollo": self.PROTOCOLLO, "versione": self.VERSIONE, "host_attivo": self.host_attivo, "dispositivi_associati": self.dispositivi_associati, "sessione_temporanea": True, "trasporto": "USB/ADB", "core_sul_mac": True}
