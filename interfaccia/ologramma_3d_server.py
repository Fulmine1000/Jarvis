"""Server HTTP locale per il visualizzatore 3D e ponte unidirezionale dei gesti.

Ascolta esclusivamente su loopback. Espone soltanto la pagina statica e una coda
di eventi gestuali; non offre endpoint per eseguire comandi o leggere file.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


_BASE = Path(__file__).resolve().parent
_PAGE = _BASE / "ologramma_3d.html"
_MODELS = _BASE / "modelli_ologramma_3d"
_MODEL_ERROR = ""
_MODEL_LOCK = threading.Lock()
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


def _scarica_file(url: str, destinazione: Path) -> None:
    """Scarica un file HTTPS con curl, compatibile con macOS meno recenti."""
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    temporaneo = destinazione.with_name(destinazione.name + ".download")
    try:
        risultato = subprocess.run(
            ["curl", "-fLsS", "--retry", "2", "--connect-timeout", "10",
             "--max-time", "90", url, "-o", str(temporaneo)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=100,
            check=False,
        )
        if risultato.returncode != 0:
            raise RuntimeError((risultato.stderr or "curl non è riuscito a scaricare il file").strip())
        if not temporaneo.is_file() or temporaneo.stat().st_size < 100:
            raise RuntimeError("Il file scaricato è vuoto o troppo piccolo.")
        os.replace(str(temporaneo), str(destinazione))
    finally:
        try:
            temporaneo.unlink()
        except OSError:
            pass


def _prepara_modelli() -> None:
    """Scarica e verifica una sola volta i modelli TensorFlow.js richiesti."""
    global _MODEL_ERROR
    base = "https://tfhub.dev/mediapipe/tfjs-model/handpose_3d"
    with _MODEL_LOCK:
        try:
            for nome in ("detector", "landmark"):
                cartella = _MODELS / nome
                json_path = cartella / "model.json"
                valido = False
                try:
                    descrizione = json.loads(json_path.read_text(encoding="utf-8"))
                    percorsi = [
                        p for gruppo in descrizione.get("weightsManifest", [])
                        for p in gruppo.get("paths", [])
                    ]
                    valido = (
                        bool(percorsi)
                        and all(isinstance(p, str) and Path(p).name == p for p in percorsi)
                        and all((cartella / p).is_file() and (cartella / p).stat().st_size > 100
                                for p in percorsi)
                    )
                except (OSError, ValueError, TypeError):
                    valido = False
                if valido:
                    continue
                _scarica_file(f"{base}/{nome}/lite/1/model.json?tfjs-format=file", json_path)
                descrizione = json.loads(json_path.read_text(encoding="utf-8"))
                percorsi = [
                    p for gruppo in descrizione.get("weightsManifest", [])
                    for p in gruppo.get("paths", [])
                ]
                if not percorsi or any(not isinstance(p, str) or Path(p).name != p for p in percorsi):
                    raise RuntimeError(f"Manifest dei pesi non valido per {nome}.")
                for peso in percorsi:
                    _scarica_file(f"{base}/{nome}/lite/1/{peso}?tfjs-format=file", cartella / peso)
            _MODEL_ERROR = ""
        except Exception as exc:
            _MODEL_ERROR = f"{type(exc).__name__}: {exc}"


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
            if path == "/ologramma_3d_worker.js":
                try:
                    payload = (_BASE / "ologramma_3d_worker.js").read_bytes()
                except OSError:
                    self.send_error(404)
                    return
                self.send_response(200)
                self._headers("application/javascript; charset=utf-8")
                self.wfile.write(payload)
                return
            if path.startswith("/models/"):
                # Whitelist stretta: vengono esposti solo i modelli del visualizzatore.
                allowed = {
                    "/models/detector/model.json": (_MODELS / "detector" / "model.json", "application/json; charset=utf-8"),
                    "/models/detector/group1-shard1of1.bin": (_MODELS / "detector" / "group1-shard1of1.bin", "application/octet-stream"),
                    "/models/landmark/model.json": (_MODELS / "landmark" / "model.json", "application/json; charset=utf-8"),
                    "/models/landmark/group1-shard1of1.bin": (_MODELS / "landmark" / "group1-shard1of1.bin", "application/octet-stream"),
                }
                item = allowed.get(path)
                if item is None:
                    self.send_error(404)
                    return
                model_path, content_type = item
                try:
                    payload = model_path.read_bytes()
                except OSError:
                    payload = json.dumps({
                        "error": "Modello locale non disponibile",
                        "detail": _MODEL_ERROR or "Il download automatico non è riuscito."
                    }, ensure_ascii=False).encode("utf-8")
                    self.send_response(503)
                    self._headers("application/json; charset=utf-8")
                    self.wfile.write(payload)
                    return
                self.send_response(200)
                self._headers(content_type)
                self.wfile.write(payload)
                return
            if path == "/state":
                with _LOCK:
                    events = list(_EVENTS)
                payload = json.dumps({"events": events}, ensure_ascii=False).encode("utf-8")
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
    # Scarica i modelli prima di aprire il browser, così il viewer usa solo URL locali.
    _prepara_modelli()
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
