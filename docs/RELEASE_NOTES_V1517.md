# Atlantic Alféa BSB-LAN V1.5.17

## Nouveauté — présélections Auto / ECO / Confort

- Ajout des presets **Auto**, **ECO** et **Confort** dans les entités Climate C1 et C2.
- Relecture du mode réellement sélectionné sur le régulateur via l'API JSON BSB-LAN (700 pour C1, 1000 pour C2).
- Commandes indépendantes par circuit, limitées aux valeurs 1 (Auto), 2 (Réduit/ECO), 3 (Confort), avec relecture de confirmation.
- **OFF individuel conservé et prioritaire** : aucune commande de preset lorsque le circuit est OFF.
- Gestion saisonnière globale chauffage/rafraîchissement et circulateurs inchangés.
- Aucun emplacement MQTT supplémentaire requis.

## Configuration

Dans les options de l'intégration, renseigner l'URL HTTP(S) de BSB-LAN (exemple : `http://192.168.1.88`). Sans URL, les presets restent inactifs. L'accès HTTP à BSB-LAN depuis Home Assistant doit être autorisé.

## Précautions

- Les modes presets ont été validés par des tests automatisés hors ligne ; leur fonctionnement sur la PAC réelle doit encore être vérifié en chauffage puis rafraîchissement.
- L'automatisation ECO selon la présence **n'est pas incluse** dans cette version.
- Préserver les dérogations natives et les choix manuels reste prioritaire.
