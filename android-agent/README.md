# J.A.R.V.I.S. Android Agent

Agente verticale per Huawei P Smart 2019 (POT-LX1 / Android 10 / arm64-v8a).

## Architettura

- Mac ↔ USB ↔ ADB ↔ Android agent
- nessun IP del telefono richiesto
- `adb forward` per il canale Mac → telefono
- `adb reverse` per il canale telefono → Mac
- la sessione locale rimane sul telefono quando il cavo viene scollegato
- il telefono può continuare a riconoscere la voce offline con Vosk
- quando il telefono viene ricollegato, il monitor USB del Mac ripristina il bridge
- con USB collegato, la wake word `Jarvis` sul telefono richiede il ritorno della sessione al Mac
- il Core Python completo di Jarvis **non viene copiato** sul telefono: il telefono contiene solo l'Android Agent e le funzioni locali necessarie

## Sincronizzazione automatica Mac → Huawei

La repository GitHub resta la sorgente del codice. L'Android Agent viene compilato sul Mac e installato sul Huawei solo quando il dispositivo è collegato e autorizzato via ADB.

Il watcher è in `dispositivi/sincronizzazione_android.py` e osserva esclusivamente `android-agent/`. Quando rileva una modifica:

1. aspetta che i file siano stabili;
2. esegue `./gradlew assembleDebug`;
3. installa l'APK con `adb install -r`;
4. riavvia l'Android Agent sul Huawei.

Se il Huawei è scollegato, l'aggiornamento resta in coda. Quando viene ricollegato, il watcher lo sincronizza automaticamente.

Avvio continuo:

```bash
cd ~/Desktop/Jarvis
python3 -m dispositivi.sincronizzazione_android --watch
```

Una sola sincronizzazione:

```bash
cd ~/Desktop/Jarvis
python3 -m dispositivi.sincronizzazione_android --once
```

Per interrompere il watcher: `Ctrl+C`.

> Le modifiche al Jarvis principale che devono essere disponibili anche sul telefono devono essere riflesse anche nel codice dell'Android Agent. Il watcher non trasferisce automaticamente il Core Python del Mac sul telefono.

## Build sul Mac

Il Mac del progetto usa Java 11. Il progetto include un bootstrap Gradle compatibile con Java 11, quindi non serve installare il comando `gradle` globalmente.

```bash
cd ~/Desktop/Jarvis/android-agent
chmod +x gradlew
./gradlew assembleDebug
```

Al primo build viene scaricato automaticamente il modello ufficiale Vosk italiano `vosk-model-small-it-0.22` e inserito nell'APK come asset. Il modello piccolo è progettato per applicazioni mobile/Android ed è circa 48 MB. Vosk supporta il riconoscimento offline su Android.

Dopo la compilazione:

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb shell am start -n com.fulmine1000.jarvis.agent/.MainActivity
```

## Verifica ADB

```bash
adb devices
adb shell getprop ro.product.model
adb shell getprop ro.build.version.release
adb shell getprop ro.product.cpu.abi
```

Per il dispositivo previsto i valori sono POT-LX1, Android 10 e arm64-v8a.

## Vosk offline

Il modello viene copiato dall'APK alla memoria privata dell'app al primo avvio della sessione. Il microfono usa `AudioRecord` a 16 kHz mono PCM e Vosk esegue il riconoscimento localmente, senza Wi-Fi e senza il servizio di riconoscimento vocale di Google.

La prima volta Android chiederà il permesso microfono. Dopo l'autorizzazione, quando la sessione è attiva il pannello mostra `VOSK: OFFLINE READY` e il canale vocale mostra `LISTENING / VOSK OFFLINE`.
