from __future__ import annotations

import json
import os
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request


class DialogoJarvis:
    """Motore conversazionale IA di J.A.R.V.I.S.

    Backend principale: llama.cpp locale. Ollama e API compatibili restano
    disponibili come alternative esplicite. Nessuna chiave privata viene
    salvata nella repository.
    """

    BASE_JARVIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FILE_STORIA = os.path.join(BASE_JARVIS, "memoria", "conversazioni.json")
    MASSIMO_STORIA = 12

    def __init__(self, logger=None):
        self.logger = logger
        self.provider_richiesto = os.getenv("JARVIS_AI_PROVIDER", "llama").strip().lower()
        self.provider = self.provider_richiesto
        self.endpoint = os.getenv(
            "JARVIS_OLLAMA_URL", "http://127.0.0.1:11434/api/chat"
        ).strip()
        self.endpoint_llama = os.getenv(
            "JARVIS_LLAMA_URL",
            "http://127.0.0.1:8080/v1/chat/completions",
        ).strip()
        self.endpoint_compatibile = os.getenv("JARVIS_AI_URL", "").strip()
        self.modello = os.getenv(
            "JARVIS_AI_MODEL",
            os.getenv("JARVIS_OLLAMA_MODEL", "qwen2.5:3b"),
        ).strip()
        self.modello_llama = os.getenv(
            "JARVIS_LLAMA_MODEL",
            "qwen2.5-3b-instruct-q4_0.gguf",
        ).strip()
        self.api_key = os.getenv("JARVIS_AI_API_KEY", "").strip()
        self.timeout = self._intero_env("JARVIS_AI_TIMEOUT", 60, 5, 180)
        self.llama_threads = self._intero_env("JARVIS_LLAMA_THREADS", 4, 1, 4)
        self.llama_context = self._intero_env("JARVIS_LLAMA_CONTEXT", 512, 512, 4096)
        self.llama_max_tokens = self._intero_env("JARVIS_LLAMA_MAX_TOKENS", 48, 16, 96)
        self.attivo = True
        self.storia = []
        self.ultima_errore = None
        self.ultimo_backend = None
        self._server_llama = None
        self._server_avvio_thread = None
        self._server_avvio_lock = threading.Lock()
        self._conversazione_locale = None

        try:
            from intelligenza.conversazione import ConversationEngine
            self._conversazione_locale = ConversationEngine(language="it_IT")
        except Exception:
            pass

        self.istruzioni = (
            "Sei Jarvis, assistente personale in italiano. "
            "Rispondi solo alla domanda dell'utente, in modo corretto, chiaro e breve. "
            "Non aggiungere data, ora, saluti o informazioni non richieste. "
            "Non inventare: se non sei sicuro, dillo. "
            "Per domande fattuali, usa definizioni affidabili e non fare supposizioni. ""Dai prima la risposta corretta e poi una breve spiegazione. "
            "Usa 'Sir' solo quando ti rivolgi direttamente all'utente."
        )
        self._carica_storia()

        # Precarica il server IA in background: il primo comando non deve
        # aspettare anche il caricamento del modello da circa 2 GB.
        if self.provider_richiesto in {"llama", "llama_cpp", "llama.cpp"}:
            self._prepara_llama_background()

    @staticmethod
    def _intero_env(nome, predefinito, minimo, massimo):
        try:
            valore = int(os.getenv(nome, str(predefinito)))
            return max(minimo, min(massimo, valore))
        except (TypeError, ValueError):
            return predefinito

    def _carica_storia(self):
        try:
            if not os.path.exists(self.FILE_STORIA):
                return
            with open(self.FILE_STORIA, "r", encoding="utf-8") as file:
                dati = json.load(file)
            if isinstance(dati, list):
                storia = []
                for messaggio in dati[-self.MASSIMO_STORIA:]:
                    if (
                        isinstance(messaggio, dict)
                        and messaggio.get("role") in {"user", "assistant"}
                        and isinstance(messaggio.get("content"), str)
                    ):
                        storia.append({
                            "role": messaggio["role"],
                            "content": messaggio["content"],
                        })
                self.storia = storia
        except (OSError, ValueError, TypeError):
            self.storia = []

    def _salva_storia(self):
        try:
            cartella = os.path.dirname(os.path.abspath(self.FILE_STORIA))
            os.makedirs(cartella, exist_ok=True)
            fd, temporaneo = tempfile.mkstemp(
                prefix=".jarvis_dialogo_", suffix=".json", dir=cartella
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as file:
                    json.dump(
                        self.storia[-self.MASSIMO_STORIA:],
                        file,
                        indent=2,
                        ensure_ascii=False,
                    )
                    file.flush()
                    os.fsync(file.fileno())
                os.replace(temporaneo, self.FILE_STORIA)
            except Exception:
                try:
                    os.remove(temporaneo)
                except OSError:
                    pass
        except OSError as errore:
            self._log_debug(f"Memoria conversazionale non salvata: {errore}")

    def _log_debug(self, messaggio):
        if self.logger and hasattr(self.logger, "debug"):
            self.logger.debug(messaggio)

    def _messaggi(self, testo):
        # Ogni domanda vocale viene inviata come richiesta autonoma. La
        # cronologia persistente non viene inserita automaticamente nel
        # prompt, evitando contaminazioni e lavoro inutile sul CPU.
        return [
            {"role": "system", "content": self.istruzioni},
            {"role": "user", "content": testo},
        ]

    @staticmethod
    def _raggiungibile(endpoint, timeout=0.5):
        try:
            parsed = urllib.parse.urlparse(endpoint)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            if not host:
                return False
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, ValueError):
            return False

    @staticmethod
    def _richiesta_json(payload, endpoint, headers=None, timeout=90):
        intestazioni = {"Content-Type": "application/json"}
        if headers:
            intestazioni.update(headers)
        richiesta = urllib.request.Request(
            endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=intestazioni,
            method="POST",
        )
        with urllib.request.urlopen(richiesta, timeout=timeout) as risposta:
            return json.loads(risposta.read().decode("utf-8"))

    def _rispondi_ollama(self, messaggi):
        dati = self._richiesta_json(
            {
                "model": self.modello,
                "messages": messaggi,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "repeat_penalty": 1.05,
                    "num_ctx": self.llama_context,
                    "num_predict": self.llama_max_tokens,
                },
            },
            self.endpoint,
            timeout=self.timeout,
        )
        return (dati.get("message") or {}).get("content", "").strip()

    def _rispondi_compatibile(self, messaggi, endpoint, modello):
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        dati = self._richiesta_json(
            {
                "model": modello,
                "messages": messaggi,
                "temperature": 0.1,
                "top_p": 0.9,
                "repeat_penalty": 1.05,
                "stream": False,
                "max_tokens": self.llama_max_tokens,
            },
            endpoint,
            headers,
            timeout=self.timeout,
        )
        scelte = dati.get("choices") or []
        if not scelte:
            return ""
        return ((scelte[0].get("message") or {}).get("content") or "").strip()

    def _trova_llama(self):
        binario = os.getenv(
            "JARVIS_LLAMA_SERVER_BIN",
            os.path.join(self.BASE_JARVIS, "motore_ia", "bin", "llama-server"),
        ).strip()
        modello = os.getenv(
            "JARVIS_LLAMA_MODEL_PATH",
            os.path.join(
                self.BASE_JARVIS,
                "motore_ia",
                "modelli",
                self.modello_llama,
            ),
        ).strip()
        return (
            binario if os.path.isfile(binario) and os.access(binario, os.X_OK) else None,
            modello if os.path.isfile(modello) else None,
        )

    def _prepara_llama_background(self):
        """Prepara il server llama.cpp durante l'avvio di Jarvis."""
        if self._raggiungibile(self.endpoint_llama):
            return
        if self._server_avvio_thread and self._server_avvio_thread.is_alive():
            return

        def avvia():
            try:
                self._avvia_llama_server()
            except Exception as errore:
                self._log_debug(f"Avvio IA in background non riuscito: {errore}")

        self._server_avvio_thread = threading.Thread(
            target=avvia,
            name="JarvisLlamaPreload",
            daemon=True,
        )
        self._server_avvio_thread.start()

    def _avvia_llama_server(self):
        # Il precaricamento avviene in background. Un lock evita che la prima
        # domanda avvii un secondo llama-server mentre il primo sta caricando
        # il modello.
        with self._server_avvio_lock:
            if self._raggiungibile(self.endpoint_llama):
                return True

            binario, modello = self._trova_llama()
            if not binario or not modello:
                return False

            parsed = urllib.parse.urlparse(self.endpoint_llama)
            host = parsed.hostname or "127.0.0.1"
            porta = str(parsed.port or 8080)

            try:
                self._server_llama = subprocess.Popen(
                    [
                        binario,
                        "-m",
                        modello,
                        "--host",
                        host,
                        "--port",
                        porta,
                        "-c",
                        str(self.llama_context),
                        "-ngl",
                        "0",
                        "-t",
                        str(self.llama_threads),
                    ],
                    cwd=os.path.dirname(binario),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                limite = time.time() + min(self.timeout, 30)
                while time.time() < limite:
                    if self._raggiungibile(self.endpoint_llama):
                        return True
                    if self._server_llama.poll() is not None:
                        break
                    time.sleep(0.25)
            except (OSError, ValueError):
                self._server_llama = None

            return self._raggiungibile(self.endpoint_llama)

    def _backend_disponibili(self):
        richiesto = self.provider_richiesto

        if richiesto in {"ollama", "ollama_local"}:
            return ["ollama"]
        if richiesto in {"llama", "llama_cpp", "llama.cpp"}:
            return ["llama"]
        if richiesto in {"openai", "openai_compatible", "compatibile"}:
            return ["compatibile"]
        if richiesto in {"locale", "local", "fallback"}:
            return []

        candidati = []
        binario, modello = self._trova_llama()
        if self._raggiungibile(self.endpoint_llama) or (binario and modello):
            candidati.append("llama")
        if self._raggiungibile(self.endpoint):
            candidati.append("ollama")
        if self.endpoint_compatibile and self._raggiungibile(self.endpoint_compatibile):
            candidati.append("compatibile")
        return candidati

    def _risposta_locale(self, testo):
        if not self._conversazione_locale:
            return None
        try:
            return self._conversazione_locale.generate_response(
                testo, context={"memoria": self.storia[-6:]}
            )
        except Exception:
            return None

    def rispondi(self, testo):
        testo = (testo or "").strip()
        if not testo or not self.attivo:
            return None

        messaggi = self._messaggi(testo)
        self.ultima_errore = None
        self.ultimo_backend = None

        for backend in self._backend_disponibili():
            try:
                if backend == "ollama":
                    risposta = self._rispondi_ollama(messaggi)
                elif backend == "llama":
                    if not self._avvia_llama_server():
                        continue
                    risposta = self._rispondi_compatibile(
                        messaggi, self.endpoint_llama, self.modello_llama
                    )
                else:
                    risposta = self._rispondi_compatibile(
                        messaggi, self.endpoint_compatibile, self.modello
                    )

                if risposta:
                    self.ultimo_backend = backend
                    self.storia.extend([
                        {"role": "user", "content": testo},
                        {"role": "assistant", "content": risposta},
                    ])
                    self.storia = self.storia[-self.MASSIMO_STORIA:]
                    self._salva_storia()
                    return risposta
            except (
                urllib.error.URLError,
                urllib.error.HTTPError,
                TimeoutError,
                OSError,
                ValueError,
                json.JSONDecodeError,
            ) as errore:
                self.ultima_errore = str(errore)
                continue
            except Exception as errore:
                self.ultima_errore = str(errore)
                self._log_debug(f"Errore backend IA {backend}: {errore}")

        self.provider = "locale"
        risposta = self._risposta_locale(testo)
        if risposta:
            self.ultimo_backend = "conversation-engine"
            self.storia.extend([
                {"role": "user", "content": testo},
                {"role": "assistant", "content": risposta},
            ])
            self.storia = self.storia[-self.MASSIMO_STORIA:]
            self._salva_storia()
            return risposta

        return None

    def ferma(self):
        """Arresta il llama-server avviato da questa istanza di Jarvis."""
        processo = self._server_llama
        self._server_llama = None
        if processo and processo.poll() is None:
            try:
                processo.terminate()
                processo.wait(timeout=2)
            except Exception:
                try:
                    processo.kill()
                except Exception:
                    pass
        return True

    def cancella_storia(self):
        self.storia = []
        try:
            if os.path.exists(self.FILE_STORIA):
                os.remove(self.FILE_STORIA)
        except OSError as errore:
            self._log_debug(f"Impossibile cancellare la storia IA: {errore}")
        return True

    def stato(self):
        if self.ultimo_backend == "ollama":
            motore = "Ollama locale"
        elif self.ultimo_backend == "llama":
            motore = "llama.cpp locale"
        elif self.ultimo_backend == "compatibile":
            motore = "API compatibile"
        elif self.ultimo_backend == "conversation-engine":
            motore = "Conversation Engine locale"
        else:
            motore = "IA automatica (backend non attivo)"

        return {
            "attivo": self.attivo,
            "provider_richiesto": self.provider_richiesto,
            "provider": self.provider,
            "motore": motore,
            "modello": self.modello_llama if self.provider_richiesto in {"llama", "llama_cpp", "llama.cpp"} else self.modello,
            "storia_messaggi": len(self.storia),
            "memoria_conversazionale": True,
            "timeout_secondi": self.timeout,
            "thread_llama": self.llama_threads,
            "contesto_llama": self.llama_context,
            "max_token_llama": self.llama_max_tokens,
            "errore": self.ultima_errore,
            "backend_attivo": self.ultimo_backend,
            "ollama_raggiungibile": self._raggiungibile(self.endpoint),
            "llama_raggiungibile": self._raggiungibile(self.endpoint_llama),
        }
