# Visione artificiale locale

Jarvis può analizzare un'immagine locale usando un modello con supporto visivo già installato in Ollama. Questa è una prima integrazione leggera ispirata ai video che mostrano Jarvis mentre identifica oggetti e componenti sulla scrivania.

## Requisiti

- Ollama avviato in locale su `http://127.0.0.1:11434`.
- Un modello multimodale installato. Il valore predefinito è `moondream`; se non è installato, scegli un modello visivo compatibile con l'hardware e configura `JARVIS_VISION_MODEL`.
- Un'immagine locale PNG, JPG, JPEG, WEBP o BMP di dimensione inferiore a 10 MB.

Per installare il modello predefinito, se compatibile con il computer:

```bash
ollama pull moondream
```

Su computer con poca RAM, il caricamento del modello può essere lento e alcuni modelli possono non essere adatti. L'installazione del modello è facoltativa e non modifica l'avvio standard di Jarvis.

## Comandi

```text
analizza immagine /percorso/completo/Scrivania.jpg
descrivi immagine "/percorso con spazi/Componente.png"
stato visione
```

I percorsi sono mantenuti con maiuscole e spazi. Il comando chiede al modello una descrizione in italiano. La risposta dipende dal modello e può contenere errori: verifica i dettagli importanti direttamente.

## Privacy e limiti

- L'analisi viene inviata soltanto a Ollama su `localhost`; URL remoti sono rifiutati.
- Jarvis non apre né registra automaticamente la webcam e non salva immagini.
- Questa versione analizza file immagine forniti esplicitamente. Non è ancora un flusso video continuo né un riconoscimento automatico in tempo reale.
- L'immagine deve essere inferiore a 10 MB; la richiesta scade dopo 90 secondi.
- Non usare il risultato visivo da solo per decisioni di sicurezza o per identificare con certezza persone, componenti pericolosi o condizioni mediche.

La futura modalità webcam dovrà richiedere consenso esplicito, indicare quando la camera è attiva e restare disattivata all'avvio.
