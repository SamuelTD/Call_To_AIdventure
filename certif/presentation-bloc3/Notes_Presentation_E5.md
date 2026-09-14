# Notes orales — Presentation_E5

Personnaliser identité, commanditaire, rôle, dates, budget et preuves externes avant passage.

## 01. Surveiller et résoudre un incident technique — 75 s

Le référentiel accepte un contexte réel ou fictif avec erreur technique. Ici, la cause et le correctif sont historiques ; la reproduction a été réalisée le 14 septembre 2026 pour la soutenance. Ne pas inventer une alerte utilisateur, un ticket, une date de découverte ou un impact de production. Le dossier joint précise le périmètre de la reconstruction.

Sources : Référentiel, p. 17 et 22–23 ; Dossier_incident_E5.md

## 02. Observer le parcours complet du joueur — 75 s

La durée navigateur ne couvre que les retours de récit avec choix utilisables : combats, fins et erreurs sont exclus. Ce n’est donc pas une latence de toutes les requêtes. Le format des logs est du texte à champs, pas du JSON. Les exceptions peuvent produire du contenu sensible ; ne pas déclarer une anonymisation universelle. La stack n’a pas été démarrée pour ces slides.

Sources : docs/monitoring.md ; settings.py ; src/observability/metrics.py

## 03. Les alertes techniques ne détectent pas tout — 75 s

La règle indisponibilité opère par série, sans somme explicite ; ne pas la présenter comme un total global agrégé. Pour l’incident d’isolation, proposer un contrôle synthétique ou un compteur d’invariants, mais le nommer comme amélioration future. Les règles de seuil existent ; leur déclenchement et leur livraison doivent encore être montrés dans un bac à sable.

Sources : monitoring/prometheus/alerts.yml ; monitoring/alertmanager/alertmanager.yml

## 04. L’ancienne version attaque le mauvais monstre — 75 s

Expliquer l’imbrication plutôt qu’une concurrence supposée mesurée : restaurer A, restaurer B, puis reprendre l’attaque initiée pour A. Le script lit la version parent du correctif et l’exécute dans un module isolé. Il ne change ni la branche, ni le code du jeu, ni les bases. Ce n’est pas un test de charge HTTP multi-thread.

Sources : reproduce_incident.py ; preuves/incident-combat.json

## 05. Un état global partage une identité implicite — 75 s

La preuve de cause est le code historique et sa reproduction. Écarter l’hypothèse d’un calcul de dégâts erroné : les dégâts sont fixes et corrects, mais appliqués à la mauvaise référence. L’ancien adaptateur restaurait bien l’état avant l’action ; cela ne protégeait pas contre une autre restauration intercalée.

Sources : Git : parent de 8a3cf39, src/combat/core.py ; diff game_engine.py

## 06. Passer le combat explicitement aux fonctions — 75 s

Décrire la correction telle qu’elle existe, sans s’en attribuer une réalisation aujourd’hui. Le changement historique est dans un commit plus large, pas dans une PR dédiée à cet incident. Il reste des limites de concurrence sur le graphe ou des requêtes visant une même sauvegarde ; la correction ne prouve pas que toute l’application est thread-safe.

Sources : src/combat/core.py ; services/game_engine.py ; commit 8a3cf39

## 07. Le même scénario touche désormais le bon état — 75 s

Le script avant/après et le test Django ne sont pas identiques : le premier reproduit une imbrication au niveau des fonctions cœur ; le second exécute successivement des actions sur deux états et vérifie leurs HP. Les deux se complètent. Ne pas appeler cela un benchmark concurrent ni une preuve de réparation des parties historiques.

Sources : preuves/incident-combat.json ; game.tests.CombatEngineTests

## 08. Relier le correctif à l’exploitation — 75 s

Conclure sur une cause comprise, un correctif versionné et un résultat vérifié. Le document rédigé aujourd’hui n’est pas un ticket créé au moment de l’incident. La boucle d’amélioration ajuste l’application et ses tests ; elle n’entraîne pas automatiquement le modèle de génération. Utiliser les annexes pour les commandes et questions.

Sources : Dossier_incident_E5.md ; preuves/verification.md

## 09. Rejouer les preuves sans toucher au jeu — 0 s

Les lignes des cartes sont coupées pour projection ; copier les commandes complètes depuis le dossier. La reproduction requiert l’historique Git contenant le parent de 8a3cf39. Aucun git switch, reset ou retour de base n’est nécessaire.

Sources : reproduce_incident.py ; preuves/verification.md

## 10. Retrouver les pièces du dossier — 0 s

Ne pas confondre le modèle de diagramme C4 avec la compétence C4 du bloc 1. Les références au référentiel concernent les PDF locaux fournis. Compléter aussi l’identité, les dates, le budget, l’hébergement et l’audit manuel demandés par le dossier de certification.

Sources : docs/block3/ ; docs/monitoring.md ; Dossier_incident_E5.md

## 11. Expliquer les frontières de la preuve — 0 s

Préparer également : distinction CI/CD, copie de l’état versus isolation, mise à jour concurrente d’une même partie, limites du health, protection des journaux et rollback de migrations. Montrer la preuve adaptée plutôt que généraliser les résultats du lot ciblé.

Sources : preuves/verification.md ; docs/block3/README.md
