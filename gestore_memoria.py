# DEPRECATO — mantenuto per riferimento storico.
# Usare il modulo ufficiale corrispondente (vedi analisi/README).
# Non usato dal kernel corrente.
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



    # PROFILO PERSONALE

    def salva_profilo(self, categoria, valore):

        return self.profilo.imposta(
            categoria,
            valore
        )



    def leggi_profilo(self, categoria):

        return self.profilo.leggi(
            categoria
        )



    def mostra_profilo(self):

        return self.profilo.mostra_profilo()



    # RICORDI

    def salva_ricordo(
        self,
        titolo,
        contenuto,
        categoria="generale",
        importanza="normale"
    ):

        return self.ricordi.aggiungi(
            titolo,
            contenuto,
            categoria,
            importanza
        )



    def cerca_ricordo(self, parola):

        return self.ricordi.cerca(
            parola
        )



    def mostra_ricordi(self):

        return self.ricordi.tutti()



    # CONVERSAZIONI

    def salva_conversazione(
        self,
        utente,
        risposta
    ):

        return self.conversazioni.salva_messaggio(
            utente,
            risposta
        )



    def storico(self):

        return self.conversazioni.ultimi_messaggi()



    # BACKUP

    def crea_backup(self):

        return self.backup.crea_backup()



    # CONTROLLO GENERALE

    def stato_memoria(self):

        return {
            "profilo": "attivo",
            "ricordi": "attivi",
            "conversazioni": "attive",
            "backup": "attivo"
        }



if __name__ == "__main__":


    memoria = MemoriaAvanzataJarvis()


    print(
        memoria.salva_profilo(
            "colore preferito",
            "blu"
        )
    )


    print(
        memoria.salva_ricordo(
            "animale",
            "Simone preferisce i cani",
            "preferenze",
            "alta"
        )
    )


    print(
        memoria.mostra_profilo()
    )


    print(
        memoria.mostra_ricordi()
    )


    print(
        memoria.stato_memoria()
    )
