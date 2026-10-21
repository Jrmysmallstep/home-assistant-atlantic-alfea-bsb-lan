# Atlantic Alféa BSB-LAN V1.5.10

- **Synoptique** : affiche les capteurs `C1 - Circulateur` et `C2 - Circulateur` en marche, arrêtés ou indisponibles sur les cartes Circuit 1 et 2.
- Remplace la pastille ambiguë « Régime : indéterminé » par le retour réel de chaque circulateur.
- Ajoute une ligne « Circulateur » pour chaque circuit dans les diagnostics.
- Les entités `C1/C2 - État actuel` continuent de refléter Chauffage, Refroidissement, En attente ou Arrêt selon les entités Climate ; l'état réellement affiché dépend des relevés BSB-LAN.
- Aucune modification des commandes PAC, consignes, programmation, dérogations ou pilotage ECS.
