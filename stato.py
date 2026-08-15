import platform
import shutil
import time
import os


try:
    import psutil
except ImportError:
    psutil = None



class StatoJarvis:


    def __init__(self):

        self.nome = "Monitor Sistema"

        self.avvio = time.time()



    def sistema_operativo(self):

        return {

            "sistema": platform.system(),

            "versione": platform.version(),

            "architettura": platform.machine()

        }



    def cpu(self):

        if psutil:

            return {

                "utilizzo": psutil.cpu_percent(
                    interval=1
                ),

                "core": psutil.cpu_count()

            }


        return {
            "utilizzo": "Non disponibile"
        }



    def memoria_ram(self):

        if psutil:

            ram = psutil.virtual_memory()

            return {

                "totale_GB":
                    round(
                        ram.total / (1024**3),
                        2
                    ),

                "usata_percentuale":
                    ram.percent

            }


        return {
            "ram": "Non disponibile"
        }



    def disco(self):

        disco = shutil.disk_usage("/")


        return {

            "totale_GB":
                round(
                    disco.total / (1024**3),
                    2
                ),

            "libero_GB":
                round(
                    disco.free / (1024**3),
                    2
                )

        }



    def batteria(self):

        if psutil:

            try:

                batteria = psutil.sensors_battery()

                if batteria:

                    return {

                        "percentuale":
                            batteria.percent,

                        "collegato":
                            batteria.power_plugged

                    }


            except:

                pass


        return "Non disponibile"



    def tempo_attivo(self):

        tempo = int(
            time.time() - self.avvio
        )


        minuti = tempo // 60


        return f"{minuti} minuti"



    def completo(self):

        return {

            "sistema":
                self.sistema_operativo(),

            "cpu":
                self.cpu(),

            "ram":
                self.memoria_ram(),

            "disco":
                self.disco(),

            "batteria":
                self.batteria(),

            "tempo_attivo":
                self.tempo_attivo()

        }



if __name__ == "__main__":


    stato = StatoJarvis()


    print(
        stato.completo()
    )