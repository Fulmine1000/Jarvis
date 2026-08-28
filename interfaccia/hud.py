"""HUD ufficiale J.A.R.V.I.S. basato su Qt Quick / QML.

Questa versione non usa Tkinter e non usa Canvas. La parte grafica viene
renderizzata da Qt Quick tramite QML, con animazioni native, composizione,
trasparenze e rendering accelerato quando disponibile sulla piattaforma.

Il modulo mantiene l'API HUDJarvis usata dal Kernel e dal launcher di Jarvis.
La grafica vive in ``interfaccia/hud.qml`` mentre questo file si occupa del
ponte tra il Core Python e l'interfaccia.
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import socket
import threading
import time
from pathlib import Path

try:
    import psutil
except Exception:  # pragma: no cover - dipendenza opzionale
    psutil = None

try:
    from PySide2.QtCore import QObject, QTimer, Signal, Slot, QUrl
    from PySide2.QtGui import QGuiApplication
    from PySide2.QtQml import QQmlApplicationEngine
    PYSIDE2_DISPONIBILE = True
except Exception:  # pragma: no cover - consente i test senza GUI
    QObject = object
    QTimer = None
    Signal = None
    Slot = None
    QUrl = None
    QGuiApplication = None
    QQmlApplicationEngine = None
    PYSIDE2_DISPONIBILE = False


ROOT = Path(__file__).resolve().parent
QML_FILE = ROOT / "hud.qml"


if PYSIDE2_DISPONIBILE:

    class HUDBridge(QObject):
        """Ponte thread-safe tra il backend Python e QML."""

        stateChanged = Signal(str)
        hideRequested = Signal()
        showRequested = Signal()

        @Slot()
        def hide(self):
            self.hideRequested.emit()

        @Slot()
        def show(self):
            self.showRequested.emit()


class HUDJarvis:
    """Interfaccia HUD definitiva di J.A.R.V.I.S."""

    def __init__(self, kernel=None, width=1050, height=650):
        self.nome = "J.A.R.V.I.S. HUD"
        self.versione = "definitiva"
        self.kernel = kernel
        self.width = width
        self.height = height

        self.attivo = False
        self.ascolto = False
        self.parlando = False
        self.dati = {}
        self.eventi = []

        self.finestra = None
        self.engine = None
        self.app = None
        self.bridge = None
        self.timer = None
        self._ready = threading.Event()
        self._stop = threading.Event()
        self._qt_thread = None
        self._pending_state = None
        self._avvio_timestamp = time.monotonic()

    # ------------------------------------------------------------------
    # Ciclo di vita
    # ------------------------------------------------------------------
    def avvia(self):
        """Compatibilità con il vecchio modulo HUD.

        Qt/QML su macOS deve vivere nel thread principale, quindi il launcher
        ufficiale chiama ``_run_qt()`` direttamente. Se avvia() viene chiamato
        dal main thread, entra nel loop Qt; da un thread secondario non forza
        un'applicazione GUI in un contesto non supportato.
        """
        if self.attivo:
            return True

        if not PYSIDE2_DISPONIBILE:
            self.registra_evento("Qt Quick non disponibile: installare PySide2 5.15.2.1")
            return False

        if threading.current_thread() is not threading.main_thread():
            self.registra_evento("HUD Qt Quick richiesto dal main thread")
            return False

        return self._run_qt()

    def _run_qt(self):
        """Avvia il runtime Qt Quick e mantiene la finestra nel main thread."""
        if not PYSIDE2_DISPONIBILE:
            self._ready.set()
            self.attivo = False
            return False

        if not QML_FILE.exists():
            self.registra_evento(f"QML HUD non trovato: {QML_FILE}")
            self._ready.set()
            return False

        self._stop.clear()
        self._ready.clear()
        self._avvio_timestamp = time.monotonic()
        self.attivo = True

        try:
            self.app = QGuiApplication.instance()
            owns_app = self.app is None
            if owns_app:
                self.app = QGuiApplication([])

            self.engine = QQmlApplicationEngine()
            self.bridge = HUDBridge()
            self.engine.rootContext().setContextProperty("bridge", self.bridge)

            self.engine.load(QUrl.fromLocalFile(str(QML_FILE)))
            roots = self.engine.rootObjects()
            if not roots:
                raise RuntimeError("Qt Quick non ha creato la finestra HUD")

            self.finestra = roots[0]
            self.finestra.setProperty("width", self.width)
            self.finestra.setProperty("height", self.height)
            self.finestra.setProperty("title", "J.A.R.V.I.S. — Neural Command Interface")

            self.timer = QTimer()
            self.timer.setInterval(750)
            self.timer.timeout.connect(self._tick)
            self.timer.start()

            self._ready.set()
            self.registra_evento("HUD Qt Quick operativo")
            self._emetti_stato()

            if owns_app:
                self.app.exec_()
            else:
                # Normalmente non viene raggiunto dal launcher ufficiale.
                while self.attivo and not self._stop.is_set():
                    self.app.processEvents()
                    time.sleep(0.01)

            return True

        except Exception as errore:
            self.registra_evento(f"Errore HUD Qt Quick: {errore}")
            self._ready.set()
            return False
        finally:
            self.attivo = False
            self._stop.set()
            try:
                if self.timer:
                    self.timer.stop()
            except Exception:
                pass
            self.timer = None
            self.engine = None
            self.bridge = None
            self.finestra = None

    def ferma(self):
        self.attivo = False
        self._stop.set()
        try:
            if self.timer:
                self.timer.stop()
        except Exception:
            pass
        try:
            if self.app:
                self.app.quit()
        except Exception:
            pass

    def mostra(self):
        try:
            if self.bridge:
                self.bridge.show()
            elif self.finestra:
                self.finestra.setProperty("visible", True)
        except Exception:
            pass

    def nascondi(self):
        try:
            if self.bridge:
                self.bridge.hide()
            elif self.finestra:
                self.finestra.setProperty("visible", False)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Collegamento al Core
    # ------------------------------------------------------------------
    def collega_kernel(self, kernel):
        self.kernel = kernel
        self.registra_evento("Kernel collegato")
        self._emetti_stato()

    def aggiorna(self, dati):
        self.dati = dati or {}
        self._emetti_stato()

    def aggiorna_kernel(self):
        if self.kernel and hasattr(self.kernel, "stato_sistema"):
            try:
                self.dati = self.kernel.stato_sistema() or {}
            except Exception:
                pass
        self._emetti_stato()

    def registra_evento(self, messaggio):
        self.eventi.append(
            (
                datetime.datetime.now().strftime("%H:%M:%S"),
                str(messaggio),
            )
        )
        self.eventi = self.eventi[-18:]
        self._emetti_stato()

    def imposta_ascolto(self, attivo=True):
        self.ascolto = bool(attivo)
        self.registra_evento("Canale voce: ascolto" if self.ascolto else "Canale voce: standby")

    def imposta_parlato(self, attivo=True):
        self.parlando = bool(attivo)
        self.registra_evento("Sintesi vocale attiva" if self.parlando else "Sintesi vocale completata")

    def parla(self):
        self.imposta_parlato(True)

    # ------------------------------------------------------------------
    # Stato visualizzato
    # ------------------------------------------------------------------
    def _tick(self):
        if not self.attivo or self._stop.is_set():
            return
        self.aggiorna_kernel()

    def _emetti_stato(self):
        if not self.bridge:
            self._pending_state = self._stato_hud()
            return
        try:
            self.bridge.stateChanged.emit(
                json.dumps(self._stato_hud(), ensure_ascii=False)
            )
        except Exception:
            pass

    def _stato_hud(self):
        stato = self.dati or {}
        sistema = stato.get("sistema") or {}
        memoria = stato.get("memoria") or {}
        dispositivi = stato.get("dispositivi") or {}
        voce = stato.get("voce") or {}

        cpu = self._percentuale_cpu()
        memoria_percent = self._percentuale_memoria()
        disco_percent = self._percentuale_disco()
        rete = self._rete_percentuale()

        comando = self._ultimo_comando(stato)
        risposta = self._ultima_risposta(stato)
        eventi = "\n".join(
            f"{ora}  {messaggio}" for ora, messaggio in reversed(self.eventi[-10:])
        )

        activity = 0.22
        if self.ascolto:
            activity = 0.82
        elif self.parlando:
            activity = 0.94
        elif comando:
            activity = 0.55

        return {
            "state": "LISTENING" if self.ascolto else "SPEAKING" if self.parlando else "SYSTEM ONLINE",
            "command": comando or "Awaiting command...",
            "response": risposta or "Neural core standing by.",
            "clock": datetime.datetime.now().strftime("%H:%M:%S"),
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "cpu": str(cpu),
            "memory": str(memoria_percent),
            "disk": str(disco_percent),
            "network": str(rete),
            "voice": "LISTENING" if self.ascolto else "SPEAKING" if self.parlando else (
                "READY" if voce else "STANDBY"
            ),
            "memory_state": "ONLINE" if memoria else "READY",
            "devices": self._dispositivi_testo(dispositivi),
            "kernel": str(sistema.get("stato", "OPERATIONAL")).upper(),
            "events": eventi,
            "listening": self.ascolto,
            "speaking": self.parlando,
            "activity": activity,
        }

    @staticmethod
    def _percentuale_cpu():
        if psutil is None:
            return 0
        try:
            return max(0, min(100, int(psutil.cpu_percent(interval=None))))
        except Exception:
            return 0

    @staticmethod
    def _percentuale_memoria():
        if psutil is None:
            return 0
        try:
            return max(0, min(100, int(psutil.virtual_memory().percent)))
        except Exception:
            return 0

    @staticmethod
    def _percentuale_disco():
        try:
            return max(0, min(100, int(shutil.disk_usage(os.path.expanduser("~")).used * 100 / shutil.disk_usage(os.path.expanduser("~")).total)))
        except Exception:
            return 0

    @staticmethod
    def _rete_percentuale():
        try:
            socket.gethostbyname(socket.gethostname())
            return 100
        except Exception:
            return 0

    @staticmethod
    def _ultimo_comando(stato):
        for chiave in ("comandi", "sistema", "contesto"):
            valore = stato.get(chiave)
            if isinstance(valore, dict):
                for nome in ("ultimo_comando", "ultimo", "comando"):
                    if valore.get(nome):
                        return str(valore[nome])
        return ""

    @staticmethod
    def _ultima_risposta(stato):
        for chiave in ("comandi", "sistema", "contesto"):
            valore = stato.get(chiave)
            if isinstance(valore, dict):
                for nome in ("ultima_risposta", "risposta"):
                    if valore.get(nome):
                        return str(valore[nome])
        return ""

    @staticmethod
    def _dispositivi_testo(dispositivi):
        if not isinstance(dispositivi, dict):
            return "0 / 0"
        totale = len(dispositivi)
        online = 0
        for valore in dispositivi.values():
            if isinstance(valore, dict):
                stato = str(valore.get("stato", valore.get("state", ""))).lower()
                if stato in {"online", "connesso", "connessa", "attivo", "operativo"}:
                    online += 1
            elif valore:
                online += 1
        return f"{online} / {totale}"


__all__ = ["HUDJarvis"]
