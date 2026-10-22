# Atlantic Alféa BSB-LAN V1.5.14 — correctif du synoptique

Correctif de l'affichage des **liaisons PAC → Circuit 1 (RDC) / Circuit 2 (Étage) / ECS**
en mode Paysage et dans le mode Automatique sur écran large.

Dans la V1.5.13, des styles CSS du mode Portrait s'appliquaient également
aux autres dispositions : le raccordement PAC se retrouvait comprimé à
38 pixels de haut, et ses trois conduites apparaissaient en haut de la carte.

Les sélecteurs ont été isolés correctement par orientation. Le synoptique
conserve sa géométrie, ses raccordements à angles droits et les animations.

- Aucun ajout/retrait d'entités (65 correspondances inchangées).
- Les options de thèmes, d'orientation et de présentation restent disponibles.
- Aucun changement aux commandes ou dérogations BSB-LAN.

## Installation via HACS
1. Mettre Atlantic Alféa BSB-LAN à jour vers V1.5.14.
2. Redémarrer Home Assistant.
3. Mettre à jour l'URL de la ressource Lovelace (Module JavaScript) :
   `/alfea-synoptique/pac-synoptique-card.js?v=1.5.14`
4. Actualiser la page (rechargement forcé si Chrome met l'ancien JS en cache).

Votre configuration de carte YAML reste inchangée.
