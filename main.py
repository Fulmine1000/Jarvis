"""Punto di ingresso compatibile di J.A.R.V.I.S.

L'implementazione ufficiale del launcher è in ``jarvis.py``.
Questo file resta per compatibilità con gli avvii precedenti.
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
