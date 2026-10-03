import argparse
import json
import os
import uuid
import urllib.error
import urllib.request


ENDPOINT = "https://api.elevenlabs.io/v1/voices/add"


def _multipart(file_path, name, description):
    boundary = "----JarvisVoiceClone" + uuid.uuid4().hex
    chunks = []

    def field(key, value):
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
            str(value).encode("utf-8"),
            b"\r\n",
        ])

    field("name", name)
    field("description", description)

    with open(file_path, "rb") as audio:
        contenuto = audio.read()

    chunks.extend([
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="files[]"; filename="jarvis-reference.wav"\r\n',
        b"Content-Type: audio/wav\r\n\r\n",
        contenuto,
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ])
    return boundary, b"".join(chunks)


def clona(file_path, name="Jarvis Italian Reference", description="Italian Jarvis-style reference voice"):
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Imposta ELEVENLABS_API_KEY prima di creare la voce.")

    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)

    boundary, body = _multipart(file_path, name, description)
    richiesta = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "xi-api-key": api_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(richiesta, timeout=60) as risposta:
            return json.loads(risposta.read().decode("utf-8"))
    except urllib.error.HTTPError as errore:
        dettaglio = errore.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ElevenLabs ha rifiutato il campione ({errore.code}): {dettaglio}") from errore


def main():
    parser = argparse.ArgumentParser(description="Crea la voce clonata usata opzionalmente da Jarvis.")
    parser.add_argument("campione", help="Percorso locale del WAV di riferimento.")
    parser.add_argument("--name", default="Jarvis Italian Reference")
    args = parser.parse_args()

    risultato = clona(args.campione, args.name)
    voice_id = risultato.get("voice_id")
    if not voice_id:
        raise RuntimeError(f"Risposta inattesa: {risultato}")

    print(f"Voce clonata creata. Voice ID: {voice_id}")
    print("Imposta questa variabile nel Mac:")
    print(f'export JARVIS_ELEVENLABS_VOICE_ID="{voice_id}"')
    print("e poi: export JARVIS_VOICE_PROVIDER=elevenlabs")


if __name__ == "__main__":
    main()
