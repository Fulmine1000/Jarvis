"""Controllo della singola istanza di Jarvis.

Su macOS/Linux usiamo un lock di file POSIX: il lock resta acquisito finché
il processo proprietario è vivo e viene rilasciato automaticamente quando
il processo termina, evitando i problemi dei semplici PID file rimasti
dopo un arresto anomalo.
"""

from __future__ import annotations

import os
import tempfile

try:
    import fcntl
except ImportError:  # pragma: no cover - piattaforme non POSIX
    fcntl = None


class IstanzaUnicaJarvis:
    """Garantisce che esista una sola istanza del processo Jarvis."""

    def __init__(self, nome="jarvis"):
        self.nome = str(nome or "jarvis")
        self.percorso = os.path.join(
            tempfile.gettempdir(),
            f"{self.nome}.instance.lock",
        )
        self._file = None

    def acquisisci(self) -> bool:
        """Acquisisce il lock; False se un'altra istanza è già attiva."""
        if fcntl is None:
            # Jarvis è sviluppato principalmente per macOS; sulle piattaforme
            # prive di fcntl non blocchiamo l'avvio in modo arbitrario.
            return True

        try:
            self._file = open(self.percorso, "a+")
            fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._file.seek(0)
            self._file.truncate()
            self._file.write(str(os.getpid()))
            self._file.flush()
            return True
        except (OSError, IOError):
            self.rilascia()
            return False

    def rilascia(self):
        """Rilascia il lock senza cancellare forzatamente il file."""
        if self._file is None:
            return True

        try:
            if fcntl is not None:
                fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        except (OSError, IOError):
            pass

        try:
            self._file.close()
        except (OSError, IOError):
            pass

        self._file = None
        return True
