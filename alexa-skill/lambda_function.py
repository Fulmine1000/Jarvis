"""Alexa Skill Lambda: terminale vocale per il Core centrale di Jarvis.

Configurazione Lambda:
- JARVIS_GATEWAY_URL: URL HTTPS pubblico del relay/gateway autenticato.
- JARVIS_GATEWAY_TOKEN: token condiviso con il gateway, conservato in AWS Secrets Manager
  o come variabile d'ambiente protetta (mai nel repository).
- ALEXA_SKILL_ID: ID Skill opzionale per vincolare l'adapter alla Skill attesa.

La Skill non esegue comandi di sistema e inoltra soltanto testo al Core.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler,
    AbstractExceptionHandler,
)
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response


MAX_INPUT_CHARS = 1000
MAX_RESPONSE_BYTES = 8192
GATEWAY_TIMEOUT_SECONDS = 8


def _gateway_chat(testo: str) -> str:
    """Invia testo al gateway HTTPS configurato; non segue redirect."""
    url = os.environ.get("JARVIS_GATEWAY_URL", "").strip()
    token = os.environ.get("JARVIS_GATEWAY_TOKEN", "")
    access_id = os.environ.get("CLOUDFLARE_ACCESS_CLIENT_ID", "").strip()
    access_secret = os.environ.get("CLOUDFLARE_ACCESS_CLIENT_SECRET", "").strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise RuntimeError("Gateway HTTPS non configurato")
    if not token or len(token) < 32:
        raise RuntimeError("Credenziali gateway non configurate")
    if bool(access_id) != bool(access_secret):
        raise RuntimeError("Credenziali Cloudflare Access incomplete")
    if not isinstance(testo, str) or not testo.strip() or len(testo) > MAX_INPUT_CHARS:
        raise ValueError("Richiesta non valida")

    body = json.dumps({"text": testo.strip()}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url.rstrip("/") + "/v1/chat",
        data=body,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            **({"CF-Access-Client-Id": access_id,
                "CF-Access-Client-Secret": access_secret} if access_id and access_secret else {}),
        },
        method="POST",
    )
    # No redirect handler: evita che l'header Authorization venga inoltrato
    # verso un host diverso a seguito di un redirect.
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=GATEWAY_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise RuntimeError("Gateway non disponibile")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("Connessione a Jarvis non disponibile") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError("Risposta del gateway troppo grande")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Risposta del gateway non valida") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Risposta del gateway non valida")
    risposta = payload.get("response")
    if payload.get("ok") is not True or not isinstance(risposta, str) or not risposta.strip():
        raise RuntimeError("Jarvis non ha restituito una risposta")
    return risposta.strip()[:MAX_RESPONSE_BYTES]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _speak(handler_input: HandlerInput, testo: str, end_session: bool = False) -> Response:
    return (
        handler_input.response_builder
        .speak(testo)
        .set_should_end_session(end_session)
        .response
    )


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return handler_input.request_envelope.request.object_type == "LaunchRequest"

    def handle(self, handler_input: HandlerInput) -> Response:
        return _speak(handler_input, "Salve Simone. Jarvis è pronto. Come posso assisterla?")


class JarvisIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return handler_input.request_envelope.request.object_type == "IntentRequest" and (
            handler_input.request_envelope.request.intent.name == "JarvisIntent"
        )

    def handle(self, handler_input: HandlerInput) -> Response:
        slots = handler_input.request_envelope.request.intent.slots or {}
        slot = slots.get("testo")
        testo = getattr(getattr(slot, "value", None), "strip", lambda: "")()
        if not testo:
            return _speak(handler_input, "Non ho ricevuto la richiesta. Può ripetere?")
        try:
            risposta = _gateway_chat(testo)
        except (RuntimeError, ValueError):
            return _speak(
                handler_input,
                "Al momento non riesco a raggiungere il Core di Jarvis. Riprovi tra poco.",
            )
        return _speak(handler_input, risposta)


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return handler_input.request_envelope.request.object_type == "IntentRequest" and (
            handler_input.request_envelope.request.intent.name == "AMAZON.HelpIntent"
        )

    def handle(self, handler_input: HandlerInput) -> Response:
        return _speak(handler_input, "Mi dica cosa desidera chiedere a Jarvis.")


class StopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return handler_input.request_envelope.request.object_type == "IntentRequest" and (
            handler_input.request_envelope.request.intent.name in {
                "AMAZON.StopIntent", "AMAZON.CancelIntent"
            }
        )

    def handle(self, handler_input: HandlerInput) -> Response:
        return _speak(handler_input, "A disposizione.", end_session=True)


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return handler_input.request_envelope.request.object_type == "SessionEndedRequest"

    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.response


class SafeExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True

    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        # Non inserire dettagli tecnici o segreti nella risposta vocale.
        return _speak(handler_input, "Si è verificato un problema. Riprovi tra poco.")


sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(JarvisIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(StopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(SafeExceptionHandler())

# SkillAdapter dell'SDK ASK applica la verifica della firma e del timestamp
# delle richieste Alexa; non disabilitare tali controlli nel deployment.
lambda_handler = sb.lambda_handler()
