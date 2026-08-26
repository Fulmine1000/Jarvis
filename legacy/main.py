"""Punto di ingresso storico mantenuto per compatibilità.

L'implementazione ufficiale è ``jarvis.py`` nella root del progetto.
"""

from jarvis import JarvisOS


def main() -> int:
    jarvis = JarvisOS()
    try:
        jarvis.avvia()
        return 0
    except KeyboardInterrupt:
        jarvis.arresta()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
