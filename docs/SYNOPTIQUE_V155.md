# Synoptique Atlantic Alféa — V1.5.6

## Installation via HACS

Le JavaScript est automatiquement installé dans l'intégration :
`custom_components/atlantic_alfea_controller/www/pac-synoptique-card.js`.

Home Assistant sert l'asset à l'adresse :
`/alfea-synoptique/pac-synoptique-card.js?v=1.5.6`.

Redémarrer Home Assistant après HACS, puis ajouter **une unique ressource**
**Module JavaScript** dans Paramètres → Tableaux de bord → Ressources.
Supprimer toute ancienne ressource `/local/pac-synoptique-card.js` pour
éviter que l'ancien code ne s'enregistre avant le nouveau.

## Carte YAML

```yaml
type: custom:pac-synoptique-card
title: Atlantic Alféa Extensa Duo
show_diagnostics: true
grid_options:
  columns: full
  rows: auto
theme_mode: auto
```

### Thèmes

Le réglage `theme_mode` accepte `auto` (valeur par défaut), `light` et `dark`.

- **auto** : la carte utilise `--ha-card-background`, `--primary-text-color`,
  `--secondary-text-color`, `--divider-color` et les autres variables du thème HA ;
  elle s'adapte au changement clair/sombre du profil.
- **light** : force un rendu clair.
- **dark** : force un rendu sombre proche de la carte historique.

La palette des états Chauffage, Rafraîchissement et Alarmes reste lisible
dans les trois modes. La configuration ne commande jamais la PAC.

Utiliser de préférence une vue Panneau ou une section pleine largeur.

## Comportement

Le synoptique lit uniquement les états Home Assistant. Aucun service n'est
appelé depuis ce composant. Les sorties actives utilisent l'attribut
`hvac_action` des deux entités `climate` et le capteur `ECS - Production`.
Une programmation Chauffage ne prouve pas qu'un circuit chauffe actuellement.

Les diagnostics 10112/10122 pilotent l'affichage du programme :
`1 - Allure Réduit` = Éco, `2 - Allure Confort` = Confort.
L'état 8000/8001 (ex. 122 « Limitation de la température ambiante »)
reste disponible en diagnostic et ne doit pas être utilisé seul comme régime.

Mesures départ/retour : 8412 / 8410, communes à la PAC.
Consignes ambiantes effectives : 8741 / 8771, sur Climate.
ECS : 8830 (temp. ballon), 8820 (pompe), 8821 (appoint).
Alarmes : cycles courts, redémarrages rapprochés, fréquence, écart départ,
horloge. Les diagnostics non disponibles restent indiqués comme tels.

La vue est responsive et les alarmes/diagnostics sont repliés par défaut.

## Dépannage

- Carte inconnue : vérifiez l'unique ressource JS et redémarrez HA.
- Erreur 404 sur l'asset : l'intégration doit avoir été chargée après le redémarrage.
- Ancien visuel : supprimez l'ancien `/local/` dans les Ressources et actualisez le cache.
- Entités absentes : activez les diagnostics nécessaires et contrôlez leurs noms Home Assistant.
