from .database import DatabaseMemoria


class ProfiloJarvis:

    def __init__(
        self,
        logger=None
    ):
        self.nome = "Profilo Jarvis"
        self.attivo = False
        self.logger = logger
        self.database = DatabaseMemoria()
        self.categoria = "profilo"

    def avvia(self):
        self.attivo = True

        if self.logger:
            self.logger.info(
                "Profilo memoria avviato."
            )

    def imposta(
        self,
        categoria,
        valore
    ):
        self.database.aggiungi(
            self.categoria,
            categoria,
            valore
        )

        return (
            f"Profilo aggiornato: "
            f"{categoria} = {valore}"
        )

    def leggi(
        self,
        categoria
    ):
        dato = self.database.leggi(
            self.categoria,
            categoria
        )

        if dato:
            return dato["valore"]

        return None

    def mostra_profilo(
        self
    ):
        profilo = self.database.tutto().get(
            self.categoria,
            {}
        )

        if not profilo:
            return "Profilo vuoto."

        # Le risposte del profilo vengono costruite come frasi separate,
        # usando la punteggiatura invece dei soli ritorni a capo.
        # In questo modo anche il motore vocale crea una pausa naturale
        # tra un'informazione e la successiva.
        descrizioni = {
            "colore_preferito": "Il tuo colore preferito è",
            "nome_utente": "Il tuo nome è",
        }

        parti = ["Informazioni che ricordo."]

        for nome, dato in profilo.items():
            valore = dato["valore"]
            etichetta = descrizioni.get(
                nome,
                nome.replace("_", " ")
            )

            parti.append(
                f"{etichetta}: {valore}."
            )

        return " ".join(parti)

    def elimina(
        self,
        categoria
    ):
        risultato = self.database.elimina(
            self.categoria,
            categoria
        )

        if risultato:
            return (
                f"Ho eliminato {categoria}."
            )

        return (
            "Informazione non trovata."
        )

    def numero_informazioni(
        self
    ):
        profilo = self.database.tutto().get(
            self.categoria,
            {}
        )

        return len(
            profilo
        )

    def stato(
        self
    ):
        return {
            "nome":
                self.nome,

            "stato":
                "attivo"
                if self.attivo
                else "spento",

            "informazioni":
                self.numero_informazioni()
        }
    