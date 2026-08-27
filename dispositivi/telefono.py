from __future__ import annotations

import datetime
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dispositivi.identita import IdentitaDispositivo


class TelefonoJarvis:
    """Dispositivo telefono di Jarvis.

    Gestisce connessione, sessione e, quando richiesto, un server web locale
    temporaneo per permettere a un telefono di usare Jarvis senza trasferire
    il Core. Il Core resta sul Mac.
    """

    def __init__(self, nome, modello="Sconosciuto", base=False, logger=None, gestore_comandi=None):
        self.nome = nome
        self.modello = modello
        self.base = base
        self.logger = logger
        self.gestore_comandi = gestore_comandi
        self.identita = IdentitaDispositivo(nome, "base" if base else "telefono")
        self.connesso = False
        self.sessione_attiva = False
        self.principale = False
        self.app_aperte = []
        self.ultima_sincronizzazione = None
        self.batteria = 100
        self.wifi = True
        self.bluetooth = True
        self.server = None
        self.server_thread = None
        self.server_porta = 8765

    def connetti(self):
        self.connesso = True
        if self.logger:
            self.logger.info(f"{self.nome} collegato.")
        return f"{self.nome} collegato."

    def disconnetti(self):
        self.ferma_server()
        self.connesso = False
        self.sessione_attiva = False
        self.principale = False
        return f"{self.nome} scollegato."

    def attiva_sessione(self):
        if self.base:
            return "La base non può essere trasferita."
        if not self.connesso:
            self.connetti()
        self.sessione_attiva = True
        self.principale = True
        return "Jarvis ora è attivo sul telefono."

    def ritorna_alla_base(self):
        self.ferma_server()
        self.sincronizza()
        self.sessione_attiva = False
        self.principale = False
        return "Jarvis è tornato alla base."

    def apri_app(self, app):
        if not self.sessione_attiva:
            return "Telefono non attivo come dispositivo principale."
        if app not in self.app_aperte:
            self.app_aperte.append(app)
        return f"Apertura applicazione: {app}"

    def chiudi_app(self, app):
        if app in self.app_aperte:
            self.app_aperte.remove(app)
            return f"{app} chiusa."
        return "Applicazione non trovata."

    def sincronizza(self):
        self.ultima_sincronizzazione = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return "Sincronizzazione completata."

    def _indirizzo_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "127.0.0.1"

    def avvia_server(self, gestore_comandi=None, porta=8765):
        """Avvia il server web di sessione senza trasferire il Core."""
        if self.server is not None:
            return self.indirizzo_server()
        if self.base:
            return "La base non può essere usata come telefono remoto."

        callback = gestore_comandi or self.gestore_comandi
        self.server_porta = int(porta)
        dispositivo = self

        class Handler(BaseHTTPRequestHandler):
            def risposta(self, codice, corpo, tipo="application/json; charset=utf-8"):
                raw = corpo.encode("utf-8")
                self.send_response(codice)
                self.send_header("Content-Type", tipo)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                if self.path == "/api/stato":
                    self.risposta(200, json.dumps(dispositivo.stato(), ensure_ascii=False))
                    return
                if self.path in ("/", "/index.html"):
                    html = '''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>J.A.R.V.I.S.</title><style>body{margin:0;background:#050b14;color:#eaf6ff;font-family:system-ui;min-height:100vh;display:flex;align-items:center;justify-content:center}main{width:min(92%,520px);text-align:center}input,button{box-sizing:border-box;width:100%;font-size:18px;padding:14px;border-radius:12px;margin-top:10px}input{background:#0b1520;color:#fff;border:1px solid #31506b}button{background:#12304a;color:#fff;border:1px solid #426985}#r{margin-top:20px;min-height:30px}</style></head><body><main><h1>J.A.R.V.I.S.</h1><p>Sessione telefono attiva</p><input id="q" placeholder="Parla con Jarvis..." autofocus><button onclick="invia()">Invia</button><div id="r"></div><script>async function invia(){const q=document.getElementById('q').value.trim();if(!q)return;const r=await fetch('/api/comando',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({comando:q})});const d=await r.json();document.getElementById('r').textContent=d.risposta||d.errore||'Nessuna risposta';}</script></main></body></html>'''
                    self.risposta(200, html, "text/html; charset=utf-8")
                    return
                self.risposta(404, json.dumps({"errore": "Risorsa non trovata"}))

            def do_POST(self):
                if self.path != "/api/comando":
                    self.risposta(404, json.dumps({"errore": "Endpoint non trovato"}))
                    return
                try:
                    lunghezza = int(self.headers.get("Content-Length", "0"))
                    dati = json.loads(self.rfile.read(lunghezza).decode("utf-8"))
                    comando = str(dati.get("comando", "")).strip()
                    if not comando:
                        raise ValueError("Comando vuoto")
                    risposta = callback(comando) if callback else "Server telefono attivo, ma il gestore comandi non è collegato."
                    self.risposta(200, json.dumps({"risposta": str(risposta)}, ensure_ascii=False))
                except Exception as exc:
                    self.risposta(400, json.dumps({"errore": str(exc)}, ensure_ascii=False))

            def log_message(self, fmt, *args):
                if dispositivo.logger and hasattr(dispositivo.logger, "info"):
                    dispositivo.logger.info("Telefono server: " + (fmt % args))

        self.server = ThreadingHTTPServer(("0.0.0.0", self.server_porta), Handler)
        self.server_porta = self.server.server_address[1]
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True, name="JarvisTelefonoServer")
        self.server_thread.start()
        self.sessione_attiva = True
        self.connesso = True
        return self.indirizzo_server()

    def ferma_server(self):
        if self.server is None:
            return "Server telefono non attivo."
        self.server.shutdown()
        self.server.server_close()
        self.server = None
        self.server_thread = None
        return "Server telefono fermato."

    def indirizzo_server(self):
        if self.server is None:
            return None
        return f"http://{self._indirizzo_ip()}:{self.server_porta}"

    def informazioni(self):
        return {"modello": self.modello, "base": self.base, "connesso": self.connesso, "identita": self.identita.informazioni()}

    def stato(self):
        return {
            "nome": self.nome,
            "modello": self.modello,
            "tipo": "base" if self.base else "telefono",
            "connesso": self.connesso,
            "dispositivo_principale": self.principale,
            "sessione": self.sessione_attiva,
            "server_attivo": self.server is not None,
            "indirizzo_server": self.indirizzo_server(),
            "app_aperte": self.app_aperte,
            "batteria": self.batteria,
            "wifi": self.wifi,
            "bluetooth": self.bluetooth,
            "ultima_sincronizzazione": self.ultima_sincronizzazione,
            "identita": self.identita.informazioni()
        }
