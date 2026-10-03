"""
Nucleo principale compatibile del pacchetto Jarvis.

Adattamento di jarvis/core.py alla struttura reale della repository.

Il progetto Jarvis possiede già KernelJarvis come orchestratore centrale;
questa classe JARVIS fornisce quindi una facciata semplice e compatibile con
l'API del Voice Pack, delegando le funzionalità al Kernel invece di creare
un secondo sistema parallelo di memoria, voce e moduli.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, Optional

from core.kernel import KernelJarvis


class JARVIS:
    """
    Facciata principale per utilizzare Jarvis tramite un'API semplice.

    Esempio:
        jarvis = JARVIS(name="Jarvis")
        jarvis.start_conversation()
    """

    def __init__(
        self,
        name: str = "JARVIS",
        language: str = "it_IT",
        voice_speed: float = 0.9,
        voice_pitch: float = 0.8,
        enable_memory: bool = True,
        config_file: Optional[str] = None,
        kernel: Optional[KernelJarvis] = None,
    ):
        self.name = str(name or "JARVIS")
        self.language = str(language or "it_IT")
        self.voice_speed = float(voice_speed)
        self.voice_pitch = float(voice_pitch)
        self.enable_memory = bool(enable_memory)

        self.config = self._load_config(config_file)
        self.kernel = kernel or KernelJarvis()

        # Mantiene il nome richiesto dal chiamante anche quando il Kernel
        # utilizza la configurazione globale della repository.
        try:
            if self.name:
                self.kernel.nome = self.name
        except Exception:
            pass

        self.custom_commands: Dict[str, Callable[..., Any]] = {}
        self.is_listening = False
        self.is_running = False

        # Riferimenti compatibili con l'API del Voice Pack.
        self.stt = getattr(self.kernel.modulo_voce, "ascoltatore", None)
        self.tts = getattr(self.kernel.modulo_voce, "sintesi", None)
        self.ai = getattr(self.kernel, "intelligenza", None)
        self.memory = getattr(self.kernel, "memoria", None) if self.enable_memory else None

        print(f"🤖 {self.name} inizializzato")

    def start(self) -> bool:
        """Avvia il Kernel Jarvis."""
        risultato = self.kernel.avvia()
        self.is_running = bool(risultato)
        return bool(risultato)

    def stop(self) -> bool:
        """Arresta il Kernel Jarvis."""
        risultato = self.kernel.arresta()
        self.is_running = False
        self.is_listening = False
        return bool(risultato)

    def listen(self) -> Optional[str]:
        """
        Acquisisce un comando vocale usando il modulo voce già presente.

        Se il modulo vocale non espone un metodo compatibile, restituisce None
        senza interrompere il processo principale.
        """
        self.is_listening = True
        try:
            voce = self.kernel.modulo_voce

            for nome_metodo in ("ascolta", "ascolta_una_volta", "riconosci"):
                metodo = getattr(voce, nome_metodo, None)
                if callable(metodo):
                    testo = metodo()
                    testo = str(testo).strip() if testo else None
                    if testo:
                        print(f"👤 Tu: {testo}")
                    return testo

            return None
        except Exception as errore:
            print(f"❌ Errore ascolto: {errore}")
            return None
        finally:
            self.is_listening = False

    def process(self, text: str) -> str:
        """
        Elabora un testo tramite i comandi registrati o il cervello di Jarvis.
        """
        testo = str(text or "").strip()
        if not testo:
            return ""

        for command, handler in self.custom_commands.items():
            if command in testo.casefold():
                try:
                    return str(handler())
                except TypeError:
                    try:
                        return str(handler(testo))
                    except Exception as errore:
                        return f"Errore nell'esecuzione del comando: {errore}"
                except Exception as errore:
                    return f"Errore nell'esecuzione del comando: {errore}"

        try:
            risposta = self.kernel.parla(testo)
            return str(risposta) if risposta is not None else ""
        except Exception as errore:
            print(f"❌ Errore elaborazione: {errore}")
            return "Si è verificato un errore durante l'elaborazione della richiesta."

    def speak(self, text: str) -> None:
        """Pronuncia un testo tramite il modulo voce del Kernel."""
        testo = str(text or "").strip()
        if not testo:
            return

        print(f"🤖 {self.name}: {testo}")
        try:
            voce = self.kernel.modulo_voce

            for nome_metodo in ("parla", "sintetizza", "pronuncia"):
                metodo = getattr(voce, nome_metodo, None)
                if callable(metodo):
                    metodo(testo)
                    return
        except Exception as errore:
            print(f"❌ Errore sintesi vocale: {errore}")

    def listen_and_respond(self) -> Optional[str]:
        """Ascolta una richiesta, la elabora e restituisce la risposta."""
        testo = self.listen()
        if not testo:
            return None

        risposta = self.process(testo)
        if risposta:
            self.speak(risposta)
        return risposta

    def start_conversation(self) -> None:
        """
        Avvia la modalità conversazione continua.

        L'arresto manuale è possibile con Ctrl+C.
        """
        self.start()
        self.is_running = True

        try:
            self.speak(f"Salve, {self.name}. Come posso assisterla?")
            while self.is_running and not getattr(self.kernel, "arresto_richiesto", False):
                self.listen_and_respond()
        except KeyboardInterrupt:
            self.speak("Arrivederci, Sir.")
        finally:
            self.is_running = False
            self.stop()

    def on_command(self, command: str) -> Callable:
        """Decoratore per registrare un comando personalizzato."""
        nome = str(command or "").strip().casefold()

        def decorator(func: Callable) -> Callable:
            if nome:
                self.custom_commands[nome] = func
            return func

        return decorator

    def add_command(self, command: str, handler: Callable) -> None:
        """Registra manualmente un comando personalizzato."""
        nome = str(command or "").strip().casefold()
        if nome and callable(handler):
            self.custom_commands[nome] = handler

    def get_memory(self) -> Optional[Dict[str, Any]]:
        """Restituisce lo stato della memoria persistente disponibile."""
        if not self.enable_memory or self.memory is None:
            return None

        try:
            return self.memory.stato()
        except Exception:
            return None

    def clear_memory(self) -> None:
        """Cancella la memoria disponibile tramite il Kernel."""
        if not self.enable_memory or self.memory is None:
            return

        for nome_metodo in ("svuota", "cancella", "clear"):
            metodo = getattr(self.memory, nome_metodo, None)
            if callable(metodo):
                try:
                    metodo()
                    print("🧠 Memoria cancellata")
                    return
                except Exception as errore:
                    print(f"⚠️ Errore cancellazione memoria: {errore}")
                    return

    def status(self) -> Dict[str, Any]:
        """Restituisce lo stato completo del Kernel."""
        try:
            return self.kernel.stato_sistema()
        except Exception:
            return {
                "nome": self.name,
                "lingua": self.language,
                "in_esecuzione": self.is_running,
                "in_ascolto": self.is_listening,
            }

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Carica un JSON opzionale senza rendere obbligativo il file."""
        configurazione: Dict[str, Any] = {
            "name": self.name,
            "language": self.language,
            "voice_speed": self.voice_speed,
            "voice_pitch": self.voice_pitch,
            "enable_memory": self.enable_memory,
        }

        if not config_file:
            return configurazione

        percorso = os.path.abspath(os.path.expanduser(str(config_file)))
        if not os.path.isfile(percorso):
            return configurazione

        try:
            with open(percorso, "r", encoding="utf-8") as file:
                dati = json.load(file)
            if isinstance(dati, dict):
                configurazione.update(dati)
        except (OSError, ValueError, TypeError) as errore:
            print(f"⚠️ Errore caricamento configurazione: {errore}")

        return configurazione


__all__ = ["JARVIS"]
