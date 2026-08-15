import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer

model = Model("vosk-model-small-it-0.22")
rec = KaldiRecognizer(model, 16000)

def ascolta():
    print("🎤 Ti ascolto...")

    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1
    ) as stream:

        while True:
            dati, overflow = stream.read(4000)

            if rec.AcceptWaveform(bytes(dati)):
                risultato = json.loads(rec.Result())
                testo = risultato["text"]

                if testo:
                    print("Hai detto:", testo)
                    return testo
