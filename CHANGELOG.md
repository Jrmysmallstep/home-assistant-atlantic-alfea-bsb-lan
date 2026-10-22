# Changelog

## 1.5.16 — Afficher les états BSB-LAN sans interprétation

- Annule uniquement la transformation du badge des circuits en « Régime : Confort/Éco ».
- Affiche à nouveau le libellé d'origine remonté par les capteurs « C1/C2 - État actuel ».
- 10112/10122 restent disponibles séparément dans les diagnostics.
- Préserve intégralement la correction des connexions en mode portrait de V1.5.15.
- Aucune commande PAC, aucune programmation native et aucun attribut Climate modifié.


## 1.5.15 — Portrait et programme Confort / Éco sur le synoptique

- Portrait/Auto : liaisons verticales courtes sans collecteur latéral superposé.
- Cartes RDC, Étage, ECS ajustées à la largeur des smartphones.
- Régime Confort/Éco prioritaire via les programmes actifs 10112/10122 ; valeurs
  d'état BSB brutes conservées en diagnostic.
- 65 correspondances d'entités conservées ; aucune commande PAC modifiée.
- V1.5.14 paysage conservé.


## 1.5.14 — Raccordements PAC → circuits et ECS en paysage

- Corrige le débordement des styles CSS des modes Portrait / Automatique sur le mode Paysage.
- La hauteur des liaisons entre PAC et RDC / Étage / ECS reste alignée sur les trois sorties.
- Les six groupes de sélecteurs CSS concernés sont maintenant préfixés individuellement.
- Test de non-régression des sélecteurs et du code visuel.
- Conserve les 65 correspondances d'entités, thèmes, orientations, animations, diagnostics et alarmes.
- Aucun changement fonctionnel de la PAC.


## 1.5.13 — Synoptique V2.8 compact et responsive

- Nouvelle configuration `layout_orientation: auto | landscape | portrait`, également accessible via l'éditeur visuel.
- Carte moins haute et blocs plus compacts, sans suppression de champs.
- Paysage forcé avec défilement horizontal sur écran trop étroit.
- Portrait optimisé pour smartphone, transitions CSS et liaisons verticales en mode classique.
- Les modes thème Automatique/Clair/Sombre et les présentations Classique/Épurée restent disponibles.
- 65 correspondances d'entités conservées, y compris diagnostics, alarmes et circulateurs.
- Aucune image externe, SVG incorporés dans le JavaScript ; filtres animés remplacés par animation d'opacité.
- Mouvements arrêtés si l'utilisateur demande des animations réduites.
- Aucun changement côté régulation, chauffage, rafraîchissement, ECS, programmation ou dérogations.


## 1.5.11 — Retours BSB natifs et synoptique adaptatif

- Restaure les états natifs BSB-LAN des circuits 1/2 (chauffage 8000/8001 ; refroidissement 8004/8025) sans interprétation Climate, et conserve leurs identifiants Home Assistant.
- Le synoptique affiche les valeurs « État actuel » directement dans la pastille de chacun des deux circuits.
- Affiche les circulateurs C1/C2 dans Diagnostics et dans une section dédiée aux capteurs complémentaires.
- Favorise le synoptique horizontal compact selon la largeur de la carte ; disposition verticale avec connexions COMP → PAC → C1/C2/ECS visibles et animées si nécessaire.
- Aucune modification des commandes PAC ou des programmations et dérogations natives.


## 1.5.10 — Circulateurs affichés sur le synoptique

- Ajoute les circulateurs C1 et C2 au synoptique (découverte des capteurs binaires existants).
- Affiche « Circulateur en marche / arrêté / indisponible » sur chaque bloc Circuit plutôt que « Régime : indéterminé ».
- Ajoute deux lignes « Circulateur » aux diagnostics Circuits 1 et 2.
- Conserve les capteurs « État actuel » basés sur Climate et les régimes BSB dans leurs attributs.
- Aucun changement des commandes PAC, programmations et dérogations.


## 1.5.9 — États des circuits et circulateurs

- Les capteurs C1 et C2 « État actuel » affichent Chauffage, Refroidissement, En attente ou Arrêt d'après l'action Climate, plutôt que le régime BSB brut.
- Le régime BSB natif reste disponible dans les attributs diagnostics des deux capteurs.
- Un état BSB manquant ne masque plus, à lui seul, le retour valide d'un circulateur.
- Surveillance en lecture seule : C1 (relais QX1, paramètre 9031) et C2 (pompe, paramètre 8760), avec retour MQTT de secours.
- Vérifications GitHub mises à jour. Aucune modification des commandes, consignes, programmations ou dérogations PAC.


## 1.5.7 — Éditeur visuel Lovelace

- Éditeur visuel natif de la carte PAC Synoptique (sans extension graphique externe).
- Liste déroulante Apparence : Automatique / Clair / Sombre (valeur enregistrée `theme_mode`).
- Case à cocher d'affichage des diagnostics complémentaires (`show_diagnostics`).
- Mise à jour en temps réel de l'aperçu, événement `config-changed` conforme à Home Assistant.
- Les réglages antérieurs en YAML et les associations d'entités personnalisées sont conservés.
- Aucun changement dans le fonctionnement de la PAC, les alarmes, les animations ou les sécurités.


