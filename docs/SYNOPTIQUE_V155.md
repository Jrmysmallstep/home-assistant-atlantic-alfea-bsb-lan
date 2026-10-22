# Synoptique Atlantic Alféa — V1.5.12

## Installation via HACS

Le JavaScript est automatiquement installé dans l'intégration :
`custom_components/atlantic_alfea_controller/www/pac-synoptique-card.js`.

Home Assistant sert l'asset à l'adresse :
`/alfea-synoptique/pac-synoptique-card.js?v=1.5.13`.

Redémarrer Home Assistant après HACS, puis ajouter **une unique ressource**
**Module JavaScript** dans Paramètres → Tableaux de bord → Ressources.
Supprimer toute ancienne ressource `/local/pac-synoptique-card.js` pour
éviter que l'ancien code ne s'enregistre avant le nouveau.

## Éditeur visuel Lovelace (V1.5.12)

1. Dans le tableau de bord, cliquer sur le crayon **Modifier**.
2. Ajouter la carte **PAC Synoptique — Atlantic Alféa (lecture seule)**,
   ou ouvrir la configuration de la carte existante.
3. L'**éditeur visuel** s'affiche automatiquement (le YAML reste disponible
   via le bouton d'édition de code de Home Assistant).
4. Dans **Apparence du synoptique**, choisir :
   - **Automatique (thème Home Assistant)** — valeur `auto`, défaut ;
   - **Clair** — valeur `light` ;
   - **Sombre** — valeur `dark`.
5. Cocher/décocher **Afficher les diagnostics complémentaires**.
6. Enregistrer. L'aperçu se met à jour avant l'enregistrement.

La sélection et la case sont les **seuls réglages du composant**, toutes les
commandes PAC sont volontairement absentes. Pour la largeur, utiliser l'onglet
**Disposition** de Home Assistant.

Les anciennes cartes configurées en YAML conservent leurs propriétés. Les
`entities` personnalisées éventuelles ne sont pas réinitialisées par l'éditeur.

## Dispositions responsive — V1.5.13

Depuis **Modifier la carte → Orientation**, trois choix sont proposés :

- **Automatique** (`layout_orientation: auto`) : horizontal en largeur suffisante,
  vertical lorsque la carte se rétrécit. Le critère est la largeur de la carte.
- **Paysage** (`layout_orientation: landscape`) : toujours horizontal, avec
  défilement horizontal intégré lorsque l'écran est trop étroit.
- **Portrait** (`layout_orientation: portrait`) : toujours vertical,
  adapté à un affichage mobile.

Ces choix s'ajoutent aux présentations Classique / Épurée et aux thèmes
Automatique / Clair / Sombre. Les réglages existants restent compatibles.

**Performances :** aucun chargement d'image externe ; le ventilateur, les
échangeurs et les flux sont composés en SVG inline/CSS. Les préférences
`prefers-reduced-motion` sont respectées. Le composant reste en lecture seule.

**Capteurs :** les 65 correspondances d'entités présentes dans la V1.5.12
sont intégralement conservées, y compris les capteurs masqués dans les
diagnostics repliables. Aucun capteur additionnel nécessaire.

## Carte YAML

```yaml
type: custom:pac-synoptique-card
title: Atlantic Alféa Extensa Duo
show_diagnostics: true
grid_options:
  columns: full
  rows: auto
theme_mode: auto
layout_orientation: auto
layout_style: clean
show_links: true
animate_flows: true
show_pump_badges: true
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

## V1.5.12 — Éditeur enrichi et diagnostics allégés

Le mode `layout_style: clean` affiche des liaisons fines en disposition horizontale et aucune liaison en disposition verticale (largeur de carte inférieure ou égale à 900 px). `layout_style: classic` conserve le schéma original. `show_links`, `animate_flows` et `show_pump_badges` sont configurables dans l'éditeur visuel ; thème automatique/clair/sombre et diagnostics restent disponibles.

Diagnostics : compresseur complet (comptages et durées sans décimales), PAC simplifiée, circuits C1 et C2 conservés. Les groupes séparés « Capteurs complémentaires / circulateurs » et « Eau chaude sanitaire » ne sont plus affichés ; leurs entités ne sont pas supprimées.
