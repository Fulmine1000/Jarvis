import json
from pathlib import Path


FILE_DISPOSITIVI = Path(__file__).resolve().parent / "smart_devices.json"


class SmartHomeJarvis:
    """Gestione persistente dei dispositivi Smart Home di Jarvis."""

    def __init__(self):
        self.nome = "Smart Home"
        self.dispositivi = []
        self.carica()

    @staticmethod
    def _percorso_file():
        """Restituisce il percorso del file come Path, anche se sovrascritto come stringa nei test."""
        return Path(FILE_DISPOSITIVI)

    def carica(self):
        percorso = self._percorso_file()
        if percorso.exists():
            try:
                with percorso.open("r", encoding="utf-8") as file:
                    dati = json.load(file)
                self.dispositivi = dati if isinstance(dati, list) else []
            except (OSError, json.JSONDecodeError, TypeError):
                self.dispositivi = []

    def salva(self):
        percorso = self._percorso_file()
        percorso.parent.mkdir(parents=True, exist_ok=True)
        with percorso.open("w", encoding="utf-8") as file:
            json.dump(self.dispositivi, file, indent=4, ensure_ascii=False)

    def aggiungi_dispositivo(self, nome, tipo):
        dispositivo = {
            "nome": nome,
            "tipo": tipo,
            "stato": "spento",
        }
        self.dispositivi.append(dispositivo)
        self.salva()
        return f"{nome} aggiunto."

    def accendi(self, nome):
        for dispositivo in self.dispositivi:
            if dispositivo.get("nome", "").lower() == nome.lower():
                dispositivo["stato"] = "acceso"
                self.salva()
                return f"{nome} acceso."
        return "Dispositivo non trovato."

    def spegni(self, nome):
        for dispositivo in self.dispositivi:
            if dispositivo.get("nome", "").lower() == nome.lower():
                dispositivo["stato"] = "spento"
                self.salva()
                return f"{nome} spento."
        return "Dispositivo non trovato."

    def lista(self):
        return self.dispositivi

    def stato(self):
        return {
            "sistema": self.nome,
            "dispositivi": self.dispositivi,
        }


if __name__ == "__main__":
    casa = SmartHomeJarvis()
    print(casa.aggiungi_dispositivo("Luce soggiorno", "lampada"))
    print(casa.accendi("Luce soggiorno"))
    print(casa.stato())
