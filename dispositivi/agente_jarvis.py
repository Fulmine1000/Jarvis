from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROTOCOLLO = "JARVIS-MULTIDEVICE/1"
VERSIONE = "1.0"


def identita_dispositivo() -> dict:
    nome = platform.node() or "dispositivo-jarvis"
    return {
        "id": hashlib.sha256(f"{nome}:{platform.system()}:{platform.machine()}".encode()).hexdigest()[:24],
        "nome": nome,
        "piattaforma": platform.system() or "sconosciuta",
        "architettura": platform.machine() or "sconosciuta",
        "protocollo": PROTOCOLLO,
        "agente": VERSIONE,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "JarvisAgent/1.0"

    def _json(self, codice: int, dati: dict):
        raw = json.dumps(dati, ensure_ascii=False).encode("utf-8")
        self.send_response(codice)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/jarvis/handshake":
            self._json(200, {"protocollo": PROTOCOLLO, "timestamp": dt.datetime.now().isoformat(timespec="seconds"), "dispositivo": identita_dispositivo(), "capacita": ["trasferimento", "ricezione_manifesto", "stato"]})
            return
        if self.path == "/jarvis/stato":
            self._json(200, {"protocollo": PROTOCOLLO, "stato": "online", "dispositivo": identita_dispositivo()})
            return
        self._json(404, {"errore": "endpoint non trovato"})

    def do_POST(self):
        if self.path != "/jarvis/trasferimento":
            self._json(404, {"errore": "endpoint non trovato"})
            return
        try:
            lunghezza = int(self.headers.get("Content-Length", "0"))
            if lunghezza <= 0 or lunghezza > 2 * 1024 * 1024:
                raise ValueError("pacchetto non valido")
            dati = json.loads(self.rfile.read(lunghezza).decode("utf-8"))
            if dati.get("protocollo") != PROTOCOLLO:
                raise ValueError("protocollo incompatibile")
            ricevuti = dati.get("checksum_sha256")
            copia = dict(dati)
            copia.pop("checksum_sha256", None)
            raw = json.dumps(copia, ensure_ascii=False, indent=2).encode("utf-8")
            if ricevuti and ricevuti != hashlib.sha256(raw).hexdigest():
                raise ValueError("checksum non valido")
            root = Path(os.path.expanduser("~")) / ".jarvis"
            root.mkdir(parents=True, exist_ok=True)
            destinazione = root / "ultimo_trasferimento.json"
            destinazione.write_text(json.dumps(dati, ensure_ascii=False, indent=2), encoding="utf-8")
            self._json(200, {"ok": True, "messaggio": "Manifesto Jarvis ricevuto", "destinazione": str(destinazione), "dispositivo": identita_dispositivo()})
        except Exception as errore:
            self._json(400, {"ok": False, "errore": str(errore)})

    def log_message(self, fmt, *args):
        print(f"[Jarvis Agent] {fmt % args}")


def main():
    parser = argparse.ArgumentParser(description="Agente multi-dispositivo J.A.R.V.I.S.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print("J.A.R.V.I.S. Multi-Device Agent")
    print(json.dumps(identita_dispositivo(), ensure_ascii=False, indent=2))
    print(f"In ascolto su http://{args.host}:{args.port}/jarvis/handshake")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
