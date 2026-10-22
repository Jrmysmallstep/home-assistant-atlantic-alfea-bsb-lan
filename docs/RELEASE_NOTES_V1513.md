# Atlantic Alféa BSB-LAN V1.5.13 — Carte compacte et orientations

Cette mise à jour vise uniquement le **rendu du synoptique Lovelace**.

- **Mode automatique** : paysage/portrait selon la largeur disponible de la carte.
- **Mode paysage forcé** : conserve la disposition horizontale avec défilement si besoin.
- **Mode portrait forcé** : blocs superposés, optimisés pour une utilisation mobile.
- **Plus compact** : paddings, tailles d'icônes et hauteurs réduits, informations inchangées.
- **Fluidité** : filtres SVG animés remplacés par une simple variation d'opacité ;
  rotation du ventilateur via CSS transform ; animations de flux conservées.
- **Aucune image externe** : tous les dessins sont en CSS/SVG inline.
- **Automatique / Clair / Sombre** : les trois choix de thème sont conservés.
- **65 correspondances d'entités** maintenues, avec alarmes, circulateurs
  et diagnostics ; aucune entité nouvelle requise.
- **Aucun changement de commande** de la PAC, des programmes ou des dérogations.

## Installer
1. Mettre l'intégration à jour dans HACS vers V1.5.13.
2. Redémarrer Home Assistant.
3. Modifier la ressource Module JavaScript Lovelace :
   `/alfea-synoptique/pac-synoptique-card.js?v=1.5.13`
4. Éditer la carte et choisir l'orientation **Automatique / Paysage / Portrait**.

L'option YAML `layout_orientation: auto` est appliquée par défaut.
La carte demeure exclusivement en lecture seule.
