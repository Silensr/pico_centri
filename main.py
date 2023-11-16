import network, json, os, asyncio, gc
from machine import Pin
from logger import Logger
from mcp import mcp9600


onboard = Pin("LED", Pin.OUT)
mcp = mcp9600()

ssid, key = "Pico_Castor", "Pollux22"

logger = Logger(mcp)

def parse_json(raw) -> dict:
    j = ('{' + raw.split('{')[1].split('}')[0] + '}')\
        .replace('\\n', '')\
        .rstrip()\
        .replace(' ', '')

    return json.loads(j)

def list_files():
    d = {}
    for file in os.listdir():
        d[file] = {"size": os.stat(file)[6]}

    return d

# Enclenchement du réseau
def create_network():

    # Initialisation du réseau
    wlan = network.WLAN(network.AP_IF)
    wlan.config(essid=ssid, password=key)
    wlan.active(True)

    # On bloque tant que le réseau wifi n'est pas actif
    while wlan.active() == False:
        pass

    print('AP Mode Is Active, You can Now Connect')
    print('IP Address To Connect to:: ' + wlan.ifconfig()[0])


# Logique serveur
async def serveAPI(reader, writer):
    print("Client connected")
    # Lecture de la requête
    request_line = await reader.read(1024)
    print("Request :", request_line)

    # Transformation en chaîne de caractère
    request = str(request_line)

    # Ajustage du temps
    if request.find("/settime") == 6:
        
        data = parse_json(request)
        
        new_dt = logger.change_datetime(data)

        writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
        writer.write(json.dumps({"time": '-'.join([str(i) for i in new_dt])}))

    # Obtention des données de mesures
    elif request.find('/retrieve') == 6:

        # Ramassage des miettes, pour transmettre le plus d'informations possibles sans erreurs de mémoire vive.
        gc.collect()

        writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
        writer.write(json.dumps({"data":logger.retrieve()}))

    # Changement du nom de fichier
    elif request.find('/changefilename') == 6:
        data = parse_json(request)

        logger.change_file_name(data["name"])
    
    # Création du fichier
    elif request.find('/createfile') == 6:
        data = parse_json(request)

        try:
            logger.create_file(data["overwrite"])
            
            writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')

        except OSError:

            writer.write('HTTP/1.0 403 Forbidden\r\nContent-type: application/json\r\n\r\n')
            writer.write(json.dumps({"message": "Le fichier existe déjà et n'a pas été supprimé"}))
    
    # Déclenchement des mesures
    elif request.find('/begin') == 6:
        try:
            logger.begin()
            writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')

        except RuntimeError:
            writer.write('HTTP/1.0 500 Internal Server Error\r\nContent-type: application/json\r\n\r\n')
            writer.write(json.dumps({"message": "La tache n'a pas pu être enclenchée"}))
    
    # Arrêt des mesures
    elif request.find('/stop') == 6:
        try:
            logger.stop()
            writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')

        except RuntimeError:
            writer.write('HTTP/1.0 500 Internal Server Error\r\nContent-type: application/json\r\n\r\n')
            writer.write(json.dumps({"message": "La tâche n'a pas pu être terminée"}))

    # Obtention du nom du fichier
    elif request.find('/getname') == 6:
        writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
        writer.write(json.dumps({"filename": logger.filename}))
    
    # Liste des fichiers csv
    elif request.find('/listfiles') == 6:
        writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
        writer.write(json.dumps({"files": list_files()}))
    
    # Supression fichier
    elif request.find("/deletefile") == 6:

        filename = parse_json(request)["filename"]
        
        # On vérifie:
        # Si le fichier qui va être supprimé n'est pas un script python
        if filename.endswith(".py"):
            writer.write('HTTP/1.0 403 Forbidden\r\nContent-type: application/json\r\n\r\n')
            writer.write(json.dumps({"message": "Les scripts ne doivent pas être supprimés"}))

        # Si le fichier n'est pas utilisé pour une acquisition
        elif filename == logger.filename and logger.working():
            writer.write('HTTP/1.0 403 Forbidden\r\nContent-type: application/json\r\n\r\n')
            writer.write(json.dumps({"message": "L'acquisition est en cours sur ce fichier"}))
        
        # Si le fichier existe
        elif filename not in os.listdir():
            writer.write('HTTP/1.0 403 Forbidden\r\nContent-type: application/json\r\n\r\n')
            writer.write(json.dumps({"message": "Le fichier n'existe pas"}))

        # Si tout est bon, on supprime
        else :
            os.remove(filename)

            writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
            writer.write(json.dumps({"message": "fichier supprimé"}))

    # Permet de savoir si l'acquisition est en cours.
    elif request.find('/state') == 6:
        writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
        writer.write(json.dumps({"working": logger.working()}))

    #Obtient l'identité du pico. Cela permet au logiciel technicien de vérifier si l'appareil auquel il est connecté est bien un pico.
    elif request.find("/self") == 6:
        writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
        writer.write(json.dumps({"name": ssid}))

    elif request.find("/gettime"):
        
        writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
        writer.write(json.dumps({"time": '-'.join([str(i) for i in logger.rtc.datetime()])}))

    # Si le client tente une requête dont l'adresse n'existe pas, on renvoie l'erreur 404
    else:
        writer.write('HTTP/1.0 404 Not Found\r\nContent-type: application/json\r\n\r\n')

    # Fermeture de la requête
    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")


async def main():
    print("Setting up network")
    # Création du réseau
    create_network()
    
    print("Setting up webserver")

    # Mise en place du serveur
    asyncio.create_task(asyncio.start_server(serveAPI, '0.0.0.0', 80))

    # Cliegnottement de sécurité
    while True:
        onboard.on()
        await asyncio.sleep(0.25)
        onboard.off()
        await asyncio.sleep(5)


#Démarage du programme
try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
