# Conoscenza locale Jarvis

Questa cartella contiene la base di conoscenza usata dal cervello locale di Jarvis.

## Funzionamento

1. Jarvis riceve la domanda.
2. Il recuperatore confronta domanda, titoli e parole chiave con `base.json`.
3. Vengono passate al modello solo le voci piu pertinenti.
4. Per richieste che richiedono dati aggiornati viene aggiunto anche il risultato della ricerca Web, quando disponibile.
5. Qwen2.5 3B Instruct Q4_K_M genera la risposta tramite llama.cpp.

La base locale non viene inserita interamente nel prompt: questo mantiene basso il costo in token e la latenza sul Mac Intel.
