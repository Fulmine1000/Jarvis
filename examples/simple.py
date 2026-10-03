"""Esempio semplice di utilizzo di Jarvis.

Adattamento di jarvis-italiano-main/examples/simple.py alla struttura reale
della repository Jarvis.
"""

from core.core import JARVIS


def main() -> None:
    """Avvia un ciclo semplice di ascolto e risposta."""
    jarvis = JARVIS(
        name="Jarvis",
        language="it_IT",
        voice_speed=0.9,
        enable_memory=True,
    )

    print("\n🤖 Jarvis - Premi Ctrl+C per uscire\n")

    try:
        jarvis.start()
        while True:
            jarvis.listen_and_respond()
    except KeyboardInterrupt:
        jarvis.speak("Arrivederci, Sir.")
        print("\n👋 Spento.")
    finally:
        try:
            jarvis.stop()
        except Exception:
            pass


if __name__ == "__main__":
    main()
