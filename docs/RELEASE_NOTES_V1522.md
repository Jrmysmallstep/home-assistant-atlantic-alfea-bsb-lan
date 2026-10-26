# Atlantic Alféa BSB-LAN V1.5.22 — synoptique Aérien

Nouveau style graphique optionnel **Aérien**, directement inclus dans la carte
Lovelace et dans l'intégration HACS. Les styles Classique et Épurée restent inchangés.

## Présentation
- COMP de face, carter simplifié **sans grilles latérales ni logo** ;
  quatre pales SVG identiques en rotation autour d'un centre fixe.
- Échangeurs froid et chaud dessinés avec le même contour que le COMP.
- Fond uni, palette liée au thème Home Assistant ; cadres et canalisations fins.
- Ventilateur, échangeurs et liaisons toujours animés selon états confirmés ;
  les connexions en attente restent grises et statiques.
- Jauge de modulation conservée, transition douce de la largeur.
- Portrait automatique et forcé sans liaisons qui traversent les cartes.

## Fidélité aux entités
65 correspondances conservées, les deux climats réversibles, le mode natif
AUTO/ECO forcé/Confort forcé, l'état BSB-LAN **brut**, les circulateurs,
températures, ECS, alarmes, diagnostics, dérogations.
Aucune puissance, vanne, pression ou aller/retour hypothétique ajouté.
Pas de modification des commandes PAC, des modes ou des programmations.

## Installation
1. Mettre l'intégration à jour depuis HACS vers V1.5.22, puis redémarrer HA.
2. Actualiser la ressource JS (type Module JavaScript) :
   `/alfea-synoptique/pac-synoptique-card.js?v=1.5.22`
3. Choisir **Présentation des circuits → Aérien** dans l'éditeur,
   ou définir `layout_style: aerien` dans le YAML.
4. Vider le cache frontal si l'ancien graphisme persiste.

**Lecture seule.** Tests hors ligne ; vérification visuelle sur l'installation réelle conseillée.
