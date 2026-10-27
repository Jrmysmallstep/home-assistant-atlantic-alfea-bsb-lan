<!-- Archive du README historique avant réorganisation de la page d'accueil en V1.5.25.
     Conservé pour référence ; certaines consignes de préversions et de publication
     sont obsolètes. Se reporter au README principal pour l'installation actuelle. -->

# Atlantic Alfea BSB-LAN pour Home Assistant

Intégration personnalisée Home Assistant pour piloter et surveiller une pompe à chaleur **Atlantic Alféa Extensa Duo** via **BSB-LAN**.

> Version stable : **1.5.25** — Synoptique V2.9.7, programmes natifs chauffage, ECS et rafraîchissement.

## Inclus dans V1.5.25 — V3V Q3 / synoptique

Sur une Alféa équipée d'une **vanne de dérivation ECS Q3** (paramètre
BSB-LAN **5731 = 2**), le paramètre **8820** correspond à la commande Q3 :
**1 → A / ECS**, **0 → B / chauffage**. Ces deux états ont été contrôlés
visuellement sur l'installation de référence le 26 octobre 2026.

- Nouveau capteur **« V3V - Commande »** : état `ECS` ou `Chauffage`,
  attribut `position_commandee` A/B. Il est **en lecture seule** et ne
  constitue **pas un retour de position mécanique**.
- La carte synoptique **V2.9.1** affiche le symbole hydraulique Q3 et la
  branche sélectionnée. L'animation des flux exige en plus des états
  de fonctionnement confirmés. Les mises en page portrait et Aérien sont prises
  en charge ; le badge reste visible en présentation Épurée.
- **Prérequis** : seul le paramètre **8820** doit être publié en continu dans
  Home Assistant. Pour éviter de dépasser la limite des 40 paramètres MQTT,
  activer **Configurer → Options → « Q3 est une vanne 3 voies ECS
  (5731 = 2) »** après avoir vérifié cette valeur une fois sur la PAC.
  Le paramètre 5731 n'a donc **pas besoin** d'être ajouté à la liste MQTT.
  Si une entité 5731 existe malgré tout, sa valeur réelle prévaut sur l'option.
  Si ni 5731 ni la confirmation manuelle ne sont disponibles, le capteur
  V3V reste indisponible.
- **V1.5.24 (correctif)** : le statut de commande 8820 est également écouté
  directement sur `BSB-LAN/+/+/8820/status` : aucune entité MQTT-discovery
  n'est nécessaire. L'attribut `source_commande` précise si l'information
  vient d'une entité Home Assistant ou du MQTT direct. La confirmation
  `q3_diverter_confirmed` reste indispensable en l'absence de 5731.
- Le capteur historique **« ECS - Pompe »** est conservé pour la compatibilité
  des installations existantes ; dans le synoptique, sa sortie 8820 est
  présentée comme **Q3** ou **V3V** selon les données disponibles.

**Cette évolution fait partie de la version stable V1.5.25.**



## Version stable V1.5.25 — programmes natifs de rafraîchissement (synoptique V2.9.7)

Lecture **réelle validée sur PAC Atlantic Alféa Extensa Duo** le 27 octobre 2026 :
14 réponses JSON `/JQ` sans erreur, pour les sept jours des deux circuits.

- **Rafraîchissement RDC** : `11000` à `11006`, 10:30–20:30 sur les sept jours.
- **Rafraîchissement étage** : `11010` à `11016`, 11:30–21:30 sur les sept jours.
- Deux nouveaux capteurs de diagnostic, avec `jours`, `derniere_importation` et état d'erreur.
- Le synoptique propose deux cases supplémentaires **Froid RDC** et **Froid étage**,
  désactivées par défaut pour préserver la comparaison initiale RDC/Étage/ECS.
- La carte autonome `pac-programmes-card` dispose de cinq onglets.
- Le bouton d'actualisation lit désormais **35 journées** via HTTP `/JQ`,
  avec une pause de 200 ms entre lectures ; **aucune écriture /JS** et
  aucun nouveau paramètre MQTT.
