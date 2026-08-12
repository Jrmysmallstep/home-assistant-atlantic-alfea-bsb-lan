# Atlantic Alfea BSB-LAN pour Home Assistant

Intégration personnalisée Home Assistant pour piloter et surveiller une pompe à chaleur **Atlantic Alféa** via **BSB-LAN**.

> Version actuelle : **1.3.0**

## Fonctionnalités

- Mode global de la PAC : **Arrêt / Chauffage / Rafraîchissement**.
- Deux entités Climate, une pour chaque circuit hydraulique.
- Températures ambiantes et consignes effectives des circuits.
- Prise en compte des régimes Confort / Réduit du régulateur.
- Gestion et suivi de l'**ECS** : mode, température ballon, état de charge, pompe et appoint électrique lorsque les paramètres sont disponibles.
- État et modulation du compresseur.
- Températures départ, retour, consigne départ et température extérieure.
- Compteur d'énergie totale BSB-LAN.
- Suivi des heures et démarrages du compresseur.
- Diagnostics : cycles courts, redémarrages rapprochés, démarrages fréquents et écart départ/consigne.
- Lecture de l'horloge PAC, détection d'une désynchronisation et bouton de synchronisation avec Home Assistant.
- Détection automatique des entités BSB-LAN avec possibilité de corriger l'association manuellement.

## Dérogation native

La V1.3.0 utilise les paramètres natifs de dérogation du régulateur au lieu de modifier les programmations Confort / Eco.

**Limitation de sécurité de la V1.3.0 :** la création d'une dérogation depuis l'entité Climate Home Assistant est volontairement limitée au **rafraîchissement** et à une demande **plus froide**. Le comportement équivalent en chauffage n'a pas encore été validé sur le bus et n'est donc pas activé dans cette version.

L'annulation d'une dérogation native est disponible lorsque les paramètres BSB correspondants sont détectés comme modifiables.

## Philosophie de fonctionnement

La programmation horaire reste gérée par la PAC. L'intégration ne remplace pas le programmateur du régulateur et conserve la PAC comme source de vérité pour les régimes Confort / Réduit.

## Prérequis

- Home Assistant avec MQTT fonctionnel.
- Une passerelle **BSB-LAN** déjà intégrée à Home Assistant.
- Les paramètres BSB nécessaires publiés sous forme d'entités Home Assistant.

L'intégration détecte automatiquement les paramètres connus. Les paramètres obligatoires qui ne peuvent pas être associés sans ambiguïté sont demandés pendant la configuration.

## Documentation BSB-LAN

La documentation officielle BSB-LAN est la référence principale pour l'installation, la configuration de la passerelle et la compréhension des paramètres du bus :

- **Documentation BSB-LAN en français :** https://docs.bsb-lan.de/fr/index.html

Les numéros de paramètres et leur disponibilité peuvent varier selon le régulateur, le firmware et la configuration de l'installation. En cas de doute, vérifiez toujours le paramètre concerné dans la documentation BSB-LAN et directement sur votre régulateur.

## Installation manuelle

1. Copiez le dossier :

   `custom_components/atlantic_alfea_controller/`

   dans le dossier `custom_components` de votre configuration Home Assistant.

2. Vous devez obtenir :

   `/config/custom_components/atlantic_alfea_controller/manifest.json`

3. Redémarrez Home Assistant.
4. Ouvrez **Paramètres → Appareils et services → Ajouter une intégration**.
5. Recherchez **Atlantic Alfea BSB-LAN**.
6. Laissez la détection automatique associer les paramètres BSB-LAN, puis vérifiez les éventuels paramètres non détectés.

## Principaux paramètres BSB-LAN

| Fonction | Circuit 1 | Circuit 2 |
|---|---:|---:|
| Mode chauffage | 700 | 1000 |
| Consigne chauffage Confort | 710 | 1010 |
| Consigne chauffage Réduit | 712 | 1012 |
| Mode rafraîchissement | 901 | 1201 |
| Consigne rafraîchissement Confort | 902 | 1202 |
| Consigne rafraîchissement Réduit | 903 | 1203 |
| Température ambiante | 8740 | 8770 |
| Consigne ambiante effective | 8741 | 8771 |
| État chauffage | 8000 | 8001 |
| État rafraîchissement | 8004 | 8025 |
| État dérogation | 701 | 1001 |

Autres paramètres importants :

- `0` : date et heure de la PAC
- `1600` : mode ECS
- `1610` : consigne nominale ECS
- `1612` : consigne réduite ECS
- `8003` : état ECS
- `8006` : état général générateur/PAC
- `8400` : état compresseur
- `8410` : température retour PAC
- `8411` : consigne départ PAC
- `8412` : température départ PAC
- `8413` : modulation compresseur
- `8450` : heures compresseur
- `8451` : nombre de démarrages compresseur
- `8700` : température extérieure
- `8820` : pompe ECS
- `8821` : appoint électrique ECS
- `8830` : température ballon ECS
- `3113` : énergie électrique totale

## Mise à jour des données

L'intégration demande périodiquement à BSB-LAN de republier certains diagnostics qui doivent rester frais :

- `8411` toutes les 5 minutes ;
- `3113`, `8450` et `8451` toutes les 15 minutes ;
- l'horloge (`0`) une fois par heure.

Ces demandes sont des lectures et ne modifient pas les réglages de la PAC.

## Avertissement

Projet communautaire non officiel, sans affiliation avec Atlantic ou le projet BSB-LAN. Les commandes écrites sur le bus sont volontairement limitées aux comportements qui ont été validés sur l'installation utilisée pour développer cette intégration.
