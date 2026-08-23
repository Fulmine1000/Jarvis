# Comandi principali

## Conversazione

- `ciao`
- `buongiorno`
- `come stai`
- `chi sei`
- `aiuto`
- `grazie`

## Sistema

- `che ore sono`
- `che giorno è`
- `stato sistema`
- `diagnostica`
- `stato computer`
- `stato memoria`
- `stato voce`
- `stato ai`
- `stato automazioni`
- `stato visione`

## Memoria

- `ricorda che il mio colore preferito è blu`
- `cosa ricordi di me`
- `dimentica <chiave>`
- `chiamami <nome>`
- `come mi chiamo`

## Operazioni

- `calcola 25 * 4`
- `cerca <testo>`
- `apri sito <sito>`
- `meteo <città>`
- `apri app <app>`
- `fai uno screenshot`
- `imposta timer di 60 secondi`
- `annulla timer`
- `volume 50`
- `silenzia computer`

## HUD

- `attiva hud`
- `spegni hud`

## Dispositivi

I moduli esistenti mantengono i comandi per telefono, TV LG webOS, Bluetooth, rete e smart home. Le azioni reali dipendono dalla connessione e dai permessi del dispositivo.

## AI locale

Quando Ollama è installato e configurato, le frasi non riconosciute come comandi possono essere passate al modello locale configurato in `core/dialogo.py`. Senza Ollama Jarvis continua con il router deterministico.
