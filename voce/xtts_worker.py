"""Worker CLI isolato per la sintesi XTTS di Jarvis.

Eseguito come modulo Python per evitare il bootstrap fragile di multiprocessing
spawn in alcune combinazioni di macOS e Python.
"""
import argparse
import os
import sys
import traceback


def main(argv=None):
    parser = argparse.ArgumentParser(description="Genera audio locale con XTTS v2")
    parser.add_argument("--text", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--language", default="it_IT")
    parser.add_argument("--audio", required=True)
    parser.add_argument("--status", required=True)
    args = parser.parse_args(argv)

    try:
        if not os.path.isfile(args.reference) or os.path.getsize(args.reference) == 0:
            raise FileNotFoundError("Il campione WAV non esiste o è vuoto")

        from TTS.api import TTS

        print("🔊 Processo XTTS: caricamento modello...", flush=True)
        model = TTS(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            progress_bar=False,
            gpu=False,
        )
        print("🎙️ Processo XTTS: generazione audio...", flush=True)
        model.tts_to_file(
            text=args.text,
            speaker_wav=args.reference,
            language=args.language,
            file_path=args.audio,
            split_sentences=False,
            temperature=0.65,
            top_k=40,
            top_p=0.80,
            repetition_penalty=10.0,
            speed=1.0,
            gpt_cond_len=6,
            gpt_cond_chunk_len=4,
            max_ref_len=4,
            sound_norm_refs=False,
            enable_text_splitting=False,
        )
        if not os.path.isfile(args.audio) or os.path.getsize(args.audio) == 0:
            raise RuntimeError("XTTS ha terminato senza creare un WAV valido")
        with open(args.status, "w", encoding="utf-8") as status:
            status.write("OK")
        print("✅ Worker XTTS: audio generato.", flush=True)
        return 0
    except BaseException as error:
        detail = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        try:
            with open(args.status, "w", encoding="utf-8") as status:
                status.write(f"{type(error).__name__}: {error}\n{detail}")
        except OSError:
            pass
        print(f"❌ Worker XTTS: {type(error).__name__}: {error}", file=sys.stderr, flush=True)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
