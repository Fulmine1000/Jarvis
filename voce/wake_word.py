import time


class WakeWordJarvis:
    """Gestisce l'attivazione vocale e separa sempre la wake word dal comando."""

    def __init__(self):
        self.nome = "Wake Word Jarvis"
        self.parole_attivazione = ["jarvis", "hey jarvis", "ehi jarvis"]
        self.prefissi_attivazione = ["ehi", "hey"]
        self.attivo = False
        self.ultimo_rilevamento = None
        self.tempo_attivo = 10
        self.ultimo_comando = ""

    def pulisci_testo(self, testo):
        if not testo:
            return ""
        testo = str(testo).lower().strip()
        for vecchio, nuovo in {"jervis": "jarvis", "gervis": "jarvis"}.items():
            testo = testo.replace(vecchio, nuovo)
        testo = testo.replace(",", " ").replace(".", " ")
        return " ".join(testo.split())

    def _estrai_comando_da_wake_word(self, frase):
        """Rimuove la wake word e restituisce soltanto il comando."""
        for parola in sorted(self.parole_attivazione, key=len, reverse=True):
            if frase == parola:
                return ""
            if frase.startswith(parola + " "):
                return frase[len(parola):].strip()
        return None

    def controlla(self, frase):
        frase = self.pulisci_testo(frase)
        if not frase:
            return {"attivato": False, "comando": ""}

        # Anche se la wake word era già attiva, "jarvis che ore sono"
        # deve diventare semplicemente "che ore sono".
        if self.verifica_timeout():
            comando = self._estrai_comando_da_wake_word(frase)
            if comando is not None:
                self.attiva()
                self.ultimo_comando = comando
                return {"attivato": True, "comando": comando}

            if frase in self.prefissi_attivazione:
                self.attiva()
                self.ultimo_comando = ""
                return {"attivato": True, "comando": ""}

            self.ultimo_comando = frase
            self.attiva()
            return {"attivato": True, "comando": frase}

        if frase in self.prefissi_attivazione:
            self.attiva()
            self.ultimo_comando = ""
            return {"attivato": True, "comando": ""}

        # Supporta sia "jarvis" sia "jarvis + comando" nella stessa frase.
        comando = self._estrai_comando_da_wake_word(frase)
        if comando is not None:
            self.attiva()
            self.ultimo_comando = comando
            return {"attivato": True, "comando": comando}

        return {"attivato": False, "comando": ""}

    def attiva(self):
        self.attivo = True
        self.ultimo_rilevamento = time.time()

    def verifica_timeout(self):
        if not self.attivo:
            return False
        if time.time() - self.ultimo_rilevamento > self.tempo_attivo:
            self.disattiva()
            return False
        return True

    def disattiva(self):
        self.attivo = False

    def cambia_timeout(self, secondi):
        self.tempo_attivo = secondi

    def aggiungi_parola(self, parola):
        parola = parola.lower().strip()
        if parola not in self.parole_attivazione:
            self.parole_attivazione.append(parola)
            return f"Parola aggiunta: {parola}"
        return "Parola già presente."

    def rimuovi_parola(self, parola):
        parola = parola.lower().strip()
        if parola in self.parole_attivazione:
            self.parole_attivazione.remove(parola)
            return f"Parola rimossa: {parola}"
        return "Parola non trovata."

    def stato(self):
        return {
            "nome": self.nome,
            "attivo": self.attivo,
            "timeout": self.tempo_attivo,
            "parole": self.parole_attivazione,
            "ultimo_comando": self.ultimo_comando,
        }