- Cette version est **en développement**, à tester dans Home Assistant.
  Ne pas fusionner la PR brouillon avant validation du rendu réel.

**Publication stable** : tag `v1.5.25` sur `main`, release GitHub normale
(non préversion), après fusion de la branche `release/v1.5.25`.

## Préversion V1.5.25b5 — comparaison regroupée par jour (synoptique V2.9.6)

À la demande de l'utilisateur, les trois calendriers séparés de la bêta 3
ont été réunis dans **un seul graphique hebdomadaire** :

- **Sept groupes : lundi à dimanche**, avec une seule graduation 0–24 h commune.
- Chaque jour affiche **une ligne par programme coché** (RDC, étage, ECS),
  sur la même échelle, les uns sous les autres, **sans superposition**.
- Les horaires de chaque plage restent visibles à la minute sous la ligne.
- Les couleurs et les cases à cocher sont conservées, ainsi que le bouton
  **↻ Actualiser** placé à côté.
- Les 3 programmes sélectionnés produisent 21 lignes ; 2 programmes,
  14 lignes ; un programme, 7 lignes. Le graphique conserve toujours
  exactement **7 jours** et une seule graduation.
- Les correctifs des bêtas précédentes (MQTT, diamètre des tuyaux Aérien)
  restent inclus.

**Préversion de test :** tag `v1.5.25b5` sur
`feature/native-weekly-programs-readonly`, avec « Set as a pre-release ».
Rendu final à valider dans Home Assistant.

## Préversion V1.5.25b4 — tuyauterie homogène (synoptique V2.9.5)

Suite à une capture du raccordement de la vanne 3 voies Q3,
le thème **Aérien** applique désormais une épaisseur visible de
**10 px** aux conduites SVG, aux raccords gris de Q3 et aux chemins
colorés actifs. La propriété SVG `vector-effect: non-scaling-stroke`
empêche l'étirement des frises SVG de déformer les diamètres des
segments horizontaux et verticaux. Les autres styles et les
fonctionnalités BSB-LAN restent inchangés.

**Tag à créer pour tester :** `v1.5.25b4` sur
`feature/native-weekly-programs-readonly`, en préversion GitHub.
Le rendu doit encore être vérifié sur le synoptique réel.

## Préversion V1.5.25b3 — comparaison des horaires (synoptique V2.9.4)

Suite au premier essai réel de la bêta 1, la visualisation intégrée
dans « Diagnostics et capteurs complémentaires » a été repensée :

- **Cases à cocher RDC, Étage et ECS** : afficher un, deux ou trois
  programmes simultanément (au moins un doit rester coché).
- **Chaque programme possède ses propres sept frises horaires** ;
  aucune superposition de circuits sur une même ligne.
- Frises graduées de 0 h à 24 h, repères toutes les heures et
  étiquettes toutes les 3 heures ; chaque créneau est aussi indiqué
  avec ses heures et minutes exactes.
- **Bouton « ↻ Actualiser » dans la même ligne que les cases à cocher**,
  relié au bouton de lecture BSB-LAN déjà créé par l'intégration.
- Trois couleurs pour distinguer chauffage RDC, étage et ECS.
- La bêta 3 contient aussi le correctif de démarrage MQTT de la bêta 2.

**Tag de préversion à publier :** `v1.5.25b3` depuis
`feature/native-weekly-programs-readonly` (et non `main`).
La bêta 1 déjà installée reste inchangée jusqu'à mise à jour via HACS.

## Correctif de préversion V1.5.25b2 — démarrage MQTT

La bêta 1 pouvait échouer à l'initialisation avec
`mqtt_not_setup_cannot_subscribe` si les abonnements directs aux
circulateurs (9031/8760) et à la vanne Q3 (8820) étaient créés avant que
Home Assistant ait initialisé MQTT.

