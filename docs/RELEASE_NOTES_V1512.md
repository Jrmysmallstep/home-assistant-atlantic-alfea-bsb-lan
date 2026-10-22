# V1.5.12 — Synoptique 2D

## Nouveautés
- Présentation « Épurée » en option, sans illustration 3D ni image externe.
- En largeur horizontale, liens SVG plus discrets entre l'unité extérieure, la PAC, C1, C2 et ECS ; en affichage vertical, aucune liaison.
- Éditeur visuel enrichi : disposition classique/épurée, liaisons, animations et badges des circulateurs, thème clair/sombre/auto et diagnostics.
- Indication optionnelle du fonctionnement des circulateurs C1 et C2.
- Diagnostics simplifiés : groupe Compresseur intégral avec comptages et durées sans décimales inutiles ; groupe PAC réduit ; groupe Circuits conservé ; suppression des groupes redondants Circulateurs et ECS de cette seule interface.

## Installation / mise à jour
1. Télécharger la version via HACS après publication de la release correspondante.
2. Redémarrer Home Assistant.
3. Modifier l’unique ressource JavaScript Lovelace en `/alfea-synoptique/pac-synoptique-card.js?v=1.5.12` et supprimer toute ancienne ressource `/local/pac-synoptique-card.js`.
4. Ouvrir l'éditeur visuel de la carte et choisir « Épurée ».

## Compatibilité
Aucune commande BSB-LAN ou configuration de la PAC modifiée. Affichage uniquement. Les versions antérieures du synoptique ne reconnaissent pas les nouvelles propriétés YAML tant que la ressource JavaScript n'a pas été mise à jour.
