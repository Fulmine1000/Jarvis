import threading
import time


class MotoreAscolto:
    """
    Motore di ascolto vocale di Jarvis.

    Gestisce:
    - ascolto dal microfono;
    - riconoscimento vocale;
    - wake word;
    - esecuzione dei comandi;
    - avvio e arresto del motore.

    La risposta vocale dei comandi viene gestita
    direttamente da KernelJarvis.esegui_comando().

    Il motore NON richiama rispondi() dopo
    l'esecuzione del comando, evitando il doppio parlato.
    """

    def __init__(self, modulo_voce):
        self.modulo_voce = modulo_voce

        self.attivo = False
        self.thread = None

        self.ascoltatore = getattr(
            modulo_voce,
            "ascoltatore",
            None
        )

        self.riconoscitore = getattr(
            modulo_voce,
            "riconoscitore",
            None
        )

        self.wake_word = getattr(
            modulo_voce,
            "wake_word",
            None
        )

    def avvia(self):
        """Avvia il motore di ascolto."""

        if self.attivo:
            return True

        self.attivo = True

        self.thread = threading.Thread(
            target=self.ciclo,
            name="Jarvis-MotoreAscolto",
            daemon=True
        )

        self.thread.start()

        self.log(
            "Motore ascolto Jarvis avviato."
        )

        return True

    def ferma(self):
        """Arresta il motore di ascolto."""

        self.attivo = False

        if self.ascoltatore is not None:
            try:
                metodo = getattr(
                    self.ascoltatore,
                    "ferma",
                    None
                )

                if callable(metodo):
                    metodo()

            except Exception as errore:
                self.log(
                    f"Errore arresto ascoltatore: {errore}"
                )

        if self.thread is not None:
            try:
                if self.thread.is_alive():
                    self.thread.join(
                        timeout=2
                    )

            except Exception as errore:
                self.log(
                    f"Errore arresto thread ascolto: {errore}"
                )

        self.thread = None

        self.log(
            "Motore ascolto fermato."
        )

    def ciclo(self):
        """Ciclo principale di ascolto."""

        while self.attivo:

            try:
                if self.ascoltatore is None:
                    time.sleep(0.1)
                    continue

                if self.riconoscitore is None:
                    time.sleep(0.1)
                    continue

                audio = self.ascoltatore.ascolta()

                if not audio:
                    time.sleep(0.05)
                    continue

                testo = self.riconoscitore.riconosci(
                    audio
                )

                if not testo:
                    continue

                testo = str(
                    testo
                ).strip()

                if not testo:
                    continue

                self.log(
                    f"Testo riconosciuto: {testo}"
                )

                if self.wake_word is None:
                    continue

                risultato = self.wake_word.controlla(
                    testo
                )

                if risultato is None:
                    continue

                if isinstance(
                    risultato,
                    str
                ):
                    comando = risultato.strip()

                elif isinstance(
                    risultato,
                    tuple
                ):

                    if len(risultato) < 2:
                        continue

                    attivato = risultato[0]
                    comando = risultato[1]

                    if not attivato:
                        continue

                    comando = str(
                        comando or ""
                    ).strip()

                elif isinstance(
                    risultato,
                    dict
                ):

                    if not risultato.get(
                        "attivo",
                        False
                    ):
                        continue

                    comando = str(
                        risultato.get(
                            "comando",
                            ""
                        )
                    ).strip()

                else:
                    continue

                # -------------------------------------------------
                # WAKE WORD SENZA COMANDO
                # -------------------------------------------------
                #
                # Esempio:
                #
                # "Jarvis"
                #
                # Jarvis risponde "Sono qui."
                # e rimane pronto per il comando successivo.
                #
                # Questa risposta viene effettuata UNA SOLA VOLTA.
                #

                if not comando:

                    self.modulo_voce.rispondi(
                        "Sono qui."
                    )

                    continue

                self.log(
                    f"Comando ricevuto: {comando}"
                )

                kernel = getattr(
                    self.modulo_voce,
                    "kernel",
                    None
                )

                if kernel is None:
                    self.log(
                        "Kernel non disponibile."
                    )
                    continue

                # -------------------------------------------------
                # ESECUZIONE COMANDO
                # -------------------------------------------------
                #
                # IMPORTANTE:
                #
                # KernelJarvis.esegui_comando()
                # esegue il comando E pronuncia già
                # la risposta tramite kernel.parla().
                #
                # NON chiamare:
                #
                # self.modulo_voce.rispondi(...)
                #
                # qui sotto.
                #
                # Altrimenti Jarvis parlerebbe due volte.
                #

                kernel.esegui_comando(
                    comando
                )

                # -------------------------------------------------
                # DISATTIVAZIONE WAKE WORD
                # -------------------------------------------------

                try:
                    self.wake_word.disattiva()

                except Exception:
                    pass

            except Exception as errore:

                self.log(
                    f"Errore motore ascolto: {errore}"
                )

                time.sleep(0.2)

    def log(self, messaggio):
        """Invia un messaggio al logger di Jarvis."""

        try:
            logger = getattr(
                self.modulo_voce,
                "logger",
                None
            )

            if logger is not None:

                metodo = getattr(
                    logger,
                    "info",
                    None
                )

                if callable(metodo):
                    metodo(
                        messaggio
                    )
                    return

        except Exception:
            pass

        print(
            messaggio
        )
