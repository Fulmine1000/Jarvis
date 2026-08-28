# J.A.R.V.I.S. Android Agent

Agente verticale per Huawei P Smart 2019 (POT-LX1 / Android 10 / arm64-v8a).

## Architettura

- Mac ↔ USB ↔ ADB ↔ Android agent
- nessun IP del telefono richiesto
- `adb forward` per il canale Mac → telefono
- `adb reverse` per il canale telefono → Mac
- la sessione rimane sul telefono quando il cavo viene scollegato
- il telefono può continuare a riconoscere la voce offline con Vosk
- quando il telefono viene ricollegato, il monitor USB del Mac ripristina il bridge
- con USB collegato, la wake word `Jarvis` sul telefono richiede il ritorno della sessione al Mac

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
