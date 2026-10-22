# Atlantic Alféa BSB-LAN V1.5.15 — Correction mobile

## Corrigé
- Portrait mobile : suppression des branches horizontales et du collecteur
  gris qui débordaient dans les cartes RDC, Étage et ECS.
- Raccordements verticaux courts pour COMP → PAC → sorties.
- Les cartes des deux circuits affichent désormais **Régime : Confort/Éco**
  via le programme actif BSB-LAN 10112/10122 (1 Réduit/Éco, 2 Confort).
  En cas d'indisponibilité, repli sur l'attribut Climate s'il est fiable ;
  sinon aucune affirmation inventée.
- L'état de régulation brut, par exemple « Limitation de la température
  ambiante », reste consultable dans les diagnostics.
- Le paysage conserve la présentation et les liaisons de la V1.5.14.

## Installation
1. Dans HACS, mettre à jour vers V1.5.15, puis redémarrer Home Assistant.
2. Modifier l'URL de la ressource **Module JavaScript** en
   `/alfea-synoptique/pac-synoptique-card.js?v=1.5.15`.
3. Garder `layout_orientation: auto` dans le YAML, ou choisir
   `layout_orientation: portrait` pour forcer le mode vertical.
4. Actualiser la page et purger le cache du navigateur si nécessaire.

La carte reste **en lecture seule**. Aucune commande, dérogation ni programmation
native n'a été modifiée.
