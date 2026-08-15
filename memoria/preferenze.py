class PreferenzeJarvis:


    def __init__(self):

        self.preferenze = {

            "nome_utente": None,

            "stile_risposta": "normale",

            "lingua": "italiano"

        }





    def imposta(
        self,
        chiave,
        valore
    ):

        self.preferenze[chiave] = valore


        return (
            f"Preferenza aggiornata: "
            f"{chiave} = {valore}"
        )





    def leggi(
        self,
        chiave
    ):

        return self.preferenze.get(
            chiave,
            None
        )





    def tutte(
        self
    ):

        return self.preferenze





    def stato(
        self
    ):

        return {

            "nome":
                "Preferenze Jarvis",

            "preferenze":
                self.preferenze

        }