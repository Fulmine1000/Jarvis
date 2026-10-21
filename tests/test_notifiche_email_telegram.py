"""Test offline per il bridge email/Telegram."""
import os
import unittest
from unittest.mock import patch

from moduli.notifiche_email_telegram import NotificheEmailTelegram


class TestNotificheEmailTelegram(unittest.TestCase):
    def test_decodifica_intestazione_mime(self):
        valore = "=?utf-8?b?UHJvdmEgZW1haWw=?="
        self.assertEqual(NotificheEmailTelegram._decodifica(valore), "Prova email")

    def test_telegram_senza_credenziali_non_invia(self):
        with patch.dict(os.environ, {}, clear=True):
            ok, errore = NotificheEmailTelegram._telegram("test")
        self.assertFalse(ok)
        self.assertIn("non configurati", errore)

    def test_intervallo_minimo(self):
        self.assertEqual(NotificheEmailTelegram(intervallo=1).intervallo, 30)


if __name__ == "__main__":
    unittest.main()
