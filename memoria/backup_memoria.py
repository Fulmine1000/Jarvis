import os
import shutil
import datetime


CARTELLA_MEMORIA = "memoria"

CARTELLA_BACKUP = "memoria/backup"



class BackupMemoria:


    def __init__(self):

        self.crea_cartelle()



    def crea_cartelle(self):

        if not os.path.exists(CARTELLA_MEMORIA):

            os.makedirs(CARTELLA_MEMORIA)


        if not os.path.exists(CARTELLA_BACKUP):

            os.makedirs(CARTELLA_BACKUP)



    def crea_backup(self):


        data = datetime.datetime.now().strftime(
            "%d-%m-%Y_%H-%M-%S"
        )


        destinazione = (
            f"{CARTELLA_BACKUP}/backup_{data}"
        )


        os.makedirs(destinazione)



        for file in os.listdir(CARTELLA_MEMORIA):


            percorso = (
                f"{CARTELLA_MEMORIA}/{file}"
            )


            if os.path.isfile(percorso):

                shutil.copy(
                    percorso,
                    destinazione
                )


        return (
            "Backup creato correttamente."
        )



    def lista_backup(self):


        backup = os.listdir(
            CARTELLA_BACKUP
        )


        if not backup:

            return (
                "Nessun backup disponibile."
            )


        testo = "Backup disponibili:\n"


        for elemento in backup:

            testo += (
                "- "
                + elemento
                + "\n"
            )


        return testo



    def elimina_backup_vecchi(self):


        backup = os.listdir(
            CARTELLA_BACKUP
        )


        if len(backup) > 5:


            backup.sort()


            da_eliminare = backup[:-5]


            for elemento in da_eliminare:


                shutil.rmtree(
                    f"{CARTELLA_BACKUP}/{elemento}"
                )


            return (
                "Backup vecchi eliminati."
            )


        return (
            "Nessun backup da eliminare."
        )



if __name__ == "__main__":


    backup = BackupMemoria()


    print(
        backup.crea_backup()
    )


    print(
        backup.lista_backup()
    )