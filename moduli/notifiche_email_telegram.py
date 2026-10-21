"""Notifiche email verso Telegram, solo se configurate esplicitamente.

Legge esclusivamente le intestazioni dei messaggi non letti tramite IMAP SSL.
Non scarica corpi/allegati, non modifica lo stato letto/non letto e non invia email.
Le credenziali vengono lette da variabili d ambiente, mai dal repository.
"""
from __future__ import annotations

import email
import imaplib
import os
import threading
import time
from email.header import decode_header
from email.utils import parseaddr


class NotificheEmailTelegram:
    def __init__(self, logger=None, intervallo: int = 90):
        self.logger = logger
        self.intervallo = max(30, int(intervallo))
        self._stop = threading.Event()
        self._thread = None
        self._visti = set()

    def _log(self, livello, messaggio):
        try:
            if self.logger and hasattr(self.logger, livello):
                getattr(self.logger, livello)(messaggio)
        except Exception:
            pass

    @staticmethod
    def _decodifica(valore):
        parti = []
        for frammento, charset in decode_header(valore or ""):
            if isinstance(frammento, bytes):
                try:
                    parti.append(frammento.decode(charset or "utf-8", errors="replace"))
                except LookupError:
                    parti.append(frammento.decode("utf-8", errors="replace"))
            else:
                parti.append(frammento)
        return " ".join(" ".join(parti).split())

    @staticmethod
    def _telegram(testo):
        token = os.environ.get("JARVIS_TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.environ.get("JARVIS_TELEGRAM_CHAT_ID", "").strip()
        if not token or not chat_id:
            return False, "Token/chat ID Telegram non configurati."
        try:
            import requests
            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": testo[:3500], "disable_web_page_preview": True},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                return False, "Telegram ha rifiutato la notifica."
            return True, None
        except Exception as errore:
            return False, str(errore)

    def controlla_una_volta(self):
        """Controlla le email non lette; torna il numero di notifiche inviate."""
        host = os.environ.get("JARVIS_IMAP_HOST", "").strip()
        user = os.environ.get("JARVIS_IMAP_USER", "").strip()
        password = os.environ.get("JARVIS_IMAP_PASSWORD", "")
        mailbox = os.environ.get("JARVIS_IMAP_MAILBOX", "INBOX").strip() or "INBOX"
        if not all((host, user, password)):
            return 0, "Configurare JARVIS_IMAP_HOST, JARVIS_IMAP_USER e JARVIS_IMAP_PASSWORD."
        inviati = 0
        try:
            with imaplib.IMAP4_SSL(host, int(os.environ.get("JARVIS_IMAP_PORT", "993")), timeout=15) as client:
                client.login(user, password)
                status, _ = client.select(mailbox, readonly=True)
                if status != "OK":
                    return 0, "Impossibile aprire la cartella IMAP in sola lettura."
                status, dati = client.uid("search", None, "UNSEEN")
                if status != "OK":
                    return 0, "Ricerca delle email non lette non riuscita."
                uids = (dati[0] or b"").split() if dati else []
                for uid in uids:
                    chiave = (host, mailbox, uid.decode("ascii", errors="ignore"))
                    if chiave in self._visti:
                        continue
                    status, fetched = client.uid("fetch", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
                    if status != "OK":
                        continue
                    raw = next((part[1] for part in fetched if isinstance(part, tuple) and len(part) > 1), b"")
                    msg = email.message_from_bytes(raw or b"")
                    mittente = self._decodifica(msg.get("From", ""))
                    oggetto = self._decodifica(msg.get("Subject", "(senza oggetto)"))
                    nome, indirizzo = parseaddr(mittente)
                    mittente_breve = (nome or indirizzo or "Mittente sconosciuto")[:160]
                    testo = f"Nuova email non letta\\nDa: {mittente_breve}\\nOggetto: {oggetto[:240]}"
                    ok, errore = self._telegram(testo)
                    if ok:
                        self._visti.add(chiave)
                        inviati += 1
                    else:
                        self._log("warning", f"Notifica Telegram non inviata: {errore}")
                return inviati, None
        except Exception as errore:
            return inviati, str(errore)

    def avvia(self):
        if self._thread and self._thread.is_alive():
            return True
        self._stop.clear()

        def lavoro():
            while not self._stop.is_set():
                _, errore = self.controlla_una_volta()
                if errore:
                    self._log("warning", f"Notifiche email/Telegram: {errore}")
                self._stop.wait(self.intervallo)

        self._thread = threading.Thread(target=lavoro, name="JarvisEmailTelegram", daemon=True)
        self._thread.start()
        self._log("info", "Monitor email/Telegram attivato in modalità sola lettura.")
        return True

    def ferma(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None


__all__ = ["NotificheEmailTelegram"]