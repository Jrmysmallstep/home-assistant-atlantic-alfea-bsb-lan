# Atlantic Alféa BSB-LAN pour Home Assistant

**Pilotez et surveillez votre pompe à chaleur Atlantic Alféa depuis Home Assistant, tout en conservant la régulation native de la PAC.**

Cette intégration communautaire relie **Home Assistant** à une **pompe à chaleur Atlantic Alféa Extensa Duo** via une passerelle **BSB-LAN**. Elle rassemble les températures, les états de fonctionnement, les commandes des deux circuits et l'eau chaude sanitaire (ECS) dans une interface unique.

Elle s'adresse aux personnes qui souhaitent suivre leur installation au quotidien, ajuster certaines consignes et mieux comprendre le fonctionnement de leur PAC, **sans remplacer son programmateur d'origine**.

**Version stable : V1.5.25** · **Synoptique : V2.9.7** · Projet non officiel

## 📸 Aperçu

![Aperçu du synoptique Atlantic Alféa : compresseur, PAC, circuits RDC/étage et eau chaude sanitaire](docs/images/pac-synoptique-apercu.svg)

*Illustration avec des valeurs fictives. Les données réelles proviennent des entités de votre installation.*

La carte **PAC Synoptique** affiche d'un coup d'œil le compresseur, la PAC, les deux circuits de chauffage/rafraîchissement, l'ECS et les diagnostics. Elle fonctionne sur ordinateur et smartphone, avec plusieurs présentations et thèmes.

## ✨ Fonctionnalités

### 🌡️ Piloter les deux circuits de chauffage et de rafraîchissement

- **Deux thermostats Home Assistant indépendants** : circuit 1 (généralement RDC) et circuit 2 (généralement étage).
- **Mode global** : arrêt, chauffage ou rafraîchissement des deux circuits, avec contrôle des retours d'état.
- **Modes locaux** : chauffage, rafraîchissement ou arrêt de chaque circuit, dans les limites du mode global.
- **Températures et consignes** : température ambiante, consigne effective et réglage des consignes programmées Confort/Éco.
- **Dérogations temporaires** : ajustement ponctuel de la température avec retour à la programmation de la PAC après expiration.

### 🚿 Surveiller l'eau chaude sanitaire (ECS)

- Température du ballon et état de production d'eau chaude.
- Mode et consignes ECS lorsque les paramètres sont disponibles.
- Suivi de la commande de vanne trois voies **Q3**, pour les installations compatibles et correctement configurées.

### 📊 Comprendre le fonctionnement de la PAC

- État du compresseur, modulation, heures de fonctionnement et démarrages.
- Températures de départ, de retour et température extérieure.
- États des circulateurs, des circuits et de la production ECS.
- Énergie totale remontée par BSB-LAN, si disponible.
- Diagnostics et alertes : cycles courts, redémarrages rapprochés, écarts de température et synchronisation de l'horloge.

### 🗓️ Consulter les programmes horaires natifs

L'intégration peut **lire à la demande** les programmes hebdomadaires enregistrés dans la PAC :

| Programme | Disponibilité |
| --- | --- |
| Chauffage circuit 1 (RDC) | Lecture sur 7 jours |
| Chauffage circuit 2 (étage) | Lecture sur 7 jours |
| Eau chaude sanitaire | Lecture sur 7 jours |
| Rafraîchissement circuit 1 | Lecture sur 7 jours |
| Rafraîchissement circuit 2 | Lecture sur 7 jours |

Les horaires peuvent être visualisés dans le synoptique ou dans la carte dédiée **PAC Programmes**.

**Important : les programmes horaires sont en lecture seule.** Home Assistant ne réécrit pas les plages horaires de la PAC. Leur actualisation est déclenchée manuellement et utilise l'interface HTTP JSON de BSB-LAN, sans ajouter 35 paramètres à la liste MQTT.

## 🚀 Améliorations de la V1.5.25

Cette version apporte notamment :

- **Programmes horaires natifs** : lecture et comparaison visuelle des cinq programmes hebdomadaires (chauffage, ECS et rafraîchissement).
- **Synoptique V2.9.7** : affichage plus complet, adaptation aux écrans mobiles, choix des présentations Classique, Épurée ou Aérien.
- **Vanne Q3** : visualisation de la commande de dérivation ECS/chauffage sur les installations compatibles.
- **Remontées MQTT** : améliorations de l'initialisation et de la réception directe de certains états.
- **Diagnostics** : meilleure distinction entre états réellement lus, régimes horaires et informations indisponibles.

Pour l'historique détaillé des développements et des bêtas, voir [les notes historiques du README](docs/README_HISTORIQUE_V1525.md).

## 🔌 Comment fonctionne l'intégration ?

```text
Pompe à chaleur Atlantic Alféa
             │ bus BSB
             ▼
      Passerelle BSB-LAN
             │
       MQTT / HTTP JSON
             │
             ▼
       Home Assistant
      ├─ Thermostats C1 / C2
      ├─ Capteurs et diagnostics
      ├─ Carte PAC Synoptique
      └─ Programmes hebdomadaires (lecture)
```

