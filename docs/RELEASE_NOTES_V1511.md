# Atlantic Alféa BSB-LAN V1.5.11

- Restauration du comportement original des capteurs « C1 - État actuel » et « C2 - État actuel » : lecture du régulateur BSB-LAN natif, en fonction de la saison (8000/8001 en chauffage, 8004/8025 en refroidissement), sans interprétation basée sur les circulateurs.
- La pastille de chaque circuit sur la carte affiche directement la valeur de son capteur « État actuel ».
- Circulateurs C1 (9031 / QX1) et C2 (8760) affichés en lecture seule dans Diagnostics et Capteurs complémentaires, sans les substituer au régime natif.
- Synoptique horizontal prioritaire et compact lorsque nécessaire ; repli vertical sous largeur disponible réduite avec connexions visibles et animées entre COMP, PAC et distribution vers C1, C2, ECS.
- Climate, commandes, consignes, programmation native et dérogations PAC inchangés.
- Après installation HACS, redémarrer Home Assistant et recharger complètement le navigateur (cache de la carte JavaScript).