La bêta 2 déclare `mqtt` comme dépendance à initialiser avant
l'intégration lorsqu'elle est disponible (`after_dependencies`),
diffère les abonnements jusqu'au chargement du composant, et laisse
les autres entités ainsi que l'importation HTTP des programmes se
charger même si MQTT est temporairement absent. Aucune publication
MQTT ni commande BSB supplémentaire.

**Préversion à publier :** tag `v1.5.25b2` sur la branche
`feature/native-weekly-programs-readonly`, avec l'option GitHub
« Set as a pre-release ». Ne pas réutiliser le tag bêta 1.

## En développement — importation des programmes natifs (V1.5.25)

La branche `feature/native-weekly-programs-readonly` ajoute une première
importation **en lecture seule**, indépendante des 40 paramètres MQTT.
Aucune programmation n'est écrite et Home Assistant ne remplace pas
le régulateur de la PAC.

**Prérequis** : dans les options de l'intégration, renseigner
**Adresse BSB-LAN JSON** avec l'adresse HTTP(S) de BSB-LAN.
Le bouton de diagnostic **« Programmes natifs - Actualiser »** lance
explicitement 35 lectures JSON `/JQ=...` (espacées de 200 ms).
Aucune lecture automatique au démarrage ni publication MQTT supplémentaire.

Cinq capteurs de diagnostic présentent ensuite un état `Chargé`, `Erreur`
ou `Non chargé`, ainsi que les plages par jour dans l'attribut `jours` :

| Capteur | Lundi | Mardi à dimanche |
| --- | --- | --- |
| Programme natif - Chauffage RDC | 501 | 501.1 à 501.6 |
| Programme natif - Chauffage étage | 521 | 521.1 à 521.6 |
| Programme natif - Eau chaude sanitaire | 561 | 561.1 à 561.6 |
| Programme natif - Rafraîchissement RDC | 11000 | 11001 à 11006 |
| Programme natif - Rafraîchissement étage | 11010 | 11011 à 11016 |

Chaque jour comporte jusqu'à trois créneaux `debut` / `fin` ;
`##:##-##:##` représente une plage inactive.
Une semaine est mise à jour uniquement si ses sept jours ont été lus et
validés. En cas d'erreur, le capteur affiche `Erreur` et conserve sa
dernière importation horodatée pour diagnostic (elle ne doit pas être
interprétée comme une lecture récente).

### Visualisation intégrée dans le synoptique (V1.5.25)

Dans **Diagnostics et capteurs complémentaires**, le synoptique comporte
désormais un bloc **« Programmes horaires natifs · Lecture seule »** dans la
**deuxième colonne**, à côté de « Circuits 1 & 2 / programmation ».

Cinq programmes sélectionnables **Chauffage RDC / Chauffage étage / ECS / Froid RDC / Froid étage**
s'affichent sur une même frise hebdomadaire 24 heures, avec une ligne par programme sélectionné. Le
programme ECS est bien inclus (paramètres 561 à 561.6).
Les valeurs proviennent exclusivement des capteurs de l'importateur BSB-LAN,
et sont actualisées lorsque le bouton de diagnostic
**« Programmes natifs - Actualiser »** est pressé.
Aucun changement de configuration de la carte synoptique existante n'est
nécessaire. Si les capteurs ne sont pas encore chargés, le panneau indique
« Non chargé » au lieu d'inventer des horaires.

La carte autonome ci-dessous reste facultative : le synoptique contient
désormais la visualisation demandée.

### Carte hebdomadaire Lovelace (prototype)

L'intégration expose également une carte `pac-programmes-card` :
cinq onglets (chauffage RDC, étage, ECS, rafraîchissement RDC, étage), sept jours, frise 24 h,
jusqu'à trois plages par jour et bouton d'actualisation.
Les entités sont détectées par leur paramètre source, ou peuvent être
renseignées explicitement si plusieurs installations coexistent.

Ajouter la ressource JavaScript **module** dans
Paramètres → Tableaux de bord → Ressources :

`/alfea-synoptique/pac-programmes-card.js?v=1.5.25b6`

Puis créer une carte manuelle :

```yaml
type: custom:pac-programmes-card
title: Programmes horaires PAC
```

Optionnellement, préciser `chauffage_c1`, `chauffage_c2`, `ecs`,
`rafraichissement_c1`, `rafraichissement_c2` et `refresh_button` avec les identifiants d'entité correspondants.
**Attention :** il s'agit d'un prototype non encore testé sur la PAC réelle.

Les programmes de **rafraîchissement C1/C2** ont été validés via les
14 paramètres JSON `/JQ=11000…11006` et `/JQ=11010…11016`.
Ils sont importés uniquement en lecture seule, à la demande.

**Essais requis avant publication** : vérifier les 35 réponses réelles de
BSB-LAN, la correspondance des jours, l'absence de commandes /JS et les
capteurs dans Outils de développement → États. Cette branche n'est pas une
release HACS.

## Synoptique Aérien (V1.5.22)

Une nouvelle présentation **Aérien** est incluse dans la carte Lovelace,
sans dépendance ni image externe : COMP **de face**, carter plat sans ailettes
latérales ni logo, quatre pales SVG strictement identiques, échangeurs
froid/chaud redessinés avec un cadre et un trait assortis. Le fond suit le
thème Home Assistant (clair/sombre) ; les cartes, les raccordements et les
bordures sont plus discrets.

- **Conservation des 65 correspondances d'entités** et de tous les champs :
  RDC/Étage (mode natif, état BSB brut, circulateur, température et consigne),
  ECS, COMP, PAC, dérogations et alarmes/diagnostics.
- Les animations sont indicatives : rotation COMP lorsque confirmé en marche,
  pulsation légère des échangeurs, liaisons rouge/bleu selon activité
  réelle de chauffage/rafraîchissement, ECS colorée pendant une production
  confirmée, jauge de modulation interpolée.
- Aucune pression frigorifique, puissance ou vanne fictive ; pas d'aller/retour
  hydraulique inventé. **La carte est uniquement en lecture seule**.
- **Classique** et **Épurée** restent disponibles comme avant.

Dans l'éditeur visuel, choisir **Présentation des circuits → Aérien** ou :
```yaml
type: custom:pac-synoptique-card
title: Atlantic Alféa Extensa Duo
layout_style: aerien
layout_orientation: auto
theme_mode: auto
show_diagnostics: true
grid_options:
  columns: full
  rows: auto
```
Après mise à jour HACS et redémarrage Home Assistant, versionner la ressource :
`/alfea-synoptique/pac-synoptique-card.js?v=1.5.22`.

## Aperçu de la carte Lovelace

![Aperçu du synoptique Atlantic Alféa dans Home Assistant : unité extérieure, module PAC, circuits RDC et Étage, ECS, alarmes et diagnostics](docs/images/pac-synoptique-apercu.svg)

*Illustration de l'interface avec des valeurs fictives, pour présenter l'organisation des informations. La carte réelle utilise les capteurs de votre installation.*

Le synoptique est **en lecture seule** : il présente les états du compresseur, de la PAC, des circuits de chauffage/rafraîchissement et de l'ECS, avec alarmes et diagnostics repliables. Son éditeur Lovelace permet de choisir une apparence **Automatique / Claire / Sombre** selon le thème Home Assistant.


## Matériel de référence

Cette intégration a été développée et testée sur une **Atlantic Alféa Extensa Duo** équipée d'un régulateur / carte **RVS21.831F** (**famille 211, variante 127**).

D'autres modèles Atlantic Alféa ou d'autres variantes de régulateurs Siemens RVS peuvent être compatibles, mais ils ne sont pas considérés comme validés tant que les paramètres BSB-LAN correspondants n'ont pas été vérifiés.

## Travail en cours — présélections Auto / ECO / Confort (branche de développement)

