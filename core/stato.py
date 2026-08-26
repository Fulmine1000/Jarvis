import os
import platform
import shutil
import time

try:
    import psutil
except ImportError:
    psutil = None


class StatoJarvis:
    """Raccoglie lo stato hardware e software senza dipendenze obbligatorie."""

    def __init__(self):
        self.nome = "Monitor Sistema"
        self.avvio = time.time()

    def sistema_operativo(self):
        return {
            "sistema": platform.system(),
            "versione": platform.version(),
            "architettura": platform.machine(),
            "hostname": platform.node(),
        }

    def cpu(self):
        if psutil:
            return {"utilizzo": psutil.cpu_percent(interval=0.1), "core": psutil.cpu_count() or 0}
        return {"utilizzo": "Non disponibile", "core": "Non disponibile"}

    def memoria_ram(self):
        if psutil:
            ram = psutil.virtual_memory()
            return {"totale_GB": round(ram.total / (1024 ** 3), 2), "usata_percentuale": ram.percent, "libera_GB": round(ram.available / (1024 ** 3), 2)}
        return {"ram": "Non disponibile"}

    def disco(self):
        disco = shutil.disk_usage(os.path.abspath(os.sep))
        return {"totale_GB": round(disco.total / (1024 ** 3), 2), "usato_GB": round((disco.total - disco.free) / (1024 ** 3), 2), "libero_GB": round(disco.free / (1024 ** 3), 2)}

    def batteria(self):
        if psutil:
            try:
                batteria = psutil.sensors_battery()
                if batteria is not None:
                    return {"percentuale": batteria.percent, "collegato": batteria.power_plugged}
            except (OSError, AttributeError):
                pass
        return "Non disponibile"

    def tempo_attivo_secondi(self):
        return max(0, int(time.time() - self.avvio))

    def tempo_attivo(self):
        secondi = self.tempo_attivo_secondi()
        ore, resto = divmod(secondi, 3600)
        minuti, secondi = divmod(resto, 60)
        if ore:
            return f"{ore} ore, {minuti} minuti"
        return f"{minuti} minuti, {secondi} secondi"

    def completo(self):
        return {"sistema": self.sistema_operativo(), "cpu": self.cpu(), "ram": self.memoria_ram(), "disco": self.disco(), "batteria": self.batteria(), "tempo_attivo": self.tempo_attivo()}

    def stato(self):
        return self.completo()
