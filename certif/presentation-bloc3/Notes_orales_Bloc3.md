# Notes orales — Presentation_Bloc3

Personnaliser identité, commanditaire, rôle, dates, budget et preuves externes avant passage.

## 01. Construire une application intégrant l’IA — 100 s

Présenter identité, rôle, commanditaire et contexte scolaire. Le passage isolé du bloc prévoit E4 20 minutes, E5 10 minutes, puis 10 minutes de questions. Personnaliser les contributions réelles et les éventuelles aides reçues. Les slides ne remplacent pas le rapport E4 ni les documentations E5.

Sources : Référentiel 2023, p. 16–21 ; règlement, p. 12

## 02. Permettre de jouer et de retrouver sa progression — 100 s

Expliquer les acteurs et la valeur du service avant la technologie. La session anonyme n’offre pas la même reprise durable qu’une sauvegarde authentifiée. Le commanditaire et les contraintes de volume/budget restent à confirmer dans le document de cadrage ; ne pas les inventer.

Sources : docs/block3/project-brief-requirements.md

## 03. Transformer le besoin en critères vérifiables — 100 s

Relier FR-10 à SaveGame, NFR-06 aux filtres de propriétaire et NFR-07 à la frontière de persistance. Les critères d’accessibilité doivent être intégrés aux user stories et associés à un standard choisi. Une cible WCAG/RGAA documentée n’est pas une conformité auditée.

Sources : docs/block3/traceability.md ; project-brief-requirements.md

## 04. Séparer présentation, métier et persistance — 100 s

Présenter une architecture en couches, pas des microservices déployés qui n’existent pas. Les appels de génération transmettent le contexte utile au service distant. Les secrets restent dans l’environnement. Le schéma est une vue simplifiée ; les modèles du dossier détaillent les flux et les zones de stockage.

Sources : docs/block3/technical-framework-models.md ; services/game_engine.py

## 05. Choisir une architecture adaptée au périmètre — 100 s

Défendre chaque choix avec ses alternatives et ses conséquences. Ne pas appeler l’environnement local une préproduction déployée. Le référentiel C15 attend une preuve de concept accessible en préproduction et une conclusion de poursuite ; joindre cette preuve. Les critères de sobriété des prestataires restent à compléter lorsque le choix est arrêté.

Sources : docs/block3/architecture-decisions.md ; technical-framework-models.md

## 06. Piloter un projet solo avec des critères explicites — 100 s

Le dépôt décrit une démarche légère solo avec assistance outillée. Ne pas revendiquer une équipe Scrum, des cérémonies ou des échanges non attestés. Personnaliser calendrier, temps investi, imprévus et arbitrages. Les documents proposent une définition de prêt et de terminé ; l’historique des revues reste à enrichir.

Sources : docs/block3/agile-execution.md ; historique Git

## 07. Conserver une progression cohérente — 100 s

Décrire comment une vue délègue au moteur puis décide de persister. Les tests de sauvegarde couvrent l’échec du service IA, les fins de partie et la propriété. Le jeu implique des tirages aléatoires, mais ces règles ne sont pas décidées par le modèle ; les tests contrôlent l’aléatoire pour vérifier les résultats.

Sources : src/django/game/models.py ; services/ ; tests.py

## 08. Protéger les requêtes et les données du joueur — 100 s

Le test CSRF exécuté utilise api_play comme route représentative ; ne pas affirmer qu’il teste individuellement chaque POST. D’autres contrôles testent 413, quota et propriété. Les anciennes notes bloc 1/2 mentionnent encore des exemptions CSRF ; les documents bloc 3 et le code courant décrivent leur migration. Aucun audit global OWASP n’est revendiqué.

Sources : docs/block3/security-threat-model.md ; game/views.py ; tests.py

## 09. Rendre les interactions perceptibles et maîtrisées — 100 s

Les tests exécutés lisent des templates ou leurs réponses HTML ; ils ne font pas fonctionner un lecteur d’écran ni le JavaScript dans un navigateur. L’écoconception repose sur des pratiques, sans score environnemental mesuré. Le dépôt mentionne une ancienne taille Docker : elle n’a pas été revérifiée et n’est pas affichée comme résultat actuel.

Sources : docs/block3/product-quality-audit.md ; ProductQualityTemplateTests

## 10. 44 tests ciblés réussis sur le bloc applicatif — 100 s

Le lot a terminé en 6,091 secondes : c’est une durée de tests, pas une performance de l’application. BrowserSmokeJourneyTests utilise le client Django et un moteur simulé, sans navigateur réel. Le seuil de couverture configuré reste 55 %, mais la couverture n’a pas été recalculée pour ce support. Aucune exécution CI distante n’a été consultée.

Sources : preuves/verification.md ; .github/workflows/block3-ci-cd.yml

## 11. Construire, vérifier et conserver le même artefact — 100 s

Le job staging-deploy-placeholder affiche des instructions : il n’y a aucune commande de déploiement effectif. Ne pas assimiler permission packages:write à une publication d’image. Le health de conteneur utilise une clé factice dans le workflow et ne prouve pas une génération IA. Joindre digest, URL de staging et preuve de rollback réels avant de revendiquer la chaîne complète.

Sources : .github/workflows/block3-ci-cd.yml ; Dockerfile ; docs/block3/ci-cd-delivery.md

## 12. Montrer le parcours, puis les garanties — 100 s

