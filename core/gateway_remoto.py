"""Gateway HTTP locale e autenticato per i terminali remoti di Jarvis.

Il gateway resta legato a loopback per impostazione predefinita. Per l'accesso
remoto va pubblicato esclusivamente dietro un reverse proxy HTTPS o un tunnel
autenticato: non aprire direttamente la porta del Mac su Internet.
"""
from __future__ import annotations

import hmac
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


MAX_BODY_BYTES = 8 * 1024
MAX_TEXT_CHARS = 2000


class GatewayJarvis:
    """Espone chat e stato minimo del Core a client autorizzati."""

    def __init__(
        self,
        kernel,
        host: str | None = None,
        port: int | None = None,
        token: str | None = None,
    ):
        self.kernel = kernel
        self.host = host or os.environ.get("JARVIS_GATEWAY_HOST", "127.0.0.1")
        self.port = int(port if port is not None else os.environ.get("JARVIS_GATEWAY_PORT", "8767"))
        self.token = token if token is not None else os.environ.get("JARVIS_GATEWAY_TOKEN", "")
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def attivo(self) -> bool:
        return self._server is not None

    def avvia(self) -> bool:
        if self.attivo:
            return True
        if not self.token or len(self.token) < 32:
            raise ValueError("JARVIS_GATEWAY_TOKEN deve contenere almeno 32 caratteri casuali")
        gateway = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "JarvisGateway"
            sys_version = ""

            def log_message(self, fmt, *args):
                logger = getattr(gateway.kernel, "logger", None)
                if logger:
                    logger.info("Gateway remoto: " + (fmt % args))

            def _json(self, status: int, payload: dict[str, Any]):
                raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(raw)

            def _autorizzato(self) -> bool:
                header = self.headers.get("Authorization", "")
                schema, _, supplied = header.partition(" ")
                return schema.lower() == "bearer" and hmac.compare_digest(
                    supplied.encode("utf-8"), gateway.token.encode("utf-8")
                )

            def do_GET(self):
                if self.path != "/v1/health":
                    self._json(404, {"ok": False, "errore": "endpoint_non_trovato"})
                    return
                if not self._autorizzato():
                    self._json(401, {"ok": False, "errore": "non_autorizzato"})
                    return
                self._json(200, {
                    "ok": True,
                    "nome": getattr(gateway.kernel, "nome", "J.A.R.V.I.S."),
                    "stato": getattr(gateway.kernel, "stato", "sconosciuto"),
                })

            def do_POST(self):
                if self.path != "/v1/chat":
                    self._json(404, {"ok": False, "errore": "endpoint_non_trovato"})
                    return
                if not self._autorizzato():
                    self._json(401, {"ok": False, "errore": "non_autorizzato"})
                    return
                content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                if content_type != "application/json":
                    self._json(415, {"ok": False, "errore": "content_type_non_supportato"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    self._json(400, {"ok": False, "errore": "content_length_non_valido"})
                    return
                if length < 1 or length > MAX_BODY_BYTES:
                    self._json(413, {"ok": False, "errore": "dimensione_richiesta_non_valida"})
                    return
                try:
                    body = self.rfile.read(length)
                    payload = json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self._json(400, {"ok": False, "errore": "json_non_valido"})
                    return
                if not isinstance(payload, dict) or set(payload) != {"text"}:
                    self._json(400, {"ok": False, "errore": "schema_non_valido"})
                    return
                testo = payload.get("text")
                if not isinstance(testo, str) or not testo.strip() or len(testo) > MAX_TEXT_CHARS:
                    self._json(400, {"ok": False, "errore": "testo_non_valido"})
                    return
                if not getattr(gateway.kernel, "intelligenza", None):
                    self._json(503, {"ok": False, "errore": "motore_non_disponibile"})
                    return
                try:
                    # Solo dialogo: nessun endpoint per shell o esecuzione arbitraria.
                    with gateway._lock:
                        risposta = gateway.kernel.intelligenza.rispondi(testo.strip())
                    if not isinstance(risposta, str) or not risposta.strip():
                        self._json(503, {"ok": False, "errore": "risposta_non_disponibile"})
                        return
                    self._json(200, {"ok": True, "response": risposta})
                except Exception as errore:
                    logger = getattr(gateway.kernel, "logger", None)
                    if logger:
                        logger.warning(f"Errore richiesta gateway: {type(errore).__name__}")
                    self._json(500, {"ok": False, "errore": "errore_interno"})

        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        self._server.daemon_threads = True
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="JarvisGateway",
            daemon=True,
        )
        self._thread.start()
        return True

    def ferma(self) -> bool:
        server = self._server
        if server is None:
            return True
        self._server = None
        server.shutdown()
        server.server_close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None
        return True

    def stato(self) -> dict[str, Any]:
        return {
            "attivo": self.attivo,
            "host": self.host,
            "porta": self.port,
            "autenticazione_configurata": bool(self.token and len(self.token) >= 32),
            "accesso_remoto_diretto": False,
            "endpoint": ["/v1/health", "/v1/chat"],
        }
