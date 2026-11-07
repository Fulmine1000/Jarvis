"""Read-only macOS security posture checks."""
from __future__ import annotations
import platform
import re
import subprocess

_CONTROLLI = (
    ("Firewall applicazioni", ("/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate")),
    ("FileVault", ("/usr/bin/fdesetup", "status")),
    ("Gatekeeper", ("/usr/sbin/spctl", "--status")),
    ("System Integrity Protection", ("/usr/bin/csrutil", "status")),
)
_TIMEOUT_SECONDI = 4

def _classifica(nome, testo):
    valore = str(testo or "").strip().lower()
    if not valore:
        return "non verificabile"
    if nome == "Firewall applicazioni":
        if re.search(r"\bstate\s*=\s*0\b|\bfirewall\s+is\s+disabled\b", valore):
            return "disattivo"
        if re.search(r"\bstate\s*=\s*1\b|\bfirewall\s+is\s+enabled\b", valore):
            return "attivo"
    elif nome == "FileVault":
        if re.search(r"\bfilevault\s+is\s+off\b", valore):
            return "disattivo"
        if re.search(r"\bfilevault\s+is\s+on\b", valore):
            return "attivo"
    elif nome == "Gatekeeper":
        if "assessments disabled" in valore:
            return "disattivo"
        if "assessments enabled" in valore:
            return "attivo"
    elif nome == "System Integrity Protection":
        if re.search(r"\bstatus\s*:\s*disabled\b", valore):
            return "disattivo"
        if re.search(r"\bstatus\s*:\s*enabled\b", valore):
            return "attivo"
    return "non verificabile"

def controlla_postura_mac(sistema=None, runner=None):
    """Controlla quattro protezioni macOS senza modificare le impostazioni."""
    sistema = sistema or platform.system()
    controlli = []
    if sistema != "Darwin":
        for nome, _ in _CONTROLLI:
            controlli.append({"nome": nome, "stato": "non applicabile",
                              "dettaglio": "Controllo disponibile solo su macOS."})
        return {"ok": True, "sistema": sistema, "controlli": controlli,
                "nota": "Nessuna modifica è stata eseguita."}

    esegui = runner or subprocess.run
    for nome, argomenti in _CONTROLLI:
        try:
            risultato = esegui(argomenti, capture_output=True, text=True,
                               timeout=_TIMEOUT_SECONDI, check=False, shell=False)
            testo = "\n".join((getattr(risultato, "stdout", "") or "",
                               getattr(risultato, "stderr", "") or ""))
            stato = _classifica(nome, testo)
            if stato == "non verificabile":
                dettaglio = "Output assente o non riconosciuto; stato non dedotto."
            elif stato == "attivo":
                dettaglio = "Il comando di sistema segnala la protezione attiva."
            else:
                dettaglio = "Il comando di sistema segnala la protezione disattiva."
        except (OSError, subprocess.SubprocessError):
            stato = "non verificabile"
            dettaglio = "Comando non disponibile o tempo massimo superato."
        controlli.append({"nome": nome, "stato": stato, "dettaglio": dettaglio})

    return {"ok": True, "sistema": sistema, "controlli": controlli,
            "nota": ("Verifica read-only. Un risultato non verificabile non significa "
                     "che la protezione sia disattivata; questo controllo non certifica "
                     "la sicurezza complessiva del Mac.")}
