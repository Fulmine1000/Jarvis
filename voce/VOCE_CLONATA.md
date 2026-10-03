# Voce clonata di Jarvis

Questa cartella contiene solo il codice di integrazione. **I campioni vocali non vengono committati nella repository.**

## Uso

Il provider opzionale usa una voce clonata tramite ElevenLabs. ElevenLabs supporta la clonazione da brevi campioni e la sintesi in italiano; il modello Multilingual v2 supporta l'italiano. citeturn0search5turn1search2

1. Usa un campione del quale hai il diritto di utilizzare e clonare la voce.
2. Imposta la chiave API nel terminale:

   `export ELEVENLABS_API_KEY="..."`

3. Crea la voce dal campione locale:

   `python voce/clona_voce.py /percorso/al/campione.wav`

4. Imposta il Voice ID restituito:

   `export JARVIS_ELEVENLABS_VOICE_ID="..."`

5. Seleziona il provider:

   `export JARVIS_VOICE_PROVIDER=elevenlabs`

Jarvis userà la voce clonata quando disponibile; se il servizio, la chiave o la voce non sono disponibili, torna automaticamente a Piper e poi alla voce di sistema.

Le chiamate TTS usano l'endpoint ufficiale di sintesi vocale di ElevenLabs. citeturn0search0turn0search1
