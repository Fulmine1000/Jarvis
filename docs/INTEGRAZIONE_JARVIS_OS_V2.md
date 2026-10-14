# Integrazione delle funzioni utili di JARVIS-OS-V.2

Questo documento registra l'integrazione nel progetto Jarvis (Fulmine1000/Jarvis) delle idee utili del repository MAL19INDUSTRIES/JARVIS-OS-V.2, evitando una seconda applicazione parallela e mantenendo il punto d'ingresso python jarvis.py.

## Funzioni disponibili in Jarvis

| Area | Stato in Jarvis | Come si usa |
|---|---|---|
| Interfaccia desktop/HUD | Già presente, basata sull'interfaccia Jarvis esistente | python jarvis.py |
| Conversazione e memoria | Già presenti, con backend locale opzionale | Comandi naturali e memoria di Jarvis |
| Comandi di sistema e dispositivi | Già presenti; azioni effettive dipendono da OS, permessi e dispositivi | aiuto, stato sistema e comandi documentati |
| Lettura e ricerca nei file | Integrata, senza eseguire il contenuto dei file | leggi file <percorso>; cerca nel file <percorso> la parola <testo> |
| Riassunto di documenti | Integrato; dipende dal motore IA configurato e dichiara il fallback se non disponibile | riassumi file <percorso> |
| Presentazioni PowerPoint | Integrate, file modificabili e numerazione per evitare sovrascritture | crea presentazione da file <percorso>; crea presentazione da testo <testo> |
| Presentazione su un argomento | Arricchita con risultati web e avvertenze sulle fonti; se la ricerca non riesce, produce una scaletta iniziale esplicitamente non documentata | crea presentazione su <argomento> |
| Ricerca online | Integrata con risultati, estratti e URL; non richiede chiavi API o dipendenze Python aggiuntive | cerca sul web <argomento>; cerca online <argomento>; ricerca web <argomento> |
| Plugin, automazioni e sicurezza | Già presenti; le operazioni sensibili continuano a seguire le protezioni Jarvis | Consultare docs/COMANDI.md |

## Scelte di compatibilità

Non è stata copiata l'applicazione sorgente per intero: ciò avrebbe creato una seconda interfaccia, duplicato il kernel e rischiato di rompere le funzionalità già esistenti. Jarvis conserva il suo HUD e la sua architettura Python.

Non sono stati resi obbligatori Gemini Live, una chiave API cloud, PyQt6 aggiuntivo, Docker, PostgreSQL, Redis, una web app Next.js o servizi multiutente. Questi componenti appartengono a un'architettura desktop/cloud diversa e non sono necessari per le funzioni locali integrate. La ricerca web è un'azione esplicita e richiede Internet; i contenuti remoti devono essere verificati e non sono trattati come istruzioni operative.

La creazione PowerPoint richiede il pacchetto opzionale indicato in requirements-presentazioni.txt. L'estrazione PDF/DOCX richiede requirements-documenti.txt. Le dipendenze opzionali restano separate per preservare l'installazione base e la compatibilità con il Mac Intel datato.

## Verifica

Le modifiche sono accompagnate da test offline e dalla GitHub Actions CI su Python 3.11, 3.12 e 3.13. Il risultato dell'ultima esecuzione va verificato nella pagina Actions del repository; il fatto che il codice sia stato inviato su master non equivale a una verifica su ogni Mac o dispositivo reale.