Cette branche ajoute une implémentation **expérimentale**, non publiée, de la lecture
et commande des régimes natifs par circuit directement depuis les thermostats
Home Assistant. Les versions HACS publiées restent inchangées.

- Paramètre 700 pour C1 et 1000 pour C2 : Auto = 1, ECO = 2, Confort = 3.
- Mode OFF individuel inchangé : lorsqu'un circuit est arrêté, le preset n'envoie
  aucune commande. Le mode protection (0) n'est jamais commandé par un preset.
- Le mode global chauffage/rafraîchissement est inchangé.
- Dans les options d'intégration, renseigner **Adresse BSB-LAN JSON**
  (par exemple `http://192.168.1.88`). Aucun emplacement MQTT nécessaire.
- Le statut est relu par `/JQ=700` ou `/JQ=1000` toutes les 60 secondes ;
  les écritures passent par un POST `/JS` et sont confirmées par relecture.
- Tant que l'adresse BSB-LAN n'est pas configurée, aucun preset n'est proposé.
- Le basculement automatique en fonction de la présence n'est **pas encore
  développé**. L'essai réel en chauffage puis rafraîchissement reste nécessaire.

**Ne pas diffuser comme release tant que les essais et tests de régression
n'ont pas été exécutés.**

## Fonctionnalités

- Mode global de la PAC : **Off / Chauffage / Refroidissement**. Une commande globale active les deux circuits dans le mode demandé ou les arrête tous les deux, avec vérification des retours d'état BSB-LAN.
- Deux entités Climate indépendantes : **C1 - Circuit 1** et **C2 - Circuit 2**, avec commandes locales Chauffage / Refroidissement / Off.
- Températures ambiantes et consignes effectives des circuits.
- Prise en compte des régimes Confort / Réduit (Éco) du régulateur.
- Réglage depuis Home Assistant des **huit consignes programmées** Confort / Éco (chauffage et rafraîchissement sur C1 et C2), sans modifier les horaires de la PAC.
- Dérogations temporaires natives en chauffage (**Plus chaud / Plus froid**) et en rafraîchissement (**Plus froid**, sens validé), avec durée paramétrable et retour au programme interne.
- Quatre capteurs de diagnostic supplémentaires en lecture seule : régime temporaire et programme actif pour C1 et C2.
- Libellés raccourcis et homogènes : **C1, C2, PAC, ECS, COMP**.
- Gestion et suivi de l'**ECS** : mode, température ballon, état de charge, pompe et appoint électrique lorsque les paramètres sont disponibles.
- État et modulation du compresseur.
- Températures départ, retour, consigne départ et température extérieure.
- Compteur d'énergie totale BSB-LAN.
- Suivi des heures et démarrages du compresseur.
- Diagnostics : cycles courts, redémarrages rapprochés, démarrages fréquents et écart départ/consigne.
- Lecture de l'horloge PAC, détection d'une désynchronisation et bouton de synchronisation avec Home Assistant.
- Détection automatique des entités BSB-LAN avec possibilité de corriger l'association manuellement.

## Carte Lovelace synoptique incluse (V1.5.16)

**Correctif V1.5.16 — données brutes préservées :**
les badges des circuits RDC et Étage affichent **le texte de l'entité
« C1/C2 - État actuel »**, par exemple « Régime chauffage Confort » ou
« Limitation de la température ambiante ». Ils ne remplacent pas ce retour
par une estimation Éco/Confort issue des programmes 10112/10122.

Les diagnostics conservent séparément les programmes horaires et l'état
de régulation. Les commandes, la logique Climate et l'affichage portrait
corrigé dans V1.5.15 restent inchangés.

### Modifications de V1.5.15

**Correctif V1.5.15 — smartphone :**
- Mode Portrait et mode Auto en largeur étroite : remplacement des fausses
  branches latérales par des raccordements verticaux courts COMP → PAC → sorties.
- Les cartes RDC, Étage et ECS occupent la largeur disponible, sans conduite
  superposée sur les cartes.
