# Projet PicoCentri

## Description

Ce projet micropython présente tous les élements nécessaire pour une acquisition de température via thermocouple, et la transmission des données via wifi.

## Division des fichiers

Il est divisé en plusieurs fichiers :

### main.py

Sert à coordonner l'ensemble des processus. Contient la logique serveur, est éxecuté dès l'allumage du pico.

### logger.py

Gère les fichiers d'enregistrements et le processus d'acqusition. Permet aussi de fournir une lecture des fichiers.

### mcp.py

Gère la communication I2C avec l'amplificateur de thermocouple mcp9600.

## Serveur http

Un serveur http asynchrone a été programmé. Les requêtes qu'il reçoit sont seulement du types GET. Une mise à jour pourrait être envisagées afin de mettre en place les 3 autres principaux types de requêtes.

### Points d'entrées

Cette section détaille les différents points d'entrées du serveur :

#### Horodatage

##### /gettime

Renvoie l'heure et la date du module RTC du pico.

##### /settime

Met à jour le module RTC du pico. Les champs nécessaires sont:

- year: année en cours
- month: mois en cours
- day: jour du mois
- weekday: jour de la semaine (de 0 à 6)
- hour: heure
- minute: minute
- second: secondes

On peut aussi paramétrer les microsecondes, mais étant donné qu'il n'est pas nécessaire d'avoir une telle précision, elles sont paramétrées à 0 par défaut afin de ne pas se compliquer la tâche.

#### Identité
##### /self
Renvoie le nom du module pico. 

#### Processus

##### /begin

Démarre le processus de mesure. Renvoie une erreur si le processus est déjà en cours

##### /stop 

Stoppe le processus de mesure. Renvoie une erreur s'il n'est pas en cours.

##### /state

Regarde si le processus de mesure est en cours.

#### Gestion des fichiers

##### /getname

Donne le nom du fichier utilisé pour l'acquisition.

##### /changefilename

Change le nom du fichier. Utilise le nom passé dans l'argument "new_name" pour le nom de fichier. S'il n'existe pas, il faut le créer avec la requête "/create_file"

##### /createfile

Crée le fichier associé. Si le fichier existe déjà, il est nécessaire d'utiliser l'argument "overwrite" avec la valeur True. Si le fichier existe et que cet argument n'est pas fournis, alors une erreur sera renvoyée.

##### /listfiles

Renvoie la liste des fichiers présente sur le module pico.

##### /deletefile

Supprime un fichier du pico. Le nom du fichier doit être passé via l'argument "filename". S'il y a un fichier de même nom déjà présent, l'argument overwrite doit être utilisé pour le supprimer au préalable. Sinon, une erreur sera renvoyée.

#### Acquisition des données

##### /retrieve 

Renvoie les informations contenues dans le fichier utilisées pour l'acquisition.
