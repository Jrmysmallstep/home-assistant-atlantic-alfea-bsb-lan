# Atlantic Alféa BSB-LAN V1.5.18

Correctif ciblé de la version V1.5.17 :

- Correction de l'erreur `async_dispatcher_send from a thread other than the event loop` provoquée par les messages MQTT des circulateurs C1 (9031) et C2 (8760).
- La mise à jour des états des circulateurs est désormais exécutée sur la boucle Home Assistant.
- Correction de l'erreur au déchargement/rechargement de l'intégration (`a coroutine was expected, got {1: ..., 2: ...}`) en empêchant le callback de nettoyage de renvoyer le dictionnaire d'états.
- Aucune modification des modes natifs Auto/ECO/Confort, de l'arrêt individuel, des circulateurs eux-mêmes, du mode global ou de l'ECS.

Après installation HACS, redémarrer Home Assistant et vérifier que les deux erreurs ne réapparaissent pas.
