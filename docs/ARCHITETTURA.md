# Architettura J.A.R.V.I.S. Definitive Edition

## Obiettivo

J.A.R.V.I.S. è progettato con un **Core indipendente dal dispositivo**. Il cervello di Jarvis (kernel, memoria, personalità, dialogo, capacità e sicurezza) non dipende dall'interfaccia o dall'hardware che lo utilizza.

Un computer, telefono o robot può diventare un **host** tramite un adapter compatibile. In questo modo è possibile portare l'identità operativa di Jarvis su più piattaforme senza riscrivere il Core.

## Struttura

```text
Jarvis/
├── main.py                 # avvio ufficiale
├── core/                   # cervello e servizi centrali
│   ├── kernel.py
│   ├── portabilita.py      # registry e adapter degli host IA
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
├── dispositivi/            # computer, telefono, rete, Bluetooth, TV, smart home e robot IA
│   └── robot_ia.py         # adapter generico per robot con IA
├── moduli/                 # adattatori del kernel
├── personalita/            # personalità e tono conversazionale
├── plugin/                 # estensioni caricabili
├── config/                 # configurazione persistente
├── tests/                  # test automatici
├── docs/                   # documentazione
└── scripts/                # strumenti di avvio/manutenzione
```

## Architettura Core → Host

```text
                  ┌───────────────────────┐
                  │     JARVIS CORE       │
                  │ Kernel / Memoria / AI │
                  │ Personalità / Comandi │
                  └───────────┬───────────┘
                              │
                    AdapterDispositivoIA
                              │
          ┌───────────────────┼──────────────────┐
          │                   │                  │
       MacBook             Android          Robot con IA
          │                   │                  │
       HUD/Voce           Voce/UI        Voce/Sensori/Motori
```

Il Core conserva l'intelligenza e la memoria. L'host fornisce invece le periferiche e le capacità fisiche disponibili. Un robot reale richiede un adapter specifico per il proprio SDK/API.

## Trasferimento dell'identità

`GestorePortabilitaIA` permette di registrare un host, collegarlo, attivare Jarvis e trasferire una configurazione di identità non sensibile.

La memoria personale non viene copiata automaticamente sul dispositivo esterno: rimane nel Core di Jarvis e può essere resa disponibile solo tramite un'integrazione autorizzata.

## Flusso di avvio

`main.py` → `KernelJarvis` → moduli → voce/dispositivi/memoria → diagnostica → HUD.

Tkinter resta nel thread principale. Il riconoscimento vocale, le automazioni e le attività pianificate usano thread separati. Il kernel espone uno stato unico utilizzato dall'HUD.

## Principi

- Il Core di Jarvis è indipendente dal dispositivo.
- Gli host esterni comunicano con il Core tramite adapter sostituibili.
- Un robot non viene considerato compatibile senza un adapter per il suo hardware/API.
- Nessuna esecuzione arbitraria di shell tramite comandi vocali.
- Dipendenze audio e AI sono opzionali quando possibile.
- Le integrazioni mancanti non impediscono la modalità testuale.
- I dati personali e i log locali non devono essere inseriti nel repository pubblico.
