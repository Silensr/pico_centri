import os, machine, asyncio
from mcp import mcp9600


class Logger:

    # Constructeur de la classe. Initialisé avec un nom de fichier, et un objet mcp9600. La RTC est initialisée en interne. De même pour la tpache en coroutine.
    def __init__(self, mcp: mcp9600, filename: str = "default.csv") -> None:
        self.filename: str = filename
        self.mcp = mcp
        self.rtc = machine.RTC()
        self.task = asyncio.create_task(self.loop_measure())
    
    # Ajoute une ligne (et donc une mesure) au fichier
    def addrow(self):
        f = open(self.filename, "a")
        f.write(f"{self.mcp.get_hot()};" + '-'.join([str(i) for i in self.rtc.datetime()]) + "\n")
        f.close()

    # changement de nom de fichier
    def change_file_name(self, new_name: str):
        self.filename: str = new_name
    
    # Changement de date à partir d'un dict
    def change_datetime(self, new_datetime: dict):
        
        self.rtc.datetime((
            new_datetime['year'],
            new_datetime['month'],
            new_datetime['day'],
            new_datetime['weekday'],
            new_datetime['hour'],
            new_datetime['minute'],
            new_datetime['second'],
            0
        ))

        return self.rtc.datetime()

    # Crée le fichier en choisissant de le remplacer ou non.
    def create_file(self, overwrite: bool = False):

        if self.filename not in os.listdir():
            f = open(self.filename, "w")
            f.close()

        elif overwrite:
            os.remove(self.filename)
            f = open(self.filename, "w")
            f.close()

        else:
            raise OSError
        

    # Lis et renvoie les données contenue dans le fichier 
    def retrieve(self):
        try:
            f, t_dict = open(self.filename, "r"), []
        except: 
            raise FileNotFoundError
        
        for i in f.readlines():
            r: list[str] = i.split(';')
            t_dict.append({"temp": r[0], "timestamp": r[1].replace("\n", "")})
        
        f.close()

        return t_dict

    
    # Méthodes de gestion de prise de la mesure.
    # Coroutine de prise des mesures.
    async def loop_measure(self):
        while True:
            self.addrow()
            await asyncio.sleep(15)
    
    # Démarrage de l'acqusition
    def begin(self):
        if self.task.done():
            self.task = asyncio.create_task(self.loop_measure())

        else:
            raise RuntimeError
    
    # Arrêt de l'acquisition
    def stop(self):
        if not self.task.done():
            self.task.cancel()

        else:
            raise RuntimeError
        
    # Méthode retournant "True" si l'acquisition est en cours.
    def working(self) -> bool:
        return not self.task.done()


# Code de test
if __name__ == '__main__':
    try:
        os.remove("default.csv")

    except:
        pass

    mcp = mcp9600()
    logger = Logger(mcp)

    logger.change_datetime({
        "year": 2023,
        "month": 11,
        "day": 7,
        "weekday": 1,
        "hour": 16,
        "minute": 21,
        "second": 5
    })

    async def main():
        print(logger.working())
        await asyncio.sleep(30)
        logger.stop()
        await asyncio.sleep_ms(1)
        print(logger.working())
        print(logger.retrieve())
    
    asyncio.run(main())
