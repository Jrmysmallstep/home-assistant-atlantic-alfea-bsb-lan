# V1.5.7 — Éditeur visuel pour le synoptique Lovelace

La carte **PAC Synoptique** dispose désormais d'un éditeur graphique
directement dans Home Assistant.

### Éditeur visuel
- Menu **Apparence** : Automatique / Clair / Sombre ;
- case **Afficher les diagnostics complémentaires** ;
- aperçu de la carte actualisé lors des modifications ;
- conservation des options YAML et des correspondances d'entités existantes.

La carte et son éditeur restent entièrement en lecture seule côté PAC.
Le comportement des deux circuits, de l'ECS, des programmes horaires et des
dérogations n'est pas modifié.

### Mise à jour HACS
1. Installer V1.5.7 via HACS puis **redémarrer Home Assistant** ;
2. dans Ressources, remplacer l'ancienne URL par
   `/alfea-synoptique/pac-synoptique-card.js?v=1.5.7`
   (**Module JavaScript**) ;
3. dans le tableau de bord, **Modifier la carte** : l'éditeur visuel
   doit apparaître sans manipulation YAML.

> Le fichier JS est inclus dans HACS. L'enregistrement automatique de la ressource
> n'est **pas** inclus dans cette version : déclaration unique manuelle requise.

Voir `docs/SYNOPTIQUE_V155.md` pour les détails.
