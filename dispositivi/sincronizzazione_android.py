from __future__ import annotations

"""Sincronizzazione automatica del J.A.R.V.I.S. Android Agent.

La repository GitHub resta la sorgente del codice. Il Mac compila l'Android
Agent e, quando il Huawei è collegato e autorizzato via ADB, installa
automaticamente l'APK aggiornato.

Modalità:
    python3 -m dispositivi.sincronizzazione_android --once
    python3 -m dispositivi.sincronizzazione_android --watch

Il watcher non trasferisce il Core Python del Mac sul telefono: sincronizza
solo l'app Android presente in ``android-agent``. Le modifiche al Jarvis
principale che devono arrivare sul telefono devono quindi essere riflesse
anche nel codice dell'Android Agent.
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


PACKAGE = "com.fulmine1000.jarvis.agent"
ACTIVITY = f"{PACKAGE}/.MainActivity"
HUAWEI_MODEL = "POT_LX1"
HUAWEI_PRODUCT = "POT-LX1EEA"
APK_RELATIVE = Path("app/build/outputs/apk/debug/app-debug.apk")

# File e directory di build non fanno parte del sorgente da osservare.
IGNORATI = {
    ".gradle",
    ".idea",
    "build",
    "captures",
    "local.properties",
}


class SincronizzatoreAndroid:
    def __init__(self, root: Path | None = None, intervallo: float = 2.0) -> None:
        self.root = (root or Path(__file__).resolve().parents[1]).resolve()
        self.android_root = self.root / "android-agent"
        self.apk = self.android_root / APK_RELATIVE
        self.intervallo = max(0.5, intervallo)
        self.ultimo_snapshot: tuple | None = None
        self.ultimo_apk_hash: str | None = None
        self.ultimo_device: str | None = None

    def log(self, messaggio: str) -> None:
        print(f"[JARVIS ANDROID SYNC] {messaggio}", flush=True)

    def verifica_struttura(self) -> None:
        if not self.android_root.is_dir():
            raise RuntimeError(f"Cartella Android Agent non trovata: {self.android_root}")
        gradlew = self.android_root / "gradlew"
        if not gradlew.exists():
            raise RuntimeError(f"gradlew non trovato: {gradlew}")
        if not os.access(gradlew, os.X_OK):
            try:
                gradlew.chmod(gradlew.stat().st_mode | 0o111)
            except OSError as exc:
                raise RuntimeError(f"Impossibile rendere eseguibile gradlew: {exc}") from exc

    def adb(self) -> str:
        adb = shutil.which("adb")
        if not adb:
            raise RuntimeError("ADB non trovato nel PATH. Verificare con: which adb")
        return adb

    def dispositivi(self) -> list[dict[str, str]]:
        adb = self.adb()
        result = subprocess.run(
            [adb, "devices", "-l"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "adb devices ha restituito un errore")

        trovati: list[dict[str, str]] = []
        for raw in result.stdout.splitlines()[1:]:
            line = raw.strip()
            if not line or line.startswith("*"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            data = {"id": parts[0], "state": parts[1]}
            for part in parts[2:]:
                if ":" in part:
                    key, value = part.split(":", 1)
                    data[key] = value
            trovati.append(data)
        return trovati

    def huawei_collegato(self) -> dict[str, str] | None:
        autorizzati = [d for d in self.dispositivi() if d.get("state") == "device"]
        if not autorizzati:
            return None

        # Preferiamo il Huawei previsto. Se è l'unico dispositivo autorizzato,
        # lo accettiamo comunque per mantenere compatibile il setup già fatto.
        for device in autorizzati:
            if device.get("model") == HUAWEI_MODEL or device.get("product") == HUAWEI_PRODUCT:
                return device
        if len(autorizzati) == 1:
            return autorizzati[0]
        return None

    def snapshot_sorgenti(self) -> tuple:
        """Restituisce uno snapshot stabile del solo Android Agent sorgente."""
        if not self.android_root.exists():
            return ()

        entries: list[tuple[str, int, int]] = []
        for path in sorted(self.android_root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(self.android_root)
            if any(part in IGNORATI for part in rel.parts):
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            entries.append((rel.as_posix(), stat.st_mtime_ns, stat.st_size))
        return tuple(entries)

    def hash_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def build(self) -> None:
        self.verifica_struttura()
        self.log("Compilazione dell'Android Agent in corso...")
        result = subprocess.run(
            ["./gradlew", "assembleDebug"],
            cwd=self.android_root,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Build Android fallita (codice {result.returncode}).")
        if not self.apk.exists():
            raise RuntimeError(f"Build terminata senza APK: {self.apk}")
        self.log(f"APK pronto: {self.apk}")

    def install(self, device_id: str) -> None:
        adb = self.adb()
        self.log(f"Installazione su Huawei {device_id}...")
        result = subprocess.run(
            [adb, "-s", device_id, "install", "-r", str(self.apk)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            details = (result.stderr or result.stdout).strip()
            raise RuntimeError(f"Installazione APK fallita: {details}")

        start = subprocess.run(
            [adb, "-s", device_id, "shell", "am", "start", "-n", ACTIVITY],
            text=True,
            capture_output=True,
            check=False,
        )
        if start.returncode != 0:
            details = (start.stderr or start.stdout).strip()
            raise RuntimeError(f"Avvio J.A.R.V.I.S. sul telefono fallito: {details}")

        self.ultimo_device = device_id
        self.ultimo_apk_hash = self.hash_file(self.apk)
        self.log("J.A.R.V.I.S. Android Agent aggiornato e avviato sul Huawei.")

    def sincronizza(self, motivo: str = "modifica rilevata") -> bool:
        device = self.huawei_collegato()
        if not device:
            self.log("Huawei non collegato/autorizzato. Sincronizzazione rimandata.")
            return False

        apk_hash = self.hash_file(self.apk) if self.apk.exists() else None
        snapshot = self.snapshot_sorgenti()

        # Se il codice è invariato e lo stesso APK è già installato tramite
        # questo watcher, non ricompiliamo inutilmente.
        if snapshot == self.ultimo_snapshot and apk_hash == self.ultimo_apk_hash:
            return True

        self.log(f"Sincronizzazione: {motivo}.")
        self.build()
        self.install(device["id"])
        self.ultimo_snapshot = snapshot
        return True

    def once(self) -> int:
        self.verifica_struttura()
        self.ultimo_snapshot = self.snapshot_sorgenti()
        device = self.huawei_collegato()
        if not device:
            self.log("Nessun Huawei autorizzato trovato con ADB.")
            self.log("Collega il telefono, sbloccalo e accetta 'Consenti debug USB'.")
            return 2

        self.ultimo_snapshot = None
        try:
            self.sincronizza("sincronizzazione richiesta")
            return 0
        except Exception as exc:
            self.log(f"ERRORE: {exc}")
            return 1

    def watch(self) -> int:
        self.verifica_struttura()
        self.log(f"Watcher attivo sulla repository: {self.root}")
        self.log("Controllo automatico del Huawei via USB/ADB attivo.")

        snapshot = self.snapshot_sorgenti()
        connected_last = False
        pending_sync = True
        first_cycle = True

        while True:
            try:
                device = self.huawei_collegato()
                connected = device is not None

                if connected and not connected_last:
                    self.log(f"Huawei collegato: {device['id']}")
                    pending_sync = True

                if not connected and connected_last:
                    self.log("Huawei scollegato. Jarvis sul telefono continua a usare la versione locale/offline.")

                current_snapshot = self.snapshot_sorgenti()
                if current_snapshot != snapshot:
                    snapshot = current_snapshot
                    pending_sync = True
                    self.log("Modifica rilevata nell'Android Agent: aggiornamento in coda.")

                if connected and pending_sync:
                    # Piccolo debounce: evita di compilare mentre Git/editor sta
                    # ancora scrivendo più file consecutivamente.
                    time.sleep(1.0)
                    stable_snapshot = self.snapshot_sorgenti()
                    if stable_snapshot != snapshot:
                        snapshot = stable_snapshot
                        continue
                    try:
                        self.ultimo_snapshot = None
                        self.sincronizza("nuova versione disponibile")
                        pending_sync = False
                    except Exception as exc:
                        self.log(f"Sincronizzazione fallita: {exc}")
                        # Ritenta al ciclo successivo senza perdere la modifica.

                connected_last = connected
                first_cycle = False
                time.sleep(self.intervallo)
            except KeyboardInterrupt:
                self.log("Watcher arrestato.")
                return 0
            except Exception as exc:
                self.log(f"Controllo USB/ADB: {exc}")
                time.sleep(max(2.0, self.intervallo))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincronizza automaticamente Jarvis Android con il Huawei via ADB.")
    parser.add_argument("--watch", action="store_true", help="rimane attivo e sincronizza ogni modifica")
    parser.add_argument("--once", action="store_true", help="esegue una sola sincronizzazione")
    parser.add_argument("--interval", type=float, default=2.0, help="secondi tra i controlli in modalità watch")
    args = parser.parse_args()

    if not args.watch and not args.once:
        args.watch = True

    sync = SincronizzatoreAndroid(intervallo=args.interval)
    return sync.watch() if args.watch else sync.once()


if __name__ == "__main__":
    raise SystemExit(main())
