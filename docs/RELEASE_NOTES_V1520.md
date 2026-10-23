# Atlantic Alféa BSB-LAN V1.5.20

## Carte PAC Synoptique : mode natif de chaque circuit

La carte affiche désormais **AUTO**, **ECO forcé**, **Confort forcé** ou **OFF** séparément pour C1 (RDC) et C2 (Étage), à partir du `preset_mode` des entités Climate et de leur état OFF.

L'affichage est en lecture seule. Les états réels BSB-LAN, la programmation ECO/Confort, les circulateurs, les consignes, l'ECS, les alarmes et le mode global sont préservés. Aucune publication MQTT supplémentaire.

Actualiser le cache du navigateur après la mise à jour HACS pour charger le JavaScript de la nouvelle carte.