- Affichage du régime horaire 10112/10122 (**1 = Éco, 2 = Confort**) directement
  dans les cartes des circuits. L'état BSB (ex. « Limitation de la température
  ambiante ») est conservé dans les diagnostics.
- Le synoptique horizontal, les animations, les pompes, l'ECS, les alarmes et
  les commandes de l'intégration restent inchangés.

Pour forcer le portrait, ajoutez `layout_orientation: portrait` dans le YAML.
Pour adapter automatiquement aux tailles d'écran, utilisez
`layout_orientation: auto`.

### Modifications de la V1.5.14

**Correctif V1.5.14 :** les liaisons dessinées entre la PAC et les trois sorties
RDC / Étage / ECS retrouvent leur hauteur normale en paysage. Un sélecteur CSS
de la version précédente appliquait par erreur la hauteur réservée au mode
portrait au raccordement de droite, même sur grand écran. Aucune modification
des entités, des animations, des programmes ou des commandes.


### Synoptique V2.8.0 — compact et responsive

La V1.5.13 conserve les **65 correspondances d'entités** du synoptique V2.7.0,
ainsi que les animations, les alarmes, les diagnostics, les circulateurs et
les réglages de présentation précédents.

- **Orientation automatique** : disposition horizontale sur écran large et
  verticale lorsque la carte est étroite, même dans une petite section Lovelace.
- **Paysage** : maintien d'un synoptique COMP → PAC → RDC / Étage / ECS
  horizontal. Sur mobile étroit, un défilement horizontal évite les textes écrasés.
- **Portrait** : disposition verticale optimisée pour les smartphones.
- **Graphisme compact** : hauteurs et espaces réduits, sans retirer de valeurs.
- **Fluidité** : animation du ventilateur par transformation CSS, pulsation des
  échangeurs par opacité, animations de flux conservées et désactivées en
  cas de préférence d'accessibilité pour moins de mouvements.
- **Sans images externes** : HTML, CSS et formes SVG incorporées au code,
  aucune requête d'image pour afficher la carte.
- **Thèmes** : Automatique / Clair / Sombre, inchangés.

Le nouvel éditeur visuel expose **Orientation de la carte** (Automatique,
Paysage, Portrait). Les anciens dashboards sans réglage explicite bénéficient
du mode automatique.


Depuis la V1.5.12, l’éditeur visuel propose deux dispositions (Classique / Épurée), les raccordements en disposition horizontale, les animations facultatives et l'affichage des circulateurs. La disposition Épurée masque les raccordements en affichage vertical. Les diagnostics sont allégés sans supprimer les entités Home Assistant.

```yaml
type: custom:pac-synoptique-card
title: Atlantic Alféa Extensa Duo
theme_mode: auto
layout_orientation: auto  # auto / landscape / portrait
layout_style: clean
show_links: true
animate_flows: true
show_pump_badges: true
show_diagnostics: true
```


La carte **PAC Synoptique** est incluse dans l'intégration et installée par HACS, dans
`custom_components/atlantic_alfea_controller/www/pac-synoptique-card.js`.
Elle est **strictement en lecture seule** (COMP, PAC, chauffage RDC/Étage,
ECS, alarmes repliables, diagnostics et animations liées aux états).

Après la mise à jour via HACS, **redémarrez Home Assistant**, puis dans
**Paramètres → Tableaux de bord → Ressources**, ajoutez **une seule fois** la
ressource de type **Module JavaScript** :

```text
/alfea-synoptique/pac-synoptique-card.js?v=1.5.14
```

### Éditeur visuel (nouveau en V1.5.7)

Une fois le module JavaScript chargé, la carte **PAC Synoptique** apparaît dans
le sélecteur de cartes Lovelace. Dans **Modifier la carte**, l'onglet éditeur
visuel propose :

- **Apparence** : Automatique (thème Home Assistant), Clair, Sombre.
- **Afficher les diagnostics complémentaires** : oui/non.

