from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class ServerTemporaneoJarvis:
    """Server HTTP temporaneo per testare l'accesso a Jarvis da un telefono.

    Non trasferisce il Core e non installa nulla sul dispositivo remoto.
    Espone soltanto una piccola interfaccia web raggiungibile dalla stessa
    rete locale e inoltra i messaggi a un callback fornito da Jarvis.
    """

    def __init__(self, callback=None, host="0.0.0.0", porta=8765, logger=None):
        self.callback = callback
        self.host = host
        self.porta = int(porta)
        self.logger = logger
        self.server = None
        self.thread = None

    def avvia(self):
        if self.server is not None:
            return self.indirizzo()

        callback = self.callback
        logger = self.logger

        class Handler(BaseHTTPRequestHandler):
            def _rispondi(self, status, payload, content_type="application/json; charset=utf-8"):
                raw = payload.encode("utf-8") if isinstance(payload, str) else payload
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                if self.path == "/api/stato":
                    self._rispondi(200, json.dumps({"jarvis": "online", "temporaneo": True}))
                    return
                if self.path in ("/", "/index.html"):
                    html = '''<!doctype html><html lang="it"><head><meta name="viewport" content="width=device-width,initial-scale=1"><meta charset="utf-8"><title>J.A.R.V.I.S.</title><style>body{font-family:system-ui;margin:0;background:#050b14;color:#eaf6ff;display:flex;min-height:100vh;align-items:center;justify-content:center}main{width:min(92%,520px);text-align:center}input,button{font-size:18px;padding:14px;border-radius:12px;border:1px solid #31506b}input{width:calc(100% - 30px);background:#0c1724;color:white}button{margin-top:12px;background:#12304a;color:white;width:100%}#r{margin-top:20px;min-height:28px}</style></head><body><main><h1>J.A.R.V.I.S.</h1><p>Server temporaneo online</p><input id="q" placeholder="Scrivi un comando..." autofocus><button onclick="invia()">Invia a Jarvis</button><div id="r"></div></main><script>async function invia(){let q=document.getElementById('q').value.trim();if(!q)return;let r=await fetch('/api/comando',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({comando:q})});let d=await r.json();document.getElementById('r').textContent=d.risposta||d.errore||'Nessuna risposta';}</script></body></html>'''
                    self._rispondi(200, html, "text/html; charset=utf-8")
                    return
                self._rispondi(404, json.dumps({"errore": "Risorsa non trovata"}))

            def do_POST(self):
                if self.path != "/api/comando":
                    self._rispondi(404, json.dumps({"errore": "Endpoint non trovato"}))
                    return
                try:
                    lunghezza = int(self.headers.get("Content-Length", "0"))
                    dati = json.loads(self.rfile.read(lunghezza).decode("utf-8"))
                    comando = str(dati.get("comando", "")).strip()
                    if not comando:
                        raise ValueError("Comando vuoto")
                    risposta = callback(comando) if callback else "Server online: nessun gestore comandi collegato."
                    self._rispondi(200, json.dumps({"risposta": str(risposta)}, ensure_ascii=False))
                except Exception as exc:
                    self._rispondi(400, json.dumps({"errore": str(exc)}, ensure_ascii=False))

            def log_message(self, fmt, *args):
                if logger and hasattr(logger, "info"):
                    logger.info("Server telefono: " + (fmt % args))

        self.server = ThreadingHTTPServer((self.host, self.porta), Handler)
        self.porta = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True, name="JarvisPhoneServer")
        self.thread.start()
        return self.indirizzo()

    def ferma(self):
        if self.server is None:
            return "Server temporaneo non attivo."
        self.server.shutdown()
        self.server.server_close()
        self.server = None
        self.thread = None
        return "Server temporaneo Jarvis fermato."

    def indirizzo(self):
        if self.server is None:
            return None
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "IP_DEL_MAC"
        if ip.startswith("127."):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    ip = s.getsockname()[0]
            except Exception:
                ip = "IP_DEL_MAC"
        return f"http://{ip}:{self.porta}"

    def stato(self):
        return {"attivo": self.server is not None, "indirizzo": self.indirizzo(), "porta": self.porta}
