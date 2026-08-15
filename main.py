import sys
import signal
import traceback

from core.kernel import KernelJarvis


kernel = None


def chiusura(signum=None, frame=None):
    global kernel

    print("\n")

    print("Arresto Jarvis...")

    try:
        if kernel:
            kernel.arresta()
    except Exception as errore:
        print(f"Errore durante l'arresto: {errore}")

    sys.exit(0)


def main():

    global kernel

    print("=" * 60)
    print("           JARVIS 3.0")
    print(" Assistente Intelligente Personale")
    print("=" * 60)
    print()

    try:

        kernel = KernelJarvis()

        kernel.avvia()

        print()
        print("Jarvis è operativo.")
        print("Pronuncia la wake word: Jarvis")
        print("Premi CTRL+C per uscire.")
        print()

        signal.signal(signal.SIGINT, chiusura)
        signal.signal(signal.SIGTERM, chiusura)

        while True:
            signal.pause()

    except KeyboardInterrupt:
        chiusura()

    except Exception:

        traceback.print_exc()

        chiusura()


if __name__ == "__main__":
    main()