Les autres slides sont également prévues sur 100 secondes, soit E4 en 20 minutes. Préparer les onglets, une sauvegarde de test et le contexte sans données réelles. Une capture du produit n’a pas été créée pendant ce travail. La démonstration manuelle complète et la génération réelle nécessitent l’environnement configuré ; les tests seuls ne les remplacent pas.

Sources : docs/block3/traceability.md ; preuves/verification.md

## 13. Surveiller et résoudre un incident technique — 75 s

Le référentiel accepte un contexte réel ou fictif avec erreur technique. Ici, la cause et le correctif sont historiques ; la reproduction a été réalisée le 14 septembre 2026 pour la soutenance. Ne pas inventer une alerte utilisateur, un ticket, une date de découverte ou un impact de production. Le dossier joint précise le périmètre de la reconstruction.

Sources : Référentiel, p. 17 et 22–23 ; Dossier_incident_E5.md

## 14. Observer le parcours complet du joueur — 75 s

La durée navigateur ne couvre que les retours de récit avec choix utilisables : combats, fins et erreurs sont exclus. Ce n’est donc pas une latence de toutes les requêtes. Le format des logs est du texte à champs, pas du JSON. Les exceptions peuvent produire du contenu sensible ; ne pas déclarer une anonymisation universelle. La stack n’a pas été démarrée pour ces slides.

Sources : docs/monitoring.md ; settings.py ; src/observability/metrics.py

## 15. Les alertes techniques ne détectent pas tout — 75 s

La règle indisponibilité opère par série, sans somme explicite ; ne pas la présenter comme un total global agrégé. Pour l’incident d’isolation, proposer un contrôle synthétique ou un compteur d’invariants, mais le nommer comme amélioration future. Les règles de seuil existent ; leur déclenchement et leur livraison doivent encore être montrés dans un bac à sable.

Sources : monitoring/prometheus/alerts.yml ; monitoring/alertmanager/alertmanager.yml

## 16. L’ancienne version attaque le mauvais monstre — 75 s

Expliquer l’imbrication plutôt qu’une concurrence supposée mesurée : restaurer A, restaurer B, puis reprendre l’attaque initiée pour A. Le script lit la version parent du correctif et l’exécute dans un module isolé. Il ne change ni la branche, ni le code du jeu, ni les bases. Ce n’est pas un test de charge HTTP multi-thread.

Sources : reproduce_incident.py ; preuves/incident-combat.json

## 17. Un état global partage une identité implicite — 75 s

La preuve de cause est le code historique et sa reproduction. Écarter l’hypothèse d’un calcul de dégâts erroné : les dégâts sont fixes et corrects, mais appliqués à la mauvaise référence. L’ancien adaptateur restaurait bien l’état avant l’action ; cela ne protégeait pas contre une autre restauration intercalée.

Sources : Git : parent de 8a3cf39, src/combat/core.py ; diff game_engine.py

## 18. Passer le combat explicitement aux fonctions — 75 s

Décrire la correction telle qu’elle existe, sans s’en attribuer une réalisation aujourd’hui. Le changement historique est dans un commit plus large, pas dans une PR dédiée à cet incident. Il reste des limites de concurrence sur le graphe ou des requêtes visant une même sauvegarde ; la correction ne prouve pas que toute l’application est thread-safe.

Sources : src/combat/core.py ; services/game_engine.py ; commit 8a3cf39

## 19. Le même scénario touche désormais le bon état — 75 s

Le script avant/après et le test Django ne sont pas identiques : le premier reproduit une imbrication au niveau des fonctions cœur ; le second exécute successivement des actions sur deux états et vérifie leurs HP. Les deux se complètent. Ne pas appeler cela un benchmark concurrent ni une preuve de réparation des parties historiques.

Sources : preuves/incident-combat.json ; game.tests.CombatEngineTests

## 20. Relier le correctif à l’exploitation — 75 s

Conclure sur une cause comprise, un correctif versionné et un résultat vérifié. Le document rédigé aujourd’hui n’est pas un ticket créé au moment de l’incident. La boucle d’amélioration ajuste l’application et ses tests ; elle n’entraîne pas automatiquement le modèle de génération. Utiliser les annexes pour les commandes et questions.

Sources : Dossier_incident_E5.md ; preuves/verification.md

## 21. Rejouer les preuves sans toucher au jeu — 0 s

Les lignes des cartes sont coupées pour projection ; copier les commandes complètes depuis le dossier. La reproduction requiert l’historique Git contenant le parent de 8a3cf39. Aucun git switch, reset ou retour de base n’est nécessaire.

Sources : reproduce_incident.py ; preuves/verification.md

## 22. Retrouver les pièces du dossier — 0 s

Ne pas confondre le modèle de diagramme C4 avec la compétence C4 du bloc 1. Les références au référentiel concernent les PDF locaux fournis. Compléter aussi l’identité, les dates, le budget, l’hébergement et l’audit manuel demandés par le dossier de certification.

Sources : docs/block3/ ; docs/monitoring.md ; Dossier_incident_E5.md

## 23. Expliquer les frontières de la preuve — 0 s

Préparer également : distinction CI/CD, copie de l’état versus isolation, mise à jour concurrente d’une même partie, limites du health, protection des journaux et rollback de migrations. Montrer la preuve adaptée plutôt que généraliser les résultats du lot ciblé.

Sources : preuves/verification.md ; docs/block3/README.md
