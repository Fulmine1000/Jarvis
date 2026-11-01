import json
import urllib.error
import urllib.request
import unittest

from core.gateway_remoto import GatewayJarvis


class _Logger:
    def info(self, message):
        pass

    def warning(self, message):
        pass


class _Intelligenza:
    def __init__(self):
        self.richieste = []

    def rispondi(self, testo):
        self.richieste.append(testo)
        return "Risposta di prova"


class _Kernel:
    nome = "J.A.R.V.I.S."
    stato = "Operativo"

    def __init__(self):
        self.logger = _Logger()
        self.intelligenza = _Intelligenza()


class TestGatewayJarvis(unittest.TestCase):
    def setUp(self):
        self.kernel = _Kernel()
        self.token = "t" * 48
        self.gateway = GatewayJarvis(self.kernel, port=0, token=self.token)
        self.gateway.avvia()
        self.port = self.gateway._server.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self):
        self.gateway.ferma()

    def request(self, path, method="GET", token=None, payload=None, content_type="application/json"):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if token is not None:
            req.add_header("Authorization", "Bearer " + token)
        if data is not None:
            req.add_header("Content-Type", content_type)
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read().decode("utf-8"))

    def test_health_richiede_autenticazione(self):
        status, _ = self.request("/v1/health")
        self.assertEqual(status, 401)
        status, body = self.request("/v1/health", token=self.token)
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

    def test_chat_autenticata_inoltra_solo_testo_al_cervello(self):
        status, body = self.request(
            "/v1/chat", method="POST", token=self.token, payload={"text": "Ciao Jarvis"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["response"], "Risposta di prova")
        self.assertEqual(self.kernel.intelligenza.richieste, ["Ciao Jarvis"])

    def test_chat_rifiuta_schema_non_previsto(self):
        status, _ = self.request(
            "/v1/chat", method="POST", token=self.token,
            payload={"text": "ciao", "shell": "rm -rf /"}
        )
        self.assertEqual(status, 400)
        self.assertEqual(self.kernel.intelligenza.richieste, [])

    def test_chat_rifiuta_testo_troppo_lungo(self):
        status, _ = self.request(
            "/v1/chat", method="POST", token=self.token,
            payload={"text": "x" * 2001}
        )
        self.assertEqual(status, 400)

    def test_chat_rifiuta_content_type_errato(self):
        status, _ = self.request(
            "/v1/chat", method="POST", token=self.token,
            payload={"text": "ciao"}, content_type="text/plain"
        )
        self.assertEqual(status, 415)

    def test_endpoint_sconosciuto_non_esegue_comandi(self):
        status, _ = self.request("/api/comando", method="POST", token=self.token, payload={"text": "spegni"})
        self.assertEqual(status, 404)
        self.assertEqual(self.kernel.intelligenza.richieste, [])

    def test_token_debole_non_avvia_gateway(self):
        gateway = GatewayJarvis(self.kernel, port=0, token="debole")
        with self.assertRaises(ValueError):
            gateway.avvia()

    def test_gateway_non_accetta_bind_non_loopback(self):
        gateway = GatewayJarvis(self.kernel, host="0.0.0.0", port=0, token=self.token)
        with self.assertRaises(ValueError):
            gateway.avvia()


if __name__ == "__main__":
    unittest.main()
