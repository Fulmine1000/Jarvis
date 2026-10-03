"""Esempio avanzato di Jarvis con comandi custom.

Adattamento di jarvis-italiano-main/examples/advanced.py alla struttura
reale della repository Jarvis.
"""

from __future__ import annotations

import random

from core.core import JARVIS


# Inizializza Jarvis.
jarvis = JARVIS(
    name="Jarvis",
    language="it_IT",
    enable_memory=True,
)


# Registra comandi custom con il decoratore.
@jarvis.on_command("accendi le luci")
def turn_on_lights() -> str:
    return "Le luci del soggiorno sono accese"


@jarvis.on_command("spegni le luci")
def turn_off_lights() -> str:
    return "Le luci sono spente"


@jarvis.on_command("temperatura")
def get_temperature() -> str:
    temp = random.randint(18, 25)
    return f"La temperatura attuale è {temp} gradi Celsius"


@jarvis.on_command("ricordami")
def remember_something() -> str:
    return "Certo, ti farò sapere quando sarà il momento"


def main() -> None:
    """Avvia la modalità di conversazione continua."""
    print("\n🤖 Jarvis Avanzato - Con comandi smart home\n")
    print("Comandi disponibili:")
    print("  - 'Accendi le luci'")
    print("  - 'Spegni le luci'")
    print("  - 'Temperatura'")
    print("  - 'Ricordami...'")
    print("\nPremi Ctrl+C per uscire\n")

    try:
        jarvis.start_conversation()
    except KeyboardInterrupt:
        memory = jarvis.get_memory()
        if isinstance(memory, dict):
            history = memory.get("history", [])
            print(f"\n📝 Cronologia: {len(history)} turni")
        else:
            print("\n📝 Cronologia: memoria non disponibile.")
        print("Arrivederci, Sir.")


if __name__ == "__main__":
    main()
