"""Controllo opzionale di TV LG webOS tramite WebSocket.

La TV deve essere configurata con il proprio indirizzo IP in config/config.json.
Al primo collegamento webOS può mostrare una richiesta di autorizzazione.
Se la libreria websocket-client o la TV non sono disponibili, Jarvis continua
normalmente senza bloccare l'avvio.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from typing import Any


class LgWebOSTv:
    """Adapter minimale e sicuro per comandi LG webOS."""

    def __init__(self, name="tv", ip=None, client_key=None, timeout=4, logger=None):
        self.nome = name
        self.ip = ip
        self.client_key = client_key
        self.timeout = timeout
        self.logger = logger
        self.ws = None
        self.connected = False
        self._lock = threading.Lock()
        self._pending: dict[str, dict[str, Any]] = {}

    def disponibile(self):
        return bool(self.ip)

    def connetti(self):
        if not self.ip:
            return "TV LG non configurata: manca l'indirizzo IP."
        try:
            import websocket
        except ImportError:
            return "Controllo TV LG non disponibile: installa websocket-client."

        with self._lock:
            try:
                self.ws = websocket.create_connection(
                    f"ws://{self.ip}:3000",
                    timeout=self.timeout,
                )
                self.ws.send(json.dumps(self._registration()))
                response = json.loads(self.ws.recv())
                payload = response.get("payload", {})
                key = payload.get("client-key")
                if key:
                    self.client_key = key
                    self._salva_client_key(key)
                self.connected = response.get("type") in {"registered", "response"}
                return "TV LG collegata." if self.connected else "TV LG non autorizzata."
            except Exception as exc:
                self.connected = False
                self.ws = None
                self._log(f"Connessione TV LG fallita: {exc}")
                return f"Impossibile collegarsi alla TV LG: {exc}"

    def disconnetti(self):
        with self._lock:
            try:
                if self.ws:
                    self.ws.close()
            finally:
                self.ws = None
                self.connected = False
        return "TV LG disconnessa."

    def comando(self, uri: str, payload: dict | None = None):
        if not self.connected and "ssap://" in uri:
            risultato = self.connetti()
            if not self.connected:
                return risultato
        if not self.ws:
            return "TV LG non connessa."
        request_id = str(uuid.uuid4())
        message = {
            "id": request_id,
            "type": "request",
            "uri": uri,
            "payload": payload or {},
        }
        try:
            with self._lock:
                self.ws.send(json.dumps(message))
                response = json.loads(self.ws.recv())
            if response.get("type") == "error":
                return f"TV LG: {response.get('error', 'errore')}"
            return response.get("payload", response)
        except Exception as exc:
            self.connected = False
            return f"Errore comando TV LG: {exc}"

    def accendi(self):
        # Alcuni modelli non supportano l'accensione via LAN; non viene simulata.
        return "L'accensione via rete dipende dal modello LG e da Wake-on-LAN/webOS."

    def spegni(self):
        return self.comando("ssap://system/turnOff")

    def volume(self, livello: int):
        livello = max(0, min(100, int(livello)))
        return self.comando("ssap://audio/setVolume", {"volume": livello})

    def mute(self, attivo: bool = True):
        return self.comando("ssap://audio/setMute", {"mute": bool(attivo)})

    def tasto(self, key: str):
        return self.comando("ssap://com.webos.service.ime/sendEnterKey", {"key": key})

    def stato(self):
        return {
            "nome": self.nome,
            "tipo": "LG webOS",
            "ip_configurato": bool(self.ip),
            "connessa": self.connected,
            "client_key": bool(self.client_key),
        }

    def _registration(self):
        payload = {
            "manifest": {
                "manifestVersion": 1,
                "appVersion": "1.0",
                "signed": {"created": "Jarvis", "appId": "com.jarvis.assistant", "localizedAppNames": {"": "Jarvis"}},
                "permissions": [
                    "LAUNCH",
                    "CONTROL_AUDIO",
                    "CONTROL_POWER",
                    "READ_CURRENT_CHANNEL",
                    "READ_TV_CURRENT_TIME",
                    "CONTROL_INPUT_TEXT",
                ],
            },
            "pairingType": "PIN",
        }
        if self.client_key:
            payload["client-key"] = self.client_key
        return {"id": str(uuid.uuid4()), "type": "register", "payload": payload}

    def _salva_client_key(self, key: str):
        path = os.path.join("config", "lg_tv_client_key.txt")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as file:
                file.write(key)
        except OSError:
            pass

    def _log(self, message):
        if self.logger:
            try:
                self.logger.warning(message)
            except Exception:
                pass
