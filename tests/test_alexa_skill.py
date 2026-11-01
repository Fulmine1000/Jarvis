"""Test di sicurezza e contratto per l'adapter Alexa (solo libreria standard)."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "alexa-skill" / "lambda_function.py"


def _install_ask_sdk_stubs():
    """Permette di testare il client HTTP senza installare l'SDK Alexa."""
    core = types.ModuleType("ask_sdk_core")
    skill_builder = types.ModuleType("ask_sdk_core.skill_builder")
    dispatch = types.ModuleType("ask_sdk_core.dispatch_components")
    handler_input = types.ModuleType("ask_sdk_core.handler_input")
    model = types.ModuleType("ask_sdk_model")

    class SkillBuilder:
        def add_request_handler(self, handler):
            pass
        def add_exception_handler(self, handler):
            pass
        def lambda_handler(self):
            return lambda event, context: None

    class AbstractRequestHandler:
        pass

    class AbstractExceptionHandler:
        pass

    class HandlerInput:
        pass

    class Response:
        pass

    skill_builder.SkillBuilder = SkillBuilder
    dispatch.AbstractRequestHandler = AbstractRequestHandler
    dispatch.AbstractExceptionHandler = AbstractExceptionHandler
    handler_input.HandlerInput = HandlerInput
    model.Response = Response

    modules = {
        "ask_sdk_core": core,
        "ask_sdk_core.skill_builder": skill_builder,
        "ask_sdk_core.dispatch_components": dispatch,
        "ask_sdk_core.handler_input": handler_input,
        "ask_sdk_model": model,
    }
    return patch.dict(sys.modules, modules)


class AlexaGatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sdk_patch = _install_ask_sdk_stubs()
        cls.sdk_patch.start()
        spec = importlib.util.spec_from_file_location("jarvis_alexa_lambda_test", MODULE_PATH)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    @classmethod
    def tearDownClass(cls):
        cls.sdk_patch.stop()

    def setUp(self):
        self.env = patch.dict(os.environ, {
            "JARVIS_GATEWAY_URL": "https://gateway.example.test",
            "JARVIS_GATEWAY_TOKEN": "x" * 48,
        }, clear=False)
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_rifiuta_gateway_non_https(self):
        os.environ["JARVIS_GATEWAY_URL"] = "http://gateway.example.test"
        with self.assertRaises(RuntimeError):
            self.module._gateway_chat("ciao")

    def test_rifiuta_token_corto(self):
        os.environ["JARVIS_GATEWAY_TOKEN"] = "breve"
        with self.assertRaises(RuntimeError):
            self.module._gateway_chat("ciao")

    def test_rifiuta_input_vuoto_o_troppo_lungo(self):
        with self.assertRaises(ValueError):
            self.module._gateway_chat(" ")
        with self.assertRaises(ValueError):
            self.module._gateway_chat("x" * (self.module.MAX_INPUT_CHARS + 1))

    def test_invia_bearer_e_legge_risposta_valida(self):
        class FakeResponse:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, limit):
                return json.dumps({"ok": True, "response": "  Ciao Simone  "}).encode()

        class FakeOpener:
            def open(self, request, timeout):
                self.request = request
                self.timeout = timeout
                return FakeResponse()

        opener = FakeOpener()
        with patch.object(self.module.urllib.request, "build_opener", return_value=opener):
            result = self.module._gateway_chat("ciao")
        self.assertEqual(result, "Ciao Simone")
        self.assertEqual(opener.request.get_header("Authorization"), "Bearer " + "x" * 48)
        self.assertEqual(opener.timeout, self.module.GATEWAY_TIMEOUT_SECONDS)
        self.assertTrue(opener.request.full_url.endswith("/v1/chat"))

    def test_rifiuta_payload_non_valido(self):
        class FakeResponse:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, limit):
                return b"[]"

        class FakeOpener:
            def open(self, request, timeout):
                return FakeResponse()

        with patch.object(self.module.urllib.request, "build_opener", return_value=FakeOpener()):
            with self.assertRaises(RuntimeError):
                self.module._gateway_chat("ciao")

    def test_limita_dimensione_risposta(self):
        class FakeResponse:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, limit):
                return b"x" * (self.module.MAX_RESPONSE_BYTES + 1)

        class FakeOpener:
            def open(self, request, timeout):
                return FakeResponse()

        with patch.object(self.module.urllib.request, "build_opener", return_value=FakeOpener()):
            with self.assertRaises(RuntimeError):
                self.module._gateway_chat("ciao")


if __name__ == "__main__":
    unittest.main()
