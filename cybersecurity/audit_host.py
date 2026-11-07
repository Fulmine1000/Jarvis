"""Audit locale read-only di processi, avvii automatici e permessi sensibili.

Questi controlli raccolgono metadati locali: non terminano processi, non
disabilitano servizi, non modificano permessi e non eseguono file plist.
"""
from __future__ import annotations

import os
import plistlib
import platform
import stat
from pathlib import Path


_LIMITE_PROCESSI = 300
_LIMITE_LISTENER = 150
_LIMITE_AVVII = 200
_MAX_PLIST_BYTES = 1024 * 1024
_NOMI_CHIAVI_PRIVATE = (
    "id_rsa",
    "id_ecdsa",
    "id_ed25519",
    "id_dsa",
    "id_ed25519_sk",
)


def _percorso_sospetto(percorso):
    valore = str(percorso or "").replace("\\", "/").lower()
    parti = [parte for parte in valore.split("/") if parte]
    return (
        "downloads" in parti
        or "download" in parti
        or "tmp" in parti
        or "temp" in parti
        or valore.startswith("/private/var/folders/")
    )


def audit_processi_servizi(psutil_mod=None):
    """Elenca processi e socket in ascolto senza inviare traffico di rete."""
    if psutil_mod is None:
        try:
            import psutil as psutil_mod
        except ImportError:
            return {
                "ok": False,
                "errore": "psutil non è disponibile; installare la dipendenza prevista da Jarvis.",
                "processi_esaminati": 0,
                "indicatori": [],
                "porte_in_ascolto": [],
                "errori": [],
            }
    if psutil_mod is False:
        return {
            "ok": False,
            "errore": "psutil non è disponibile.",
            "processi_esaminati": 0,
            "indicatori": [],
            "porte_in_ascolto": [],
            "errori": [],
        }

    processi_esaminati = 0
    processi_non_letti = 0
    nomi_per_pid = {}
    indicatori = []
    porte_in_ascolto = []
    errori = []

    try:
        for processo in psutil_mod.process_iter(["pid", "name", "exe"]):
            if processi_esaminati >= _LIMITE_PROCESSI:
                errori.append("Raggiunto il limite massimo di processi esaminati.")
                break
            try:
                info = processo.info
                pid = info.get("pid")
                nome = info.get("name") or "processo senza nome"
                eseguibile = info.get("exe") or ""
                processi_esaminati += 1
                if pid is not None:
                    nomi_per_pid[pid] = nome
                if eseguibile and _percorso_sospetto(eseguibile):
                    indicatori.append({
                        "pid": pid,
                        "nome": nome,
                        "tipo": "eseguibile in percorso temporaneo o Download",
                        "percorso": eseguibile,
                        "gravita": "da verificare",
                    })
            except Exception:
                # Un processo può terminare o negare l'accesso mentre viene letto.
                processi_non_letti += 1
                continue
        if processi_non_letti:
            errori.append(
                f"{processi_non_letti} processi non leggibili: inventario parziale."
            )
    except Exception as errore:
        errori.append("Elenco processi parziale: " + type(errore).__name__)

    try:
        connessioni = psutil_mod.net_connections(kind="inet")
        stato_listen = getattr(psutil_mod, "CONN_LISTEN", "LISTEN")
        for connessione in connessioni:
            if len(porte_in_ascolto) >= _LIMITE_LISTENER:
                errori.append("Raggiunto il limite massimo di socket in ascolto.")
                break
            if getattr(connessione, "status", None) != stato_listen:
                continue
            indirizzo = getattr(connessione, "laddr", None)
            if not indirizzo:
                continue
            ip = getattr(indirizzo, "ip", None)
            porta = getattr(indirizzo, "port", None)
            if ip is None and isinstance(indirizzo, tuple) and len(indirizzo) >= 2:
                ip, porta = indirizzo[0], indirizzo[1]
            if ip is None or porta is None:
                continue
            esposto = str(ip) in ("0.0.0.0", "::", "")
            pid = getattr(connessione, "pid", None)
            porte_in_ascolto.append({
                "indirizzo": str(ip),
                "porta": int(porta),
                "pid": pid,
                "processo": nomi_per_pid.get(pid, "processo non identificato"),
                "esposto_su_tutte_le_interfacce": esposto,
                "gravita": "da verificare" if esposto else "informativo",
            })
    except Exception as errore:
        errori.append("Socket in ascolto non completamente leggibili: " + type(errore).__name__)

    return {
        "ok": not bool(errori),
        "sistema": platform.system(),
        "processi_esaminati": processi_esaminati,
        "processi_non_letti": processi_non_letti,
        "indicatori": indicatori[:100],
        "porte_in_ascolto": porte_in_ascolto,
        "errori": errori,
        "nota": (
            "Inventario locale read-only: nessun processo terminato e nessun "
            "pacchetto inviato. Un percorso insolito o una porta in ascolto "
            "non dimostrano da soli un'attività malevola."
        ),
    }


