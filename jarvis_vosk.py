# DEPRECATO — mantenuto per riferimento storico.
# Usare il modulo ufficiale corrispondente (vedi analisi/README).
# Non usato dal kernel 3.0.
import json

try:
    import sounddevice as sd
except (ImportError, OSError):
    sd = None

try:
    from vosk import Model, KaldiRecognizer
except (ImportError, OSError):
    Model = None
    KaldiRecognizer = None

if Model is not None and KaldiRecognizer is not None:
    model = Model("vosk-model-small-it-0.22")
    rec = KaldiRecognizer(model, 16000)
else:
    model = None
    rec = None

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
