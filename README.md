# Impression d'étiquettes à partir de la pesée

GUI pour gérer l'impression d'étiquettes de prix sur une Brother QL-710W à partir de la pesée effectuée sur une balance Kern PCD connectée à travers l'interface RS-232.
Le programme tourne sur un raspi équipé d'un écran LCD touch (1024x600).

## Installer les modules Python

sudo pip3 install -r requirements.txt

## Ajouter une règle udev pour permettre l'accès à l'imprimante

Créer un fichier nommé 99-brother.rules dans le répertoire /etc/udev/rules.d/ avec le contenu suivant:

SUBSYSTEM=="usb", ATTR{idVendor}=="04f9", ATTR{idProduct}=="2043", MODE="0666"

## Créer la base de données

Créer une nouvelle base de données dans le répertoire de base (agitescale) nommée agitescale.db

Exécuter les scripts ci-dessous pour créer les 3 tables:


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

