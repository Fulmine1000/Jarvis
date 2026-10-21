"""Server HTTP locale per il visualizzatore 3D e ponte unidirezionale dei gesti.

Ascolta esclusivamente su loopback. Espone soltanto la pagina statica e una coda
di eventi gestuali; non offre endpoint per eseguire comandi o leggere file.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


_PAGE = Path(__file__).resolve().with_name("ologramma_3d.html")
_LOCK = threading.Lock()
_EVENTS = []
_SEQUENCE = 0
_SERVER = None
_SERVER_THREAD = None
_PORT = 8766


def aggiorna_gesto(gesto: str) -> None:
    """Accoda soltanto i gesti consentiti per la visualizzazione 3D."""
    global _SEQUENCE
    if gesto not in {"scorri_destra", "scorri_sinistra", "zoom_avanti", "zoom_indietro", "pizzico"}:
        return
    with _LOCK:
        _SEQUENCE += 1
        _EVENTS.append({"seq": _SEQUENCE, "gesture": gesto})
        del _EVENTS[:-40]


def _handler_factory():
    class Handler(BaseHTTPRequestHandler):
        server_version = "JarvisHologram/1.0"

        def _headers(self, content_type):
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()

        def do_GET(self):
            path = urlparse(self.path).path
            if path in ("/", "/index.html"):
                try:
                    payload = _PAGE.read_bytes()
                except OSError:
                    self.send_error(404)
                    return
                self.send_response(200)
                self._headers("text/html; charset=utf-8")
                self.wfile.write(payload)
                return
            if path == "/state":
                with _LOCK:
                    payload = json.dumps({"events": list(_EVENTS)}, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8766")
                self._headers("application/json; charset=utf-8")
                self.wfile.write(payload)
                return
            if path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            self.send_error(404)

        def log_message(self, format, *args):
            return

    return Handler


def avvia_server(port: int = _PORT) -> str:
    """Avvia il server una sola volta e restituisce l'URL locale del viewer."""
    global _SERVER, _SERVER_THREAD, _PORT
    with _LOCK:
        if _SERVER is not None:
            return f"http://127.0.0.1:{_PORT}/"
        _PORT = int(port)
        _SERVER = ThreadingHTTPServer(("127.0.0.1", _PORT), _handler_factory())
        _SERVER.daemon_threads = True
        _SERVER_THREAD = threading.Thread(target=_SERVER.serve_forever, name="JarvisHologramHTTP", daemon=True)
        _SERVER_THREAD.start()
        return f"http://127.0.0.1:{_PORT}/"


def ferma_server() -> None:
    global _SERVER, _SERVER_THREAD
    with _LOCK:
        server = _SERVER
        _SERVER = None
        _SERVER_THREAD = None
    if server is not None:
        server.shutdown()
        server.server_close()


__all__ = ["aggiorna_gesto", "avvia_server", "ferma_server"]
