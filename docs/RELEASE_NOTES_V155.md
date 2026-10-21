# V1.5.5 — Atlantic Alféa BSB-LAN

Intégration du synoptique Lovelace en lecture seule, avec alarmes repliables et programme Confort/Éco fiabilisé.

## Nouveau

- Carte `custom:pac-synoptique-card` livrée avec l'intégration HACS.
- Ressource locale : `/alfea-synoptique/pac-synoptique-card.js?v=1.5.5`.
- COMP → PAC → RDC / Étage / ECS, affichage horizontal, diagnostics, alarmes et animations.
- Programme horaire affiché depuis `10112` et `10122` (1 = Éco, 2 = Confort).
- Contrôle inchangé : aucune commande PAC depuis le synoptique, dérogations conservées.

## Mise à jour

1. Installez V1.5.5 via HACS puis redémarrez HA.
2. Dans les ressources du tableau de bord, **supprimez** l'ancienne entrée `/local/pac-synoptique-card.js` si elle existe.
3. Ajoutez **Module JavaScript** : `/alfea-synoptique/pac-synoptique-card.js?v=1.5.5`.
4. Conservez le YAML de carte `type: custom:pac-synoptique-card`.

La carte respecte les capteurs réellement exposés. L'état `122` indique une limitation ambiante, pas à lui seul un régime Éco.

Documentation : https://github.com/Jrmysmallstep/home-assistant-atlantic-alfea-bsb-lan/blob/main/docs/SYNOPTIQUE_V155.md
