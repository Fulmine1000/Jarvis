"""Esempio di integrazione di Jarvis in un progetto esistente.

Adattamento di jarvis-italiano-main/examples/integration.py alla struttura
reale della repository Jarvis.
"""

from __future__ import annotations

import threading
from typing import Optional

from core.core import JARVIS


def main() -> None:
    """Mostra come integrare Jarvis all'interno di un'applicazione."""

    # 1. Inizializza Jarvis all'avvio dell'app.
    jarvis = JARVIS(
        name="Jarvis",
        language="it_IT",
        voice_speed=0.9,
        enable_memory=True,
    )

    # 2. Aggiungi comandi custom per la tua app.
    def handle_database_query() -> str:
        return "Query al database completata con successo"

    jarvis.add_command("cerca nel database", handle_database_query)

    # 3. Usa Jarvis dove ti serve.
    def process_user_request(user_input: str) -> str:
        """Processa una richiesta utente e restituisce la risposta."""
        return jarvis.process(user_input)

    # 4. Ascolta e rispondi in background senza bloccare il programma.
    def listen_in_background() -> threading.Thread:
        """Avvia l'ascolto continuo in un thread daemon."""

        def background_listening() -> None:
            jarvis.start()
            try:
                while jarvis.is_running:
                    if getattr(jarvis.kernel, "arresto_richiesto", False):
                        break
                    jarvis.listen_and_respond()
            finally:
                jarvis.stop()

        thread = threading.Thread(
            target=background_listening,
            name="JarvisBackgroundListener",
            daemon=True,
        )
        thread.start()
        return thread

    print("\n=== Integrazione Jarvis ===\n")

    # Avvia il kernel prima dei test che utilizzano i moduli operativi.
    jarvis.start()

    try:
        # Test processamento diretto.
        user_input = "Ciao, come stai?"
        response = process_user_request(user_input)
        print(f"Input: {user_input}")
        print(f"Response: {response}")

        # Test comando custom.
        user_input = "Cerca nel database"
        response = process_user_request(user_input)
        print(f"Input: {user_input}")
        print(f"Response: {response}")

        # Accesso alla memoria.
        memory = jarvis.get_memory()
        if isinstance(memory, dict):
            history = memory.get("history", [])
            print(f"\nTurni conversazionali: {len(history)}")
        else:
            print("\nMemoria conversazionale non disponibile.")

        # La funzione è definita per mostrare l'integrazione; non viene
        # avviata automaticamente per evitare un thread infinito nell'esempio.
        _ = listen_in_background

        print("\n✅ Integrazione completata!")
    finally:
        jarvis.stop()


if __name__ == "__main__":
    main()
