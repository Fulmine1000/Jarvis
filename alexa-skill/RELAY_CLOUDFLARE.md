# Relay HTTPS sicuro per Alexa ↔ Jarvis

Questa guida pubblica il gateway locale tramite **Cloudflare Tunnel** senza aprire porte
sul router e senza cambiare il bind loopback di Jarvis.

## Architettura

Alexa Skill (AWS Lambda) → HTTPS + Cloudflare Access → Cloudflare Tunnel →  
`cloudflared` sul Mac → `http://127.0.0.1:8767` → Core Jarvis.

Il gateway Jarvis continua ad ascoltare solo su `127.0.0.1`. Non configurare
port forwarding, DMZ o un bind su `0.0.0.0`.

## Prerequisiti

- Mac acceso e con Jarvis operativo.
- Dominio gestito da Cloudflare e accesso al dashboard Cloudflare.
- Cloudflare Tunnel installato sul Mac (`cloudflared`).
- AWS Lambda già predisposta per la Skill Alexa.
- Due segreti distinti: token Jarvis e credenziali Service Token di Cloudflare Access.

## 1. Avviare il gateway locale

Sul Mac, creare un token casuale di almeno 32 caratteri e conservarlo in un password
manager. Non inserirlo nel repository, in screenshot o nei log.

Impostare nell'ambiente del processo Jarvis:

- `JARVIS_GATEWAY_ENABLED=1`
- `JARVIS_GATEWAY_HOST=127.0.0.1`
- `JARVIS_GATEWAY_PORT=8767`
- `JARVIS_GATEWAY_TOKEN=<token-casuale>`

Riavviare Jarvis e verificare localmente `GET http://127.0.0.1:8767/v1/health`
con header `Authorization: Bearer <token>`. Una risposta 401 senza token è attesa.

## 2. Creare il tunnel

Nel dashboard Cloudflare Zero Trust:

1. Aprire Networks → Tunnels e creare un tunnel di tipo Cloudflared.
2. Installare e autenticare `cloudflared` sul Mac seguendo il comando mostrato
   dal dashboard; il token del tunnel è un segreto e non va condiviso.
3. Aggiungere una Public Hostname dedicata, ad esempio
   `jarvis-gateway.example.com`.
4. Impostare come servizio origin `http://127.0.0.1:8767`.
5. Non configurare altri hostname o servizi sullo stesso origin.

Il nome `example.com` è un segnaposto: usare un dominio effettivamente controllato
dall'utente. Lasciare il tunnel in esecuzione come servizio solo dopo aver verificato
che il Mac sia protetto da password e aggiornato.

## 3. Proteggere l'hostname con Cloudflare Access

1. Creare una policy Access per l'hostname del gateway.
2. Usare una policy **Service Auth** e creare un Service Token dedicato alla sola
   Skill Alexa.
3. Non aggiungere una regola Allow pubblica o un bypass.
4. Conservare Client ID e Client Secret come segreti AWS, mai nel repository.
5. Verificare che una richiesta senza Service Token venga bloccata da Access.

Cloudflare Access aggiunge un secondo controllo davanti al Bearer token verificato
dal gateway Jarvis. I due segreti devono essere distinti e revocabili separatamente.

## 4. Configurare AWS Lambda

Impostare le variabili d'ambiente protette:

- `JARVIS_GATEWAY_URL=https://jarvis-gateway.example.com`
- `JARVIS_GATEWAY_TOKEN=<lo-stesso-token-del-gateway>`
- `CLOUDFLARE_ACCESS_CLIENT_ID=<service-token-client-id>`
- `CLOUDFLARE_ACCESS_CLIENT_SECRET=<service-token-client-secret>`

Concedere alla Lambda accesso in lettura ai segreti necessari, preferibilmente tramite
AWS Secrets Manager. Non inserire i valori nel codice o nei parametri del modello Alexa.

**Nota implementativa:** l'handler Alexa deve inviare anche gli header
`CF-Access-Client-Id` e `CF-Access-Client-Secret`. Finché questa modifica non è
stata verificata e pubblicata, il relay non è pronto per l'uso.

## 5. Test prima di collegare Alexa

1. Da una rete esterna, chiamare `/v1/health` senza credenziali: Access deve negare.
2. Con Service Token ma senza Bearer Jarvis: il gateway deve rispondere 401.
3. Con entrambe le credenziali: `/v1/health` deve rispondere 200.
4. Provare `POST /v1/chat` con una domanda innocua e verificare la risposta.
5. Spegnere Jarvis: Alexa deve ricevere un messaggio generico di indisponibilità.
6. Revocare e rigenerare entrambi i segreti dopo ogni sospetta esposizione.

## Limiti e sicurezza

- Il Mac deve restare acceso, connesso e con Jarvis avviato.
- La Skill non sostituisce la wake word Alexa: sugli Echo standard si usa
  “Alexa, apri Jarvis”.
- Il gateway espone solo chat e health; non aggiungere endpoint shell o comandi
  arbitrari.
- Applicare rate limiting e limiti di spesa/timeout lato Cloudflare e AWS.
- Il tunnel non rende il Core disponibile se il Mac è spento.
- Questa guida non crea il tunnel, non configura il dominio e non distribuisce
  la Skill: sono operazioni da completare negli account Cloudflare/AWS dell'utente.
