# Controllo del telefono Android tramite voce

Il controllo del telefono riproduce le azioni principali dello Short di riferimento: risvegliare lo schermo, aprire un'app e preparare una chiamata.

## Requisiti

1. Installa Android Platform Tools sul Mac e verifica che `adb` sia nel `PATH`.
2. Collega il telefono Android al Mac tramite USB.
3. Attiva Opzioni sviluppatore e Debug USB sul telefono, quindi accetta la richiesta di autorizzazione ADB.
4. Verifica dal Terminale con `adb devices` che il telefono compaia con stato `device` (non `unauthorized`).

Il controllo è destinato a un solo dispositivo Android autorizzato alla volta, per evitare comandi inviati al telefono sbagliato.

## Comandi vocali

- `sblocca il telefono` / `unlock my phone`: accende lo schermo. Non aggira PIN, password o biometria; l'autenticazione resta manuale.
- `apri YouTube sul telefono` / `open YouTube on my phone`: apre l'app installata.
- `apri JioHotstar sul telefono` / `open JioHotstar in my phone`: apre JioHotstar se il pacchetto è presente e riconosciuto.
- `chiama +39...`: apre il dialer con il numero già inserito; controlla il numero e premi manualmente il pulsante di chiamata.
- `chiama mia sorella` / `call my sister`: apre Contatti per cercare il nome. La chiamata non parte automaticamente e il contatto non viene letto o memorizzato da Jarvis.

Sono previsti alias per YouTube, WhatsApp, Chrome, Spotify, Netflix, Instagram, Telegram, JioHotstar, Impostazioni, Fotocamera, Telefono e Contatti. Per un'altra app, Jarvis prova a individuare un pacchetto installato dal nome.

## Limiti e sicurezza

- La funzione usa ADB via USB; non è un controllo remoto via Internet o Wi-Fi.
- Un'app Android normale non può rimuovere in sicurezza il blocco PIN/biometrico: Jarvis può solo risvegliare lo schermo.
- Le chiamate richiedono sempre una verifica manuale sul telefono.
- Se non c'è un solo dispositivo ADB autorizzato, Jarvis non invia azioni.
- Il controllo non registra lo schermo, l'audio o la rubrica.