def audit_avvii_mac(home=None, roots=None):
    """Esamina i plist LaunchAgents/LaunchDaemons senza avviare o fermare job."""
    if roots is None:
        if platform.system() != "Darwin":
            return {
                "ok": True,
                "applicabile": False,
                "elementi": [],
                "errori": [],
                "nota": "Inventario LaunchAgents disponibile solo su macOS.",
            }
        base_home = Path(home).expanduser() if home is not None else Path.home()
        roots = (
            base_home / "Library" / "LaunchAgents",
            Path("/Library/LaunchAgents"),
            Path("/Library/LaunchDaemons"),
            Path("/System/Library/LaunchAgents"),
            Path("/System/Library/LaunchDaemons"),
        )

    elementi = []
    errori = []
    for radice in roots:
        directory = Path(radice).expanduser()
        if not directory.is_dir():
            continue
        try:
            plist_files = sorted(directory.glob("*.plist"))
        except OSError as errore:
            errori.append(f"{directory}: {type(errore).__name__}")
            continue
        for percorso in plist_files:
            if len(elementi) >= _LIMITE_AVVII:
                errori.append("Raggiunto il limite massimo di elementi di avvio.")
                break
            try:
                if percorso.is_symlink():
                    errori.append(f"{percorso}: collegamento simbolico ignorato")
                    continue
                if percorso.stat().st_size > _MAX_PLIST_BYTES:
                    errori.append(f"{percorso}: superato il limite di 1 MB per plist")
                    continue
                with percorso.open("rb") as file:
                    dati = plistlib.load(file)
                if not isinstance(dati, dict):
                    raise ValueError("plist non contiene un dizionario")
                programma = dati.get("Program")
                argomenti = dati.get("ProgramArguments")
                if not programma and isinstance(argomenti, list) and argomenti:
                    programma = argomenti[0]
                programma = str(programma) if programma else ""
                indicatori = []
                if programma and _percorso_sospetto(programma):
                    indicatori.append("percorso download o temporaneo")
                if programma.startswith("/") and not Path(programma).exists():
                    indicatori.append("programma indicato non trovato")
                elementi.append({
                    "file": str(percorso),
                    "etichetta": str(dati.get("Label") or percorso.stem),
                    "programma": programma,
                    "avvio_automatico": bool(dati.get("RunAtLoad", False)),
                    "mantieni_attivo": bool(dati.get("KeepAlive", False)),
                    "indicatori": indicatori,
                })
            except (OSError, ValueError, plistlib.InvalidFileException) as errore:
                errori.append(f"{percorso}: {type(errore).__name__}")
    return {
        "ok": not bool(errori),
        "applicabile": True,
        "elementi": elementi,
        "errori": errori,
        "nota": (
            "Inventario statico dei plist: nessun job avviato, fermato o modificato. "
            "Gli elementi sconosciuti vanno verificati prima di rimuoverli."
        ),
    }


def audit_permessi_sensibili(home=None):
    """Controlla i permessi POSIX di directory SSH e file segreti comuni."""
    base_home = Path(home).expanduser() if home is not None else Path.home()
    percorsi = [
        (base_home / ".ssh", "directory_ssh"),
        *[(base_home / ".ssh" / nome, "chiave_privata") for nome in _NOMI_CHIAVI_PRIVATE],
        (base_home / ".aws" / "credentials", "credenziali_aws"),
        (base_home / ".env", "file_segreti"),
    ]
    controlli = []
    for percorso, tipo in percorsi:
        try:
            if not percorso.exists() and not percorso.is_symlink():
                continue
            info = percorso.lstat()
            if stat.S_ISLNK(info.st_mode):
                stato = "collegamento simbolico da verificare"
                dettaglio = "Il percorso è un link simbolico; verificare manualmente la destinazione."
            elif not (stat.S_ISDIR(info.st_mode) if tipo == "directory_ssh" else stat.S_ISREG(info.st_mode)):
                stato = "tipo file inatteso"
                dettaglio = "Il percorso esiste ma non ha il tipo di file previsto."
            else:
                permessi = stat.S_IMODE(info.st_mode)
                if permessi & 0o077:
                    stato = "permessi troppo aperti"
                    dettaglio = f"Permessi POSIX {permessi:04o}; gruppo o altri utenti hanno accesso."
                else:
                    stato = "ok"
                    dettaglio = f"Permessi POSIX {permessi:04o}; nessun accesso a gruppo/altri."
            controlli.append({
                "percorso": str(percorso),
                "tipo": tipo,
                "stato": stato,
                "dettaglio": dettaglio,
            })
        except OSError as errore:
            controlli.append({
                "percorso": str(percorso),
                "tipo": tipo,
                "stato": "non verificabile",
                "dettaglio": type(errore).__name__,
            })

    return {
        "ok": not any(item["stato"] == "non verificabile" for item in controlli),
        "controlli": controlli,
        "nota": (
            "Controllo read-only dei metadati. Jarvis non cambia i permessi; "
            "valutare ogni risultato prima di intervenire."
        ),
    }
