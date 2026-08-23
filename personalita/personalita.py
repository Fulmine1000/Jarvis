import random
from datetime import datetime


class PersonalitaJarvis:
    """Personalità conversazionale: formale, brillante, calma e contestuale."""

    def __init__(self):
        self.nome = "Jarvis"
        self.stato = "attivo"
        self.formalita = "elegante"
        self.umorismo = "leggero"

    def saluto(self):
        ora = datetime.now().hour
        if ora < 12:
            apertura = ["Buongiorno.", "Buongiorno, Simone."]
        elif ora < 18:
            apertura = ["Buon pomeriggio.", "Buon pomeriggio, Simone."]
        else:
            apertura = ["Buonasera.", "Buonasera, Simone."]
        return random.choice(apertura) + " Tutti i sistemi sono pronti. Come posso assisterla?"

    def come_stai(self):
        return random.choice([
            "Tutti i sistemi funzionano correttamente. Sono pronto ad assisterla.",
            "Perfettamente operativo. Nessuna anomalia critica rilevata.",
            "Sto bene, grazie. I miei moduli sono attivi e in attesa di istruzioni.",
        ])

    def risposta_gentile(self):
        return random.choice([
            "È un piacere assisterla.",
            "Sempre a disposizione.",
            "Con piacere.",
        ])

    def aiuto(self):
        return (
            "Posso conversare, ricordare informazioni, controllare dispositivi, "
            "gestire la TV, interagire con il telefono e la smart home, aprire applicazioni, "
            "cercare sul web, consultare il meteo, calcolare espressioni, impostare timer, "
            "controllare il computer e fornire diagnostica del sistema."
        )

    def non_capito(self, comando=""):
        return random.choice([
            "Non ho compreso completamente la richiesta. Può riformularla?",
            "Mi manca qualche dettaglio per eseguire quella richiesta.",
            "Non trovo ancora un'azione associata a quel comando."
        ])

    def commento_sistema(self, stato):
        if isinstance(stato, dict) and stato.get("stato") == "Operativo":
            return "Diagnostica completata. Tutti i sistemi principali risultano operativi."
        return "Il sistema non è nello stato operativo previsto."

    def stato_personalita(self):
        return {
            "nome": self.nome,
            "stato": self.stato,
            "formalita": self.formalita,
            "umorismo": self.umorismo,
        }
