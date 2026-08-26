# DEPRECATO — mantenuto per riferimento storico.
from memoria.profilo import ProfiloJarvis
from memoria.ricordi import GestoreRicordi
from memoria.conversazioni import GestoreConversazioni
from memoria.backup_memoria import BackupMemoria


class MemoriaAvanzataJarvis:
    def __init__(self):
        self.profilo = ProfiloJarvis()
        self.ricordi = GestoreRicordi()
        self.conversazioni = GestoreConversazioni()
        self.backup = BackupMemoria()

    def salva_profilo(self, categoria, valore):
        return self.profilo.imposta(categoria, valore)

    def leggi_profilo(self, categoria):
        return self.profilo.leggi(categoria)

    def mostra_profilo(self):
        return self.profilo.mostra_profilo()

    def salva_ricordo(self, titolo, contenuto, categoria="generale", importanza="normale"):
        return self.ricordi.aggiungi(titolo, contenuto, categoria, importanza)

    def cerca_ricordo(self, parola):
        return self.ricordi.cerca(parola)

    def mostra_ricordi(self):
        return self.ricordi.tutti()

    def salva_conversazione(self, utente, risposta):
        return self.conversazioni.salva_messaggio(utente, risposta)

    def storico(self):
        return self.conversazioni.ultimi_messaggi()

    def crea_backup(self):
        return self.backup.crea_backup()

    def stato_memoria(self):
        return {"profilo": "attivo", "ricordi": "attivi", "conversazioni": "attive", "backup": "attivo"}
