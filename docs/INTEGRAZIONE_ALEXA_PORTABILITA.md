# Integrazione Alexa e portabilita multi-dispositivo

## Architettura

Alexa deve essere un terminale vocale remoto di Jarvis, non un luogo in cui installare il Kernel Python. Il Core mantiene identita, memoria, autorizzazioni e logica; Mac, Alexa e Android sono interfacce con capacita differenti.

Il trasferimento della sessione cambia il terminale principale, non sposta fisicamente il processo Python o il database sul firmware dell'Echo.

## Stato attuale

- Il repository contiene gia un registro astratto di host IA in `core/portabilita.py`.
- L'Android Agent esistente supporta una sessione locale limitata e un bridge USB verso il Mac.
- Non esiste ancora una Skill Alexa collegata al Core.
- L'agente Android e documentato per Huawei P Smart 2019: il Samsung Galaxy M55 richiede una verifica dedicata.

## Prossime componenti

1. Skill Alexa italiana che inoltra richieste a un gateway HTTPS.
2. Gateway nel Core con autenticazione, limiti, controllo input e allowlist di comandi.
3. Adapter Alexa nel registro di portabilita, con stato, health-check e timeout.
4. Adapter Android dedicato al Samsung, mantenendo le funzioni offline disponibili.
5. Sincronizzazione dello stato conversazionale sul Core, senza copiare automaticamente ricordi personali sui terminali.

## Limiti Alexa

Sugli Echo standard la parola di attivazione resta Alexa. La Skill si avvia con una frase come «Alexa, apri Jarvis» e poi riceve il comando. Non e possibile installare liberamente il Kernel Python nel firmware Echo o sostituire la wake word.

## Sicurezza

Il gateway deve usare HTTPS e un segreto conservato fuori dal repository. Non esporre il Mac direttamente a Internet con port forwarding improvvisato. Inoltrare solo il testo del comando necessario; non trasferire l'intero database della memoria. Le azioni sensibili richiedono autorizzazione esplicita e conferma.

## Attivazione

La creazione della Skill, il collegamento alla funzione cloud e l'autorizzazione del dispositivo richiedono l'account Amazon Developer/AWS e l'intervento del proprietario. Fino a quel momento la documentazione descrive l'architettura, non un'integrazione gia operativa.

## Primo componente operativo: gateway locale autenticato

Il Core include ora `core/gateway_remoto.py`, integrato nel Kernel ma disattivato per impostazione predefinita.

Per abilitarlo sul Mac:

1. Generare un token casuale di almeno 32 caratteri e conservarlo fuori da Git.
2. Impostare `JARVIS_GATEWAY_ENABLED=1` e `JARVIS_GATEWAY_TOKEN` nell'ambiente del processo Jarvis.
3. Avviare Jarvis normalmente.

Esempio macOS/Linux (il token viene generato e mostrato una sola volta nel terminale):

```bash
export JARVIS_GATEWAY_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export JARVIS_GATEWAY_ENABLED=1
python3 jarvis.py
```

Su Windows PowerShell:

```powershell
$env:JARVIS_GATEWAY_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:JARVIS_GATEWAY_ENABLED = "1"
python jarvis.py
```

Il gateway ascolta esclusivamente su `127.0.0.1:8767`. Espone solo:

- `GET /v1/health`: stato minimo del Core, autenticato.
- `POST /v1/chat`: invio di testo al motore conversazionale centrale, autenticato.

Esempio di richiesta locale:

```bash
curl -H "Authorization: Bearer $JARVIS_GATEWAY_TOKEN" \
     -H "Content-Type: application/json" \
     http://127.0.0.1:8767/v1/chat \
     -d '{"text":"Ciao Jarvis"}'
```

Sono rifiutati token mancanti/deboli, richieste non autenticate, JSON fuori schema, payload oltre 8 KiB e testo oltre 2.000 caratteri. Non esiste un endpoint per eseguire shell o comandi arbitrari. Il gateway viene arrestato insieme al Kernel. L'autenticazione non sostituisce TLS: il binding loopback è intenzionale. Per Alexa o accesso da fuori Mac serve ancora un tunnel/reverse proxy HTTPS autenticato e configurato separatamente.

## Stato di questa fase

- Implementato nel Core: gateway locale autenticato e opt-in.
- Non ancora collegati: Alexa Skill, tunnel HTTPS pubblico, adapter Android M55 e sincronizzazione completa della sessione.
- Nessun cambiamento all'HUD.
