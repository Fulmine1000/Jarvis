# Alexa Skill — Jarvis

Questa cartella contiene il primo endpoint Lambda della Skill Alexa italiana. Alexa è
un terminale vocale: il Core, la memoria e la logica di Jarvis restano sul dispositivo
host (inizialmente il Mac).

## Stato

- Handler Lambda Python basato su ASK SDK.
- Gestione apertura, richiesta Jarvis, aiuto, stop e chiusura sessione.
- Inoltro esclusivamente del testo a `POST /v1/chat`.
- Richiesto un URL HTTPS; redirect HTTP non seguiti.
- Token richiesto (minimo 32 caratteri), non salvato nel repository.
- Nessuna esecuzione shell o endpoint per comandi arbitrari.
- Non ancora pubblicata né collegata a un account Amazon.

## Deploy AWS

1. Creare una funzione AWS Lambda Python 3.12.
2. Installare le dipendenze di `requirements.txt` nel pacchetto di deploy.
3. Impostare il handler `lambda_function.lambda_handler`.
4. Configurare `JARVIS_GATEWAY_URL` con un URL HTTPS raggiungibile da AWS.
5. Configurare `JARVIS_GATEWAY_TOKEN` tramite AWS Secrets Manager o ambiente protetto.
6. In Alexa Developer Console creare una Custom Skill in italiano e associare l'endpoint Lambda.
7. Configurare l'ID Skill e verificare che la verifica firma/timestamp dell'ASK SDK resti attiva.
8. Testare prima con richieste innocue e timeout/rete non disponibile.

**Importante:** il gateway attuale nel repository ascolta solo su loopback. Non inserire
l'indirizzo locale del Mac in Lambda e non aprire la porta del Mac sul router. Prima
del collegamento reale serve un relay/tunnel HTTPS autenticato, con TLS verificato,
token distinto e revocabile, rate limiting e log senza segreti.

## Interaction model

Crea un intent `JarvisIntent` con uno slot:

- Nome: `testo`
- Tipo: `AMAZON.SearchQuery`

Esempi di utterance:

- `chiedi a Jarvis {testo}`
- `di' a Jarvis {testo}`
- `Jarvis {testo}`

Invocation name suggerito: `jarvis`.

Sugli Echo standard la wake word resta “Alexa”; la Skill si apre con “Alexa, apri
Jarvis”. Non è possibile sostituire la wake word con “Hey Jarvis” su Echo standard.