## 1.5.6 — Compatibilité thèmes Home Assistant

- Synoptique V2.4.0 : nouveau paramètre YAML `theme_mode: auto | light | dark`.
- Par défaut, fond, panneaux, contrastes, textes et bordures suivent les variables CSS du thème Home Assistant.
- Deux modes forcés : clair ou sombre, indépendamment de l'apparence de Home Assistant.
- Mise à jour du visuel lors du changement de thème sans modification d'entités.
- Géométrie d'origine, animations, Confort/Éco, alarmes et diagnostics inchangés.
- Aucun changement des commandes PAC, programmations et dérogations.


## 1.5.5 — Carte synoptique et programme Confort/Éco

- Carte Lovelace `pac-synoptique-card` V2.3.3 incluse directement dans l'intégration/HACS.
- Endpoint HTTP local `/alfea-synoptique/pac-synoptique-card.js` sans copier dans `/config/www`.
- Mise en page horizontale à angles droits ; zone PAC compacte, trois sorties RDC/Étage/ECS.
- Bloc haut supprimé ; mode Chauffage/Refroidissement dans le bloc PAC.
- Alarmes et diagnostics repliables indépendamment ; mentions en pied retirées.
- Animation des serpentins et du ventilateur indicative, uniquement liée aux états.
- Lecture Confort/Éco prioritaire via les programmes natifs 10112/10122 :
  `1 = Réduit/Éco`, `2 = Confort`.
- Distinction entre programme et état de régulation (ex. code 122 : limitation ambiante).
- Aucun changement dans les sélecteurs de consignes, programmations internes, modes ou dérogations PAC.
- Tests hors ligne Python et contrôles de syntaxe JavaScript lors des PR.


## 1.3.3

Correctif graphique HACS / Home Assistant.

- Remplacement de l’icône erronée par l’icône validée issue du fichier fourni pour le projet.
- Validation PNG et empreinte SHA-256 avant publication.
- Aucun changement fonctionnel PAC, ECS ou dérogation.

## 1.3.2

Correctif visuel de la V1.3.1.

- Remplacement de l’icône provisoire par l’icône Atlantic Alfea BSB-LAN définie pour le projet.
- Ajout du logo Atlantic Alfea BSB-LAN correspondant.
- Ressources de marque installées à la racine `brand/` et dans `custom_components/atlantic_alfea_controller/brand/` pour HACS / Home Assistant.
- Aucun changement de la logique PAC, ECS ou dérogation par rapport à la V1.3.1.

## 1.3.1

Version de consolidation de la branche 1.3 pour validation via HACS.

### Corrigé

- Classement plus clair des entités avec un préfixe cohérent `Circuit 1` / `Circuit 2`.
- Temporisation de 2 secondes après le dernier clic `+/- 0,5 °C` dans le Climate ; chaque nouveau clic relance les 2 s et une seule commande BSB finale est envoyée.
- Le `water_heater` n'affiche plus le code numérique brut dans `etat_ecs_bsb` : `Charge, température nominale` remplace `99 - Charge, température nominale`.

### HACS / Home Assistant

- Ajout d'une icône locale pour HACS et Home Assistant 2026.3+.
- Ajout des liens `documentation` et `issue_tracker` au manifeste.

## 1.3.0

Première publication GitHub de la branche 1.3.

### Ajouté

- Intégration Home Assistant complète sous `custom_components/atlantic_alfea_controller`.
- Détection automatique des entités BSB-LAN avec association manuelle en cas d'ambiguïté.
- Mode global Arrêt / Chauffage / Rafraîchissement.
- Entités Climate pour les circuits 1 et 2.
- Lecture des consignes effectives 8741 / 8771.
- Gestion et suivi de l'ECS.
- Suivi du compresseur, de sa modulation, de ses heures et de ses démarrages.
- Surveillance des cycles courts, redémarrages rapprochés, démarrages fréquents et écarts départ/consigne.
- Lecture, surveillance et synchronisation de l'horloge PAC via le paramètre BSB 0.
- Polling ciblé de certains paramètres de diagnostic via MQTT.
- Suivi de la dérogation native des deux circuits et commande d'annulation lorsqu'elle est disponible.

### Dérogation native

- Création d'une dérogation depuis Home Assistant activée uniquement en mode rafraîchissement.
- Seule une demande plus froide a été validée et est autorisée dans cette version.
- Les programmations Confort / Réduit de la PAC ne sont pas remplacées par Home Assistant.

### Sécurité

- Les paramètres de commande déjà associés restent épinglés afin qu'une redétection automatique ne redirige pas une écriture vers une mauvaise entité.
- Une ambiguïté sur une entité de commande entraîne une demande de configuration manuelle plutôt qu'une écriture automatique.
