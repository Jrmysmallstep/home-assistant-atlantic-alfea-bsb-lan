# Atlantic Alféa BSB-LAN V1.5.19

Correctif de la commande Auto/ECO/Confort depuis Home Assistant.

- Le retour de `/JS` est indexé par numéro de paramètre, par exemple `{"700": {"status": 1, "destination": 0}}`. L'intégration sait désormais interpréter cette réponse au lieu de chercher un `status` au premier niveau.
- La confirmation par **relecture `/JQ=700` ou `/JQ=1000`** est maintenue : la commande n'est considérée comme réussie que lorsque la valeur réellement lue correspond à la valeur demandée.
- Aucun changement de la fonction OFF individuelle, de la saison globale, de l'ECS et du suivi des circulateurs.

La présence automatique n'est pas incluse dans cette version.
