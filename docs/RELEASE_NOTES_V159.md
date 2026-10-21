# Atlantic Alféa BSB-LAN V1.5.9

## États réels des circuits C1 et C2
- Les capteurs existants « C1 - État actuel » et « C2 - État actuel » reflètent l'action de leurs entités Climate : **Chauffage**, **Refroidissement**, **En attente** ou **Arrêt**.
- Les régimes BSB-LAN natifs Confort/Réduit sont conservés dans les attributs diagnostics `regime_bsb` et `etat_bsb_brut`.
- L'absence temporaire d'un état BSB ne force plus « En attente » à elle seule si le retour de circulateur est exploitable.

## Circulateurs
- C1 : paramètre **9031**, relais QX1, corrélé au démarrage de la pompe sur l'installation de référence.
- C2 : paramètre **8760**, état de la pompe du circuit 2.
- Les deux capteurs binaires sont en lecture seule ; prise en charge des retours MQTT en complément des entités sources.

## Compatibilité et précautions
- Aucune modification des programmes PAC, modes natifs de dérogation, consignes ou commandes.
- La marche d'un circulateur indique une activité hydraulique commandée ; elle ne garantit pas à elle seule un débit ou un transfert thermique mesurés.
- Après mise à jour HACS et redémarrage de Home Assistant, vérifier les états C1/C2 lors des démarrages/arrêts des deux circulateurs et pendant une charge ECS.
