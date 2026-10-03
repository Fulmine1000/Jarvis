import base64
import os
import tempfile
import urllib.error
import urllib.request
import json


class ElevenLabsVoce:
    """Provider TTS opzionale con voce clonata tramite ElevenLabs.

    Non contiene credenziali né campioni vocali nella repository.
    La voce viene creata dall'utente con voce/clona_voce.py e identificata
    tramite JARVIS_ELEVENLABS_VOICE_ID.
    """

    endpoint = "https://api.elevenlabs.io/v1/text-to-speech"
    modello_default = "eleven_multilingual_v2"

    def __init__(self):
        self.api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
        self.voice_id = os.environ.get("JARVIS_ELEVENLABS_VOICE_ID", "").strip()
        self.model_id = os.environ.get(
            "JARVIS_ELEVENLABS_MODEL", self.modello_default
        ).strip()
        self.timeout = float(os.environ.get("JARVIS_ELEVENLABS_TIMEOUT", "30"))

    def disponibile(self):
        return bool(self.api_key and self.voice_id)

    def parla(self, testo, percorso_output=None):
        if not self.disponibile():
            return False

        payload = json.dumps({
            "text": str(testo),
            "model_id": self.model_id,
        }).encode("utf-8")

        richiesta = urllib.request.Request(
            f"{self.endpoint}/{self.voice_id}?output_format=mp3_44100_128",
            data=payload,
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            method="POST",
        )

        temporaneo = False
        if not percorso_output:
            fd, percorso_output = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            temporaneo = True

        try:
            with urllib.request.urlopen(richiesta, timeout=self.timeout) as risposta:
                audio = risposta.read()
            with open(percorso_output, "wb") as file_audio:
                file_audio.write(audio)
            return percorso_output
        except (OSError, urllib.error.URLError, urllib.error.HTTPError):
            if temporaneo:
                try:
                    os.remove(percorso_output)
                except OSError:
                    pass
            return False

    @staticmethod
    def da_json_risposta(risposta):
        """Estrae voice_id da una risposta JSON di ElevenLabs."""
        if isinstance(risposta, dict):
            return risposta.get("voice_id")
        return None