Les réglages sont enregistrés comme configuration normale du dashboard,
sans éditer le YAML. Le synoptique n'ajoute aucune commande PAC. Les alarmes
et leur nombre restent visibles et repliables quelle que soit l'option.

L'onglet **Disposition** standard de Home Assistant permet d'adapter la
largeur de la carte ; le rendu horizontal reste responsive.

### Configuration YAML facultative

Dans le YAML d'une carte manuelle :

```yaml
type: custom:pac-synoptique-card
title: Atlantic Alféa Extensa Duo
show_diagnostics: true
grid_options:
  columns: full
  rows: auto
theme_mode: auto  # auto (défaut), light, dark
```

**Thèmes :** `theme_mode: auto` reprend les couleurs du thème Home Assistant
et suit son basculement clair/sombre. Si souhaité, `theme_mode: light` impose une
carte claire, et `theme_mode: dark` impose le graphisme sombre d'origine.
Cette option est purement visuelle, sans effet sur les consignes ou la régulation.

**Migration depuis la carte installée manuellement :** supprimez l'ancienne
ressource `/local/pac-synoptique-card.js?v=...` afin de ne pas charger
deux versions de `pac-synoptique-card`. La configuration YAML ne change pas.

La carte ne contient aucun appel de service Home Assistant et **ne commande pas
la PAC**. Les couleurs/animations restent indicatives : pas de débitmètre,
pas de pression frigorifique ni de puissance instantanée inventés.
Voir [la documentation synoptique](docs/SYNOPTIQUE_V155.md).

## Régime Confort / Éco (affichage uniquement)

Les diagnostics BSB-LAN natifs `10112` (C1) et `10122` (C2) sont
utilisés en priorité pour afficher le programme appliqué :
**1 = Allure Réduit / Éco**, **2 = Allure Confort**.
En leur absence, le libellé de l'état BSB est consulté puis
`indéterminé` est conservé si les données ne suffisent pas.
L'état de régulation (`8000/8001`) et le régime horaire sont deux
informations distinctes : `122 - Limitation de la température ambiante`
ne veut **pas** dire Éco en soi.

**Sécurité :** cette nouvelle lecture sert exclusivement à l'affichage.
Les méthodes de choix de consigne et les dérogations natives existantes restent inchangées.

## Dérogation native

La V1.5.0 utilise les dérogations natives du régulateur pour les modifications temporaires demandées depuis les entités Climate, sans réécrire les consignes Confort / Éco ni les horaires.

- **Chauffage :** dérogation vers une température **plus chaude** ou **plus froide** sur chacun des deux circuits.
- **Rafraîchissement :** dérogation vers une température **plus froide**, selon le comportement validé en V1.3.3.
- **Amplitude :** écart de **0,1 à 5 °C** par rapport à la consigne effective au moment de la commande.
- **Durée :** configurée pour chaque circuit et gérée directement par le régulateur ; retour automatique à la programmation normale à l'expiration.
- **Annulation :** bouton dédié à chaque circuit lorsque les paramètres nécessaires sont disponibles en écriture.

Les paramètres personnalisés d'écart `10991` et `10993` peuvent ne pas renvoyer de valeur lisible, même après écriture : cela ne signifie pas nécessairement que la dérogation a échoué. L'état de dérogation (`701` / `1001`) et les consignes effectives (`8741` / `8771`) permettent d'en contrôler les effets.

**Validation :** les dérogations chauffage et leur expiration après une heure ont été testées sur les deux circuits avec la V1.4.0-beta.5. La commutation saisonnière réelle depuis le mode global de la V1.5.0 reste à confirmer sur l'installation.

## Philosophie de fonctionnement

La programmation horaire reste gérée par la PAC. L'intégration ne remplace pas le programmateur du régulateur et conserve la PAC comme source de vérité pour les régimes Confort / Réduit.

