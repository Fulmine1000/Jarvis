# Architettura J.A.R.V.I.S. Definitive Edition

## Struttura

```text
Jarvis/
├── main.py                 # avvio ufficiale
├── core/                   # kernel e servizi centrali
│   ├── kernel.py
│   ├── diagnostica.py
│   ├── capacita.py
│   ├── dialogo.py
│   ├── automazioni.py
│   ├── visione.py
│   ├── config.py
│   ├── logger.py
│   ├── event_bus.py
│   └── manager.py
├── comandi/                # linguaggio naturale e router
├── memoria/                # profilo, ricordi, conversazioni e database
├── voce/                   # ascolto, Vosk, wake word e sintesi
├── interfaccia/            # HUD animato
├── dispositivi/            # computer, telefono, rete, Bluetooth, TV e smart home
├── moduli/                 # adattatori del kernel
├── personalita/            # personalità e tono conversazionale
├── plugin/                 # estensioni caricabili
├── config/                 # configurazione persistente
├── tests/                  # test automatici
├── docs/                   # documentazione
└── scripts/                # strumenti di avvio/manutenzione
```

## Flusso di avvio

`main.py` → `KernelJarvis` → moduli → voce/dispositivi/memoria → diagnostica → HUD.

Tkinter resta nel thread principale. Il riconoscimento vocale, le automazioni e le attività pianificate usano thread separati. Il kernel espone uno stato unico utilizzato dall'HUD.

## Principi

- Nessuna esecuzione arbitraria di shell tramite comandi vocali.
- Dipendenze audio e AI sono opzionali quando possibile.
- Le integrazioni mancanti non impediscono la modalità testuale.
- Il codice è organizzato per moduli indipendenti e sostituibili.
- I dati personali e i log locali non devono essere inseriti nel repository pubblico.
