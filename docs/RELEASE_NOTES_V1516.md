# Atlantic Alféa BSB-LAN V1.5.16 — États bruts

Suite à la V1.5.15, les cartes RDC et Étage affichent à nouveau
**exactement le libellé de l'entité « État actuel »** (capteurs BSB-LAN),
sans conversion du texte en « Régime : Éco » ou « Régime : Confort ».

Par exemple, « Limitation de la température ambiante » doit rester visible,
même lorsque le programme horaire natif 10122 est en Allure Réduit.

Le programme 10112/10122 demeure consultable, dans les diagnostics.
Le correctif d'affichage portrait de la V1.5.15 est entièrement conservé.

## Mise à jour HACS
- Mettre à jour vers V1.5.16 et redémarrer Home Assistant.
- Mettre l'URL du module JavaScript à
  `/alfea-synoptique/pac-synoptique-card.js?v=1.5.16`.
- Pour un smartphone : `layout_orientation: auto` ou `portrait`.

Cette mise à jour ne modifie pas les commandes, consignes, dérogations
ou programmations de la PAC. La carte est en lecture seule.
