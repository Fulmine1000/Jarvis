import os
import tempfile
import time
import unittest
from unittest.mock import patch

from core.automazioni import AutomazioniJarvis, PianificatoreJarvis
from core.visione import VisioneJarvis
from core.dialogo import DialogoJarvis


class TestAutomazioni(unittest.TestCase):
    def test_automazione(self):
        risultati = []
        motore = AutomazioniJarvis()
        motore.registra("test", lambda: risultati.append(True))
        self.assertTrue(motore.esegui("test"))
        self.assertEqual(risultati, [True])
        self.assertTrue(motore.disattiva("test"))
        self.assertFalse(motore.esegui("test"))
        motore.ferma()

    def test_pianificatore(self):
        risultati = []
        scheduler = PianificatoreJarvis()
        scheduler.pianifica("test", 0.01, lambda: risultati.append(True))
        time.sleep(0.05)
        self.assertEqual(risultati, [True])


class TestVisione(unittest.TestCase):
    def test_stato_senza_dipendenze(self):
        visione = VisioneJarvis()
        stato = visione.stato()
        self.assertIn("camera_disponibile", stato)


class TestDialogo(unittest.TestCase):
    def test_default_usa_router_automatico_e_modello_leggero(self):
        with tempfile.TemporaryDirectory() as cartella:
            file_storia = os.path.join(cartella, "conversazioni.json")
            with patch.dict(os.environ, {}, clear=True):
                with patch.object(DialogoJarvis, "FILE_STORIA", file_storia):
                    with patch.object(
                        DialogoJarvis, "_trova_llama", return_value=(None, None)
                    ):
                        dialogo = DialogoJarvis()

        self.assertEqual(dialogo.provider_richiesto, "auto")
        self.assertEqual(dialogo.modello, "qwen2.5:0.5b")
        self.assertEqual(
            dialogo.modello_llama,
            "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        )

    def test_auto_seleziona_ollama_se_llama_cpp_non_e_disponibile(self):
        with tempfile.TemporaryDirectory() as cartella:
            file_storia = os.path.join(cartella, "conversazioni.json")
            with patch.dict(os.environ, {}, clear=True):
                with patch.object(DialogoJarvis, "FILE_STORIA", file_storia):
                    with patch.object(
                        DialogoJarvis, "_trova_llama", return_value=(None, None)
                    ):
                        dialogo = DialogoJarvis()

        with patch.object(
            dialogo, "_trova_llama", return_value=(None, None)
        ), patch.object(
            dialogo,
            "_raggiungibile",
            side_effect=lambda endpoint, timeout=0.5: endpoint == dialogo.endpoint,
        ):
            self.assertEqual(dialogo._backend_disponibili(), ["ollama"])

    def test_trova_llama_riconosce_llama_server_exe_su_windows(self):
        with tempfile.TemporaryDirectory() as cartella:
            file_storia = os.path.join(cartella, "conversazioni.json")
            with patch.dict(
                os.environ, {"JARVIS_AI_PROVIDER": "locale"}, clear=True
            ):
                with patch.object(DialogoJarvis, "BASE_JARVIS", cartella):
                    with patch.object(DialogoJarvis, "FILE_STORIA", file_storia):
                        dialogo = DialogoJarvis()

            def file_presente(percorso):
                return percorso.endswith("llama-server.exe") or percorso.endswith(
                    "qwen2.5-0.5b-instruct-q4_k_m.gguf"
                )

            with patch(
                "core.dialogo.platform.system", return_value="Windows"
            ), patch(
                "core.dialogo.os.path.isfile", side_effect=file_presente
            ):
                binario, modello = dialogo._trova_llama()

        self.assertTrue(binario.endswith("llama-server.exe"))
        self.assertTrue(modello.endswith("qwen2.5-0.5b-instruct-q4_k_m.gguf"))

    def test_stato(self):
        # Il test deve usare una cronologia isolata: la cronologia reale di
        # Jarvis è persistente e può contenere messaggi di sessioni precedenti.
        with tempfile.TemporaryDirectory() as cartella:
            file_storia_test = os.path.join(cartella, "conversazioni.json")
            with patch.object(DialogoJarvis, "FILE_STORIA", file_storia_test):
                dialogo = DialogoJarvis()
                stato = dialogo.stato()

        self.assertIn(
            stato["motore"],
            {
                "Ollama locale",
                "Conversation Engine locale",
                "IA automatica (backend non attivo)",
                "llama.cpp locale",
                "API compatibile",
            },
        )
        self.assertEqual(stato["storia_messaggi"], 0)


if __name__ == "__main__":
    unittest.main()