La **PAC reste responsable de sa régulation et de ses horaires**. L'intégration transmet certaines commandes prévues par le régulateur, lit les états BSB-LAN et les présente dans Home Assistant.

Les disponibilités et les réactions des commandes dépendent du modèle, du régulateur et des paramètres réellement exposés.

## ✅ Prérequis et compatibilité

- Une installation **Home Assistant** fonctionnelle.
- Une passerelle **BSB-LAN** reliée à la PAC et accessible sur le réseau.
- **MQTT** configuré pour publier les paramètres nécessaires dans Home Assistant.
- Pour l'importation des programmes natifs et certaines commandes : l'**adresse HTTP(S) JSON de BSB-LAN** renseignée dans les options de l'intégration.

**Matériel de référence testé :** Atlantic Alféa Extensa Duo, régulateur **RVS21.831F** (famille 211, variante 127).

D'autres PAC Atlantic Alféa ou régulateurs Siemens RVS pourraient fonctionner, **sans garantie de compatibilité** : les numéros de paramètres et leurs significations peuvent varier.

## 📦 Installation avec HACS

1. Dans **HACS**, ouvrez le menu **⋮ → Dépôts personnalisés**.
2. Ajoutez ce dépôt en choisissant le type **Intégration** :

   ```text
   https://github.com/Jrmysmallstep/home-assistant-atlantic-alfea-bsb-lan
   ```

3. Recherchez **Atlantic Alfea BSB-LAN** dans HACS et installez-le.
4. **Redémarrez Home Assistant**.
5. Ouvrez **Paramètres → Appareils et services → Ajouter une intégration** et sélectionnez **Atlantic Alfea BSB-LAN**.
6. Vérifiez les paramètres BSB-LAN détectés et complétez ceux qui ne peuvent pas être associés automatiquement.

**Installation manuelle :** copiez le dossier `custom_components/atlantic_alfea_controller/` dans `/config/custom_components/`, puis redémarrez Home Assistant et ajoutez l'intégration.

## 🖥️ Ajouter les cartes au tableau de bord

### Carte PAC Synoptique

Dans **Paramètres → Tableaux de bord → Ressources**, ajoutez une ressource de type **Module JavaScript** :

```text
/alfea-synoptique/pac-synoptique-card.js?v=1.5.25
```

Puis ajoutez une carte via l'éditeur visuel, ou utilisez :

```yaml
type: custom:pac-synoptique-card
title: Atlantic Alféa Extensa Duo
theme_mode: auto
layout_orientation: auto
layout_style: aerien
show_diagnostics: true
```

La carte propose les orientations automatique, paysage et portrait, ainsi que les styles Classique, Épurée et Aérien. **Le synoptique est une interface de supervision : il n'envoie pas de commande de régulation à la PAC.**

### Carte Programmes horaires (facultative)

Ajoutez une seconde ressource **Module JavaScript** :

```text
/alfea-synoptique/pac-programmes-card.js?v=1.5.25
```

Puis créez une carte manuelle :

```yaml
type: custom:pac-programmes-card
title: Programmes horaires PAC
```

La carte présente les cinq programmes et permet de demander leur **relecture** via Home Assistant. Cette action ne modifie pas les horaires dans le régulateur.

## ⚙️ Configuration et précautions

**Lecture des programmes :** renseignez l'option **Adresse BSB-LAN JSON**, puis utilisez le bouton **Programmes natifs - Actualiser**. Les cinq programmes correspondent à 35 lectures HTTP `/JQ` espacées ; aucune écriture `/JS` n'est envoyée pour cette fonction.

**Vanne Q3 :** le paramètre `8820` représente la **commande** de la vanne de dérivation sur les installations où `5731 = 2`. Confirmez cette configuration avant d'activer l'option correspondante. **Il ne s'agit pas d'un capteur de position mécanique réelle.**

**Paramètres MQTT :** la passerelle BSB-LAN dispose d'une limite de paramètres publiés en continu ; la lecture des programmes natifs a été conçue pour ne pas consommer ces emplacements supplémentaires.

**Sécurité :** vérifiez toujours les paramètres sur votre propre régulateur. Les commandes de changement de saison et certains comportements dépendent de la configuration matérielle. Évitez toute écriture de paramètres non validés sur votre installation.

## 📚 Documentation et ressources

- [Documentation détaillée du synoptique](docs/SYNOPTIQUE_V155.md)
- [Historique technique et notes des versions précédentes](docs/README_HISTORIQUE_V1525.md)
- [Documentation officielle BSB-LAN en français](https://docs.bsb-lan.de/fr/index.html)
- [Signaler un problème ou proposer une amélioration](https://github.com/Jrmysmallstep/home-assistant-atlantic-alfea-bsb-lan/issues)
- [Versions publiées](https://github.com/Jrmysmallstep/home-assistant-atlantic-alfea-bsb-lan/releases)

---

**Projet communautaire non officiel**, sans affiliation avec Atlantic ni avec les développeurs de BSB-LAN. Les essais sur une installation de référence ne garantissent pas un fonctionnement identique sur toutes les PAC.
