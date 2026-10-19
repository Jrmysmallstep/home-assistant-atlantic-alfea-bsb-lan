# V1.4.0-beta.3 — validation en mode chauffage

## Périmètre

Tests en lecture seule, sans bascule chauffage/rafraîchissement et sans modifier la configuration du régulateur RVS21.831F/127.

**Attention :** le sélecteur « Mode global » reste techniquement capable d'envoyer des commandes de mise en Protection lorsqu'on sélectionne **Off**. Il ne faut donc **pas** manipuler ce sélecteur pendant les essais en lecture seule. Les commandes directes Chauffage ↔ Rafraîchissement sont volontairement bloquées tant que la sécurité de commutation n'est pas vérifiée.

## Préconditions

- Effectuer une sauvegarde Home Assistant.
- Noter les quatre modes natifs dans BSB-LAN avant installation.
- Configuration attendue actuellement :
  - 700 = 1 (chauffage RDC automatique)
  - 1000 = 0 (chauffage étage protection)
  - 901 = 0 (rafraîchissement RDC protection)
  - 1201 = 0 (rafraîchissement étage protection)
- Vérifier la publication du workflow « Beta offline checks » : tests de syntaxe et simulation tous réussis.

## Tests fonctionnels sans écriture

1. Redémarrer Home Assistant après installation et vérifier l'absence d'erreur de chargement de l'intégration.
2. Vérifier le sélecteur global « Chauffage » ; attribut « source_saison » = BSB-LAN si au moins un circuit chauffage est actif.
3. Vérifier circuit RDC : climate Chauffage, consigne actuelle et température ambiante conformes aux paramètres 8741 et 8740.
4. Vérifier circuit étage : climate Éteint et état actuel « Mode protection ».
5. Vérifier que les informations ECS restent lisibles et leur historique n'est pas perdu.
6. Vérifier les capteurs « État actuel » des deux circuits, sans supprimer les anciens capteurs saisonniers.
7. Consulter en lecture seule http://192.168.1.88/JQ=700,1000,901,1201,8000,8001,8006,8400,8741,8771 ; vérifier qu'aucun des quatre modes n'a changé lors de l'installation.

## Non testé / explicitement non validé

- Commutation Chauffage ↔ Rafraîchissement depuis Home Assistant (bloquée).
- Dérogation native chauffage.
- Situation de deux circuits en Protection sans source de saison indépendante : l'affichage peut s'appuyer sur le dernier mode connu mémorisé, non confirmé.
- Sécurité de la transition réelle après 913 = 12 h. La temporisation doit être étudiée avant d'autoriser une activation opposée.

## Critères d'arrêt

Si les états réels des circuits changent sans commande explicite, si un circuit est activé de façon inattendue ou si des erreurs empêchent les états de se mettre à jour : arrêter le test, ne pas utiliser les commandes de la beta, rétablir la version stable depuis HACS et relever les journaux.
