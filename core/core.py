"""
Facciata pubblica di Jarvis compatibile con il Voice Pack italiano.

La repository possiede già KernelJarvis come orchestratore centrale. Questa
classe non crea un secondo Jarvis: collega l'API del Voice Pack ai moduli reali
del progetto, mantenendo separati ascolto, comandi, intelligenza, memoria e
sintesi vocale.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, Optional

from core.kernel import KernelJarvis
from intelligenza.conversazione import ConversationEngine
from memoria.memory import Memory


class JARVIS:
    """Facciata semplice per usare il Jarvis reale della repository."""

    RISPOSTA_COMANDO_SCONOSCIUTO = "Non ho trovato un comando compatibile."

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

        try:
            self.kernel.nome = self.name
        except Exception:
            pass

        self.custom_commands: Dict[str, Callable[..., Any]] = {}
        self.conversation = ConversationEngine(language=self.language)
        self.conversation_memory = Memory() if self.enable_memory else None

        self.is_listening = False
        self.is_running = False

        # Riferimenti compatibili con l'API del Voice Pack.
        self.stt = getattr(self.kernel.modulo_voce, "ascoltatore", None)
        self.tts = getattr(self.kernel.modulo_voce, "sintesi", None)
        self.ai = getattr(self.kernel, "intelligenza", None)
        self.memory = (
            getattr(self.kernel, "memoria", None)
            if self.enable_memory
            else None
        )

        print(f"🤖 {self.name} inizializzato")

    def start(self) -> bool:
        """Avvia il Kernel Jarvis reale."""
        risultato = self.kernel.avvia()
        self.is_running = bool(risultato)
        return self.is_running

    def stop(self) -> bool:
        """Arresta il Kernel Jarvis reale."""
        risultato = self.kernel.arresta()
        self.is_running = False
        self.is_listening = False
        return bool(risultato)

    def listen(self) -> Optional[str]:
        """Legge un comando dal ModuloVoce già presente nel progetto."""
        self.is_listening = True
        try:
            voce = self.kernel.modulo_voce
            metodo = getattr(voce, "ascolta_comando", None)
            if not callable(metodo):
                return None

            testo = metodo()
            testo = str(testo).strip() if testo else None
            if testo:
                print(f"👤 Tu: {testo}")
            return testo
        except Exception as errore:
            print(f"❌ Errore ascolto: {errore}")
            return None
        finally:
            self.is_listening = False

    def process(self, text: str) -> str:
        """
        Elabora una richiesta attraverso la pipeline reale di Jarvis.

        Ordine:
        1. comandi personalizzati della facciata;
        2. gestore comandi ufficiale;
        3. CervelloJarvis/LLM;
        4. ConversationEngine locale come fallback.
        """
        testo = " ".join(str(text or "").strip().split())
        if not testo:
            return ""

        if self.conversation_memory is not None:
            self.conversation_memory.add_user_input(testo)

        # 1. Comandi registrati tramite l'API del Voice Pack.
        testo_lower = testo.casefold()
        for command, handler in self.custom_commands.items():
            if command in testo_lower:
                try:
                    risposta = handler()
                except TypeError:
                    try:
                        risposta = handler(testo)
                    except Exception as errore:
                        risposta = f"Errore nell'esecuzione del comando: {errore}"
                except Exception as errore:
                    risposta = f"Errore nell'esecuzione del comando: {errore}"

                return self._registra_risposta(str(risposta))

        # 2. Comandi operativi reali, senza farli pronunciare due volte.
        try:
            gestore = getattr(self.kernel, "modulo_comandi", None)
            metodo_comando = getattr(gestore, "esegui", None)
            if callable(metodo_comando):
                risposta = metodo_comando(testo)
                if risposta and risposta != self.RISPOSTA_COMANDO_SCONOSCIUTO:
                    return self._registra_risposta(str(risposta))
        except Exception as errore:
            if getattr(self.kernel, "logger", None):
                self.kernel.logger.debug(
                    f"Gestore comandi non disponibile nella facciata: {errore}"
                )

        # 3. Cervello/LLM del Jarvis reale.
        try:
            cervello = getattr(self.kernel, "intelligenza", None)
            metodo_ai = getattr(cervello, "rispondi", None)
            if callable(metodo_ai):
                risposta = metodo_ai(testo)
                if risposta:
                    return self._registra_risposta(str(risposta))
        except Exception as errore:
            if getattr(self.kernel, "logger", None):
                self.kernel.logger.debug(
                    f"Cervello non disponibile nella facciata: {errore}"
                )

        # 4. Fallback completamente locale del Voice Pack.
        try:
            contesto = (
                self.conversation_memory.get_context()
                if self.conversation_memory is not None
                else None
            )
            risposta = self.conversation.generate_response(testo, contesto)
            return self._registra_risposta(str(risposta))
        except Exception as errore:
            print(f"❌ Errore elaborazione: {errore}")
            return "Si è verificato un errore durante l'elaborazione della richiesta."

    def speak(self, text: str) -> bool:
        """Pronuncia il testo attraverso il ModuloVoce ufficiale."""
        testo = str(text or "").strip()
        if not testo:
            return False

        print(f"🤖 {self.name}: {testo}")

        try:
            voce = self.kernel.modulo_voce
            metodo = getattr(voce, "rispondi", None)
            if callable(metodo):
                return bool(metodo(testo))
        except Exception as errore:
            print(f"❌ Errore sintesi vocale: {errore}")

        return False

    def listen_and_respond(self) -> Optional[str]:
        """Ascolta, elabora e pronuncia una risposta."""
        testo = self.listen()
        if not testo:
            return None

        risposta = self.process(testo)
        if risposta:
            self.speak(risposta)
        return risposta

    def start_conversation(self) -> None:
        """Avvia una conversazione continua usando i moduli reali."""
        if not self.start():
            return

        try:
            self.speak("Salve, Sir. Tutti i sistemi sono pronti. Come posso assisterla?")
            while self.is_running and not getattr(
                self.kernel, "arresto_richiesto", False
            ):
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
        """Restituisce memoria persistente e memoria conversazionale."""
        if not self.enable_memory:
            return None

        risultato: Dict[str, Any] = {}

        try:
            if self.memory is not None:
                risultato["persistent"] = self.memory.stato()
        except Exception:
            pass

        if self.conversation_memory is not None:
            stato = self.conversation_memory.stato()
            risultato["history"] = self.conversation_memory.get_history(None)
            risultato["profile"] = self.conversation_memory.get_profile()
            risultato["context"] = self.conversation_memory.get_context()
            risultato["state"] = stato

        return risultato

    def clear_memory(self) -> None:
        """Cancella la memoria temporanea della facciata senza distruggere i ricordi persistenti."""
        if not self.enable_memory:
            return

        if self.conversation_memory is not None:
            self.conversation_memory.clear()

        print("🧠 Memoria conversazionale temporanea cancellata")

    def status(self) -> Dict[str, Any]:
        """Restituisce lo stato completo del Kernel."""
        try:
            stato = self.kernel.stato_sistema()
            stato["facciata_voice_pack"] = {
                "attiva": True,
                "lingua": self.language,
                "memoria_conversazionale": self.conversation_memory is not None,
            }
            return stato
        except Exception:
            return {
                "nome": self.name,
                "lingua": self.language,
                "in_esecuzione": self.is_running,
                "in_ascolto": self.is_listening,
            }

    def _registra_risposta(self, risposta: str) -> str:
        testo = str(risposta or "").strip()
        if self.conversation_memory is not None and testo:
            self.conversation_memory.add_response(testo)
        return testo

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Carica un JSON opzionale senza rendere obbligatorio il file."""
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
