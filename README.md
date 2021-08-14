# Impression d'étiquettes à partir de la pesée

GUI pour gérer l'impression d'étiquettes de prix sur une Brother QL-710W à partir de la pesée effectuée sur une balance Kern PCD connectée à travers l'interface RS-232.
Le programme tourne sur un raspi équipé d'un écran LCD touch (1024x600).

## Installer les dépendances

`sudo apt-get install poppler-utils sqlitebrowser`

## Installer les modules Python

A partir du répertoire de l'application (p.ex. `/home/pi/agitescale`) exécuter la commande:

`sudo pip3 install -r requirements.txt`

## Ajouter une règle udev pour permettre l'accès à l'imprimante

Créer un fichier nommé `99-brother.rules` dans le répertoire `/etc/udev/rules.d/` avec le contenu suivant:

`SUBSYSTEM=="usb", ATTR{idVendor}=="04f9", ATTR{idProduct}=="2043", MODE="0666"`

## Créer la base de données

1. Créer une nouvelle base de données dans le répertoire de base (agitescale) nommée `agitescale.db` à l'aide de l'application **DB Browser for SQLite** (dans le menu *Programming*)
2. Cliquer sur *Cancel* quand la fenêtre de création d'une table s'ouvre
3. Aller sur l'onglet *Execute SQL* et exécuter les scripts ci-dessous pour créer les 3 tables:

```
CREATE TABLE `products` (
	`name`	text,
	`description`	text,
	`price_kg`	real,
	`price_fixed`	real,
	`expiration_days`	int
);

CREATE TABLE `sellers` (
	`name`	text,
	`address`	text
);

CREATE TABLE `labels` (
	`product_id`	int NOT NULL,
	`weight`	real,
	`price`	real,
	`price_kg`	real,
	`packing_date`	text,
	`expiry_date`	text,
	`seller_id`	int,
	FOREIGN KEY(`product_id`) REFERENCES `products`,
	FOREIGN KEY(`seller_id`) REFERENCES `sellers`
);
```

## Lancer automatiquement au démarrage

Pour lancer l'application lors du démarrage, créer un fichier `AgiteScale.desktop` dans le répertoire `/home/pi/.config/autostart/` (créer le répertoire si nécessaire):

```
[Desktop Entry]
Name=Agite Scale
Type=Application
Comment=Impression des étiquettes Kern
Exec=/usr/bin/python3 /home/pi/agitescale/main.py
```

Mettre les droits d'exécution sur le fichier:

`chmod +x /home/pi/.config/autostart/AgiteScale.desktop`

Redémarrer le raspberry pi

## Ajouter l'application au menu

1. Aller dane le menu *Preferences > Main Menu Editor*
2. Choisir une catégorie (p.ex. *Office*)
3. Cliquer sur *New Item*
4. Créer une entrée en utilisant les informations ci-dessous:
   - **Name**: Agite Scale
   - **Command**: `/usr/bin/python3 /home/pi/agitescale/main.py`
   - **Image**: Ajouter l'icône à partir du fichier `/home/pi/agitescale/static/favicon.ico`

## Debug

En cas d'erreur (l'application ne s'ouvre pas), lancer l'application dans le terminal à l'aide de la commande:

`python3 /home/pi/agitescale/main.py`

Les messages d'erreur s'afficher dans la console