Le **mode global** commande les deux circuits à la fois : **Chauffage** active C1 et C2 en chauffage ; **Refroidissement** active les deux en rafraîchissement ; **Off** arrête les deux circuits. Après une commande globale, chaque circuit peut de nouveau être piloté indépendamment depuis sa carte Climate. La transition de saison est effectuée en désactivant d'abord le mode opposé, puis en activant le mode demandé, avec confirmation des états BSB-LAN. La commutation saisonnière physique doit encore être validée sur la PAC.

## Prérequis

- Home Assistant avec MQTT fonctionnel.
- Une passerelle **BSB-LAN** déjà intégrée à Home Assistant.
- Les paramètres BSB nécessaires publiés sous forme d'entités Home Assistant.

L'intégration détecte automatiquement les paramètres connus. Les paramètres obligatoires qui ne peuvent pas être associés sans ambiguïté sont demandés pendant la configuration.

## Installation via HACS (dépôt personnalisé)

Le dépôt est compatible avec HACS en tant que **Custom Repository**.

1. Dans Home Assistant, ouvrez **HACS**.
2. Ouvrez le menu **⋮** en haut à droite puis **Custom repositories**.
3. Ajoutez l'URL du dépôt :

   `https://github.com/Jrmysmallstep/home-assistant-atlantic-alfea-bsb-lan`

4. Sélectionnez le type **Integration**.
5. Cliquez sur **Add**.
6. Recherchez ensuite **Atlantic Alfea BSB-LAN** dans HACS et installez l'intégration.
7. Redémarrez Home Assistant après l'installation.
8. Ouvrez **Paramètres → Appareils et services → Ajouter une intégration** puis recherchez **Atlantic Alfea BSB-LAN**.

HACS installera automatiquement l'intégration dans `custom_components/atlantic_alfea_controller/`.

## Documentation BSB-LAN

La documentation officielle BSB-LAN est la référence principale pour l'installation, la configuration de la passerelle et la compréhension des paramètres du bus :

- **Documentation BSB-LAN en français :** https://docs.bsb-lan.de/fr/index.html

Les numéros de paramètres et leur disponibilité peuvent varier selon le régulateur, le firmware et la configuration de l'installation. En cas de doute, vérifiez toujours le paramètre concerné dans la documentation BSB-LAN et directement sur votre régulateur.

## Installation manuelle

Si vous ne souhaitez pas utiliser HACS :

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
| Durée dérogation (paramètre personnalisé) | 10990 | 10992 |
| Écart dérogation (paramètre personnalisé) | 10991 | 10993 |
| Régime temporaire (diagnostic) | 10110 | 10120 |
| Programme horaire actif (diagnostic) | 10112 | 10122 |

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

## Diagnostics de programmation (V1.5.0)

Quatre nouveaux capteurs **en lecture seule** complètent la surveillance des circuits :

| Entité affichée | Paramètre BSB-LAN | Information |
|---|---:|---|
| C1 - Régime temporaire | `10110` | Régime temporaire du circuit 1 |
| C2 - Régime temporaire | `10120` | Régime temporaire du circuit 2 |
| C1 - Programme actif | `10112` | Allure actuellement appliquée (Confort / Réduit) |
| C2 - Programme actif | `10122` | Allure actuellement appliquée (Confort / Réduit) |

Ces valeurs dépendent de la disponibilité et de la publication des paramètres par BSB-LAN. Les capteurs ne changent jamais les programmes horaires.

## Mise à jour des données

L'intégration demande périodiquement à BSB-LAN de republier certains diagnostics qui doivent rester frais :

- `8411` toutes les 5 minutes ;
- `3113`, `8450` et `8451` toutes les 15 minutes ;
- l'horloge (`0`) une fois par heure.

Ces demandes sont des lectures et ne modifient pas les réglages de la PAC.

## Avertissement

Projet communautaire non officiel, sans affiliation avec Atlantic ou le projet BSB-LAN. Les comportements de certains paramètres peuvent varier selon les variantes du régulateur. Le changement de saison et le nouveau mode global nécessitent encore une validation complète sur l'installation réelle ; les tests automatiques ne remplacent pas les essais sur la PAC.
