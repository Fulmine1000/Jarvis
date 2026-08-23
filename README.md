# J.A.R.V.I.S.

Assistente personale modulare in Python, progettato come **Jarvis 3.x Definitive Edition**: voce, memoria, personalità, dispositivi, smart home, diagnostica e automazioni locali in un'unica architettura.

## Cosa fa

### Conversazione e voce
- Wake word e riconoscimento vocale tramite Vosk quando microfono e modello sono disponibili.
- Sintesi vocale con Piper quando installato, con fallback nativo macOS/Linux.
- Modalità testo sempre disponibile quando l'audio non è configurato.
- Personalità formale, naturale e contestuale in italiano.
- Risposte per saluti, identità, ringraziamenti, richieste di aiuto e comandi non riconosciuti.
- Memoria e contesto delle conversazioni tramite i moduli dedicati.

### Capacità operative
- Ora, data e diagnostica del computer.
- CPU, RAM e disco tramite `psutil` quando disponibile.
- Calcolatrice sicura senza esecuzione arbitraria di codice.
- Apertura di applicazioni e cartelle.
- Apertura di siti e ricerca web nel browser predefinito.
- Meteo online tramite servizio HTTP pubblico.
- Screenshot su sistemi compatibili.
- Volume e mute su macOS.
- Timer con notifica su macOS.

### Dispositivi
- Gestione modulare di computer, telefono, Bluetooth, rete e console.
- Controllo Android tramite i moduli ADB disponibili.
- Trasferimento della sessione tra base e telefono quando i dispositivi sono configurati.
- TV LG webOS con il modulo dedicato.
- Smart home con il modulo dedicato.
- Sistema plugin per estendere Jarvis senza riscrivere il kernel.

### Sicurezza
Le operazioni protette passano dal modulo di sicurezza e richiedono conferma esplicita. Le nuove capacità operative non eseguono comandi shell arbitrari provenienti dalla voce.

## Avvio

```bash
python3 main.py
```

Per la modalità di avvio già predisposta:

```bash
./scripts/start_jarvis.sh
```

## Test

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

La CI compila il progetto, verifica le dipendenze ed esegue l'intera suite di test su Python 3.11, 3.12 e 3.13.

## Nota importante

L'architettura è stata portata verso un Jarvis cinematografico, ma le funzioni fisicamente possibili dipendono dall'hardware, dal sistema operativo, dai dispositivi collegati, dai permessi e dai servizi esterni. Funzioni come controllo di una casa, telefono o TV richiedono quindi la relativa integrazione reale: il software non può creare hardware o permessi che non esistono.

## Architettura

- `core/` — kernel, configurazione, eventi, logging e capacità operative.
- `comandi/` — linguaggio naturale e router dei comandi.
- `memoria/` — profilo, ricordi, contesto e conversazioni.
- `personalita/` — comportamento conversazionale.
- `voce/` — ascolto, wake word, riconoscimento e sintesi.
- `dispositivi/` — integrazioni hardware e rete.
- `moduli/` — moduli caricati dal kernel.
- `plugin/` — estensioni.
- `tests/` — test automatici.
