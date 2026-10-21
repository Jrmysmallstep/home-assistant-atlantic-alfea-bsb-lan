# V1.5.6 — Atlantic Alféa BSB-LAN

## Synoptique adaptatif au thème Home Assistant

La carte Lovelace installée avec HACS suit désormais le thème Home Assistant
(mode clair ou sombre), au lieu d'imposer un fond sombre au milieu d'un tableau
de bord clair.

- `theme_mode: auto` (défaut) : suit les couleurs et le mode du thème HA installé.
- `theme_mode: light` : force le rendu clair.
- `theme_mode: dark` : conserve le rendu sombre d'origine.
- Bandeau supprimé, alarmes/diagnostics dépliables et liaisons orthogonales inchangés.
- Préservation de la lecture 10112/10122 pour Confort/Éco.
- Aucune modification des commandes PAC, dérogations et programmations.

## Installation

1. Mettre l'intégration à jour via HACS, puis redémarrer Home Assistant.
2. Dans Ressources Lovelace, remplacer l'URL du module JavaScript par :
   `/alfea-synoptique/pac-synoptique-card.js?v=1.5.6`.
3. Dans le YAML de la carte, ajouter facultativement `theme_mode: auto`.
   `auto` est utilisé si la propriété est absente.

Pour éviter les doublons, supprimer toute ancienne ressource
`/local/pac-synoptique-card.js`. L'inscription automatique des ressources
n'est pas activée par cette version : elle reste manuelle en mode stockage et YAML.

Voir `docs/SYNOPTIQUE_V155.md` pour le fonctionnement et les entités.