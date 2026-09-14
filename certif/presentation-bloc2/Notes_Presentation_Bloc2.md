# Notes orales — Presentation_Bloc2

Personnaliser identité, commanditaire, rôle, dates, budget et preuves externes avant passage.

## 01. Choisir et configurer le service d’IA — 90 s

Présenter votre identité, votre rôle exact et le commanditaire. E2 dure 15 minutes ; E3 suit pendant 20 minutes, puis le bloc prévoit 10 minutes de questions. Le rapport professionnel reste distinct de ce support. Le choix du service doit être défendu par des preuves, pas uniquement par son utilisation dans le code.

Sources : Référentiel 2023, p. 6–9 ; règlement, p. 12

## 02. Raconter, proposer, agir : trois contrats — 90 s

Illustrer avec une porte fermée : la narration décrit la situation, le modèle propose trois actions, puis le joueur en choisit une. Le modèle ne doit pas inventer directement les nouvelles statistiques. Les schémas imposent une forme, pas la pertinence narrative ou la langue : celles-ci nécessitent une évaluation distincte.

Sources : docs/block2/ai-requirements-and-selection.md ; src/agents/schemas.py

## 03. Définir la réussite avant de comparer — 90 s

Expliquer p95 : 95 % des observations sont sous cette durée sur une fenêtre définie. Ne pas confondre timeout d’un appel et durée totale d’un tour, qui peut contenir plusieurs appels et reprises. Budget, volume réel et arbitrage final ne sont pas fournis. Le taux de 90 % exige un corpus représentatif et une notation adaptée.

Sources : docs/block2/ai-requirements-and-selection.md ; ai-test-strategy.md

## 04. Une veille à rattacher aux décisions — 90 s

Le référentiel demande au minimum une heure hebdomadaire. Le document de diagnostic renvoie C6 à un dossier séparé : son absence dans ce dépôt ne prouve pas que vous ne l’avez pas réalisé ailleurs. Insérer vos dates, outils, sources identifiées, synthèses et destinataires. Cette slide est une trame, pas une veille effectivement conduite ni un état de l’art actualisé.

Sources : Référentiel, C6, p. 6–8 ; certif/block-2-technical-gap-analysis.md

## 05. Comparer sur un protocole identique — 90 s

Pour chaque candidat, relever version, date, validité, qualité FR/EN, p50/p95, tokens, coût estimé, région de traitement et rétention. Inclure les informations disponibles sur la démarche écoresponsable. Expliciter les services non étudiés et pourquoi. Ce support ne remplace pas le benchmark exigé par C7 ; aucune invocation payante n’a été réalisée.

Sources : docs/block2/ai-requirements-and-selection.md

## 06. Une génération hébergée, un RAG local — 90 s

La justification actuelle vise la génération multilingue et structurée sans héberger un gros modèle, un petit corpus vectoriel local et des transitions explicites. Le lore retrouvé est injecté dans les prompts envoyés au service de génération : rendre ce flux clair. Ne pas présenter cette décision qualitative comme un benchmark déjà conclu.

Sources : docs/block2/ai-requirements-and-selection.md ; docs/rag-system.md

## 07. Rendre la configuration explicite — 90 s

Lire les valeurs réellement configurées avant démonstration. Le nom du modèle par défaut est une chaîne du dépôt, pas une vérification de disponibilité commerciale. La commande check_ai_services valide les paramètres ; son option --connect vérifie Ollama, pas une génération réelle du fournisseur. Ne jamais afficher le fichier .env.

Sources : src/agents/runtime_config.py ; .env.example

## 08. Préparer le contexte avant la génération — 90 s

Le dry-run exécuté prépare 36 fragments de personnages et 21 de lieux. La documentation ancienne annonce 39 : la mesure du code courant prime. Aucun serveur Ollama ni Chroma n’a été testé en ligne ici. L’objectif de rappel des sources doit être mesuré séparément ; le runner actuel ne le calcule pas.

Sources : src/retrieval/ ; vérification du 14/09/2026

## 09. Maîtriser coûts, données et dépendances — 90 s

La formule complète utilise des tarifs par million de tokens : diviser la consommation par un million et distinguer entrée/sortie. Aucun tarif actuel n’est avancé. Les coûts estimés ne sont pas une facture. Éviter d’affirmer qu’un modèle local est automatiquement moins cher ou plus sobre ; cela dépend du matériel et des usages.

Sources : docs/block2/ai-requirements-and-selection.md ; docs/rag-system.md

## 10. Une solution configurée, une sélection à étayer — 90 s

Rappeler ce qui fonctionne dans le code et ce qui reste à montrer en réel. Préparer une démonstration safe de configuration et une sortie structurée issue d’un vrai appel, en conservant modèle, date et contexte d’évaluation. Le bilan ne prétend pas valider toutes les compétences E2.

Sources : docs/block2/evidence-checklist.md

## 11. Mettre le composant d’IA en service — 100 s

Introduire E3 de façon autonome si ce fichier est présenté séparément. Il s’agit de mettre en service un modèle préexistant dans une application, pas d’entraîner ses poids. Expliquer ce qui est versionné localement et ce qui dépend du fournisseur distant.

Sources : Référentiel, C9–C13, p. 10–16 ; docs/block2/traceability.md

## 12. Exposer trois points d’entrée documentés — 100 s

Le health renvoie des booléens, pas un ping fournisseur. Décrire le body {"choice": "Open the gate"}. L’API réutilise StepGameView pour déclencher le moteur. Le contrat YAML existe, mais quelques écarts contrat/code sont identifiés en annexe et ne doivent pas être présentés comme une conformité OpenAPI parfaite.

Sources : src/django/game/ai_api.py ; docs/block2/openapi.yaml

## 13. Contrôler avant de solliciter le modèle — 100 s

Résultats vérifiés : utilisateur étranger rejeté, choix arbitraire rejeté avec liste renseignée, CSRF refusé sans jeton et quota exercé. Limite importante : le code ne rejette pas par ce contrôle un choix lorsque current_choices est vide. Ne pas affirmer une prévention générale des injections de prompt. Ne pas montrer d’identifiants de session réels.

Sources : src/django/game/ai_api.py ; src/django/game/test_ai_api.py

## 14. Relier l’interface au moteur narratif — 100 s

Éviter un schéma trompeur qui ferait passer le navigateur par v1 : le template pointe vers api_step. L’intégration effective du fournisseur passe par les chaînes du moteur ; v1 expose une autre frontière. Une preuve C10 complète doit montrer les endpoints réellement consommés et les adaptations d’interface, avec leur évaluation d’accessibilité.

Sources : src/django/game/templates/game/play.html ; ai_api.py ; services/game_engine.py

## 15. Valider la forme et protéger la progression — 100 s

Les tests ciblés ont exercé les prompts FR, la reprise narrative, l’échec sans progression, les outils de soin et les objectifs. La classe SaveGamePersistenceTests n’appartient pas au lot de 33 exécuté ici : ne pas attribuer à ce lot la totalité des tests de persistance. Les cas sont simulés ; aucune qualité linguistique en réel n’est mesurée.

Sources : src/agents/schemas.py ; src/django/game/tests.py

## 16. Observer disponibilité, qualité et coût — 100 s

Expliquer compteur et histogramme, ainsi que la fenêtre de calcul. Les métriques exposées ont des tests ciblés, mais la chaîne Prometheus/Grafana n’a pas été lancée pour ce support. Les tokens peuvent dépendre des données d’usage fournies par le service ; l’estimation de coût nécessite des tarifs à jour. Les labels bornés évitent données sensibles et cardinalité excessive.

Sources : src/observability/ ; docs/block2/monitoring-slos.md ; monitoring/

## 17. Transformer un signal en action — 100 s

Le seuil précis de RAG documenté est plus de deux échecs en quinze minutes. La latence doit être élevée pendant dix minutes. Préparer un déclenchement contrôlé en bac à sable avec capture horodatée et retour à la règle initiale. Ce projet ajuste l’intégration ; il ne réentraîne pas automatiquement le modèle distant.

Sources : docs/block2/monitoring-slos.md ; monitoring/alertmanager/

## 18. Distinguer tests logiciels et évaluation IA — 100 s

Point central : validate_dataset vérifie version, identifiants et types de tâches ; ce n’est pas une validation exhaustive du contenu. En live, passed=True signifie ici passage de la chaîne et de ChoiceOutput. Les seuils 1,0 et 0,9 sont écrits dans le rapport ; le code de sortie exige tous les résultats passed. Ne pas annoncer 100 % de qualité à partir de validated_offline.

Sources : src/evaluation/runner.py ; evaluation/dataset.json

## 19. 33 tests ciblés réussis — 100 s

Nommer les classes exécutées, disponibles dans le fichier de preuve. Les 33 tests sont un sous-ensemble, pas toute la suite ni une mesure de couverture. Le résultat de 3,711 s est la durée des tests, jamais une latence d’inférence. Aucune suite API complète ou audit de sécurité ne doit être revendiqué à partir de ce lot.

Sources : preuves/evaluation-offline.json ; preuves/verification.md

## 20. Automatiser les contrôles avant livraison — 100 s

Décrire PR, push main et déclenchement manuel. Le conteneur est construit et chargé localement dans le job : le workflow ne prouve pas la publication d’une image dans un registre. Le smoke test utilise une clé factice et RAG désactivé ; il vérifie le démarrage HTTP, pas le modèle. La couverture 55 % est un seuil configuré, pas une mesure obtenue aujourd’hui.

Sources : .github/workflows/block2-ai.yml ; docs/block2/delivery.md

## 21. Promouvoir un artefact, prévoir le retour arrière — 100 s

Garder au moins un artefact connu bon. Le modèle hébergé peut évoluer si son identifiant n’est pas une version figée ; expliciter cette limite. Versionner une collection RAG fait partie de la procédure à organiser, pas d’une preuve d’activation déjà produite ici. Staging, registre et liens de jobs restent à renseigner.

Sources : docs/block2/delivery.md ; src/evaluation/runner.py

## 22. Montrer une preuve à chaque frontière — 100 s

Les manipulations tiennent dans le créneau de cette slide si les onglets sont prêts. Sans service démarré, montrer les preuves hors ligne et nommer explicitement ce qui est une simulation. Ne pas déclencher un appel payant ou envoyer une notification à un tiers par surprise. Préparer l’audit d’accessibilité et les liens de démonstration avant la soutenance.

Sources : docs/block2/evidence-checklist.md ; Notes_orales_Bloc2.md

## 23. Écarts repérés entre contrat et code — 0 s

Ces observations proviennent du code local, sans test d’exploitation. Le lot courant couvre une liste de choix non vide. Ajouter des tests de contrat et corriger les écarts avant de revendiquer une conformité stricte. Ce support ne change pas le périmètre de la demande en tâche de développement.

Sources : docs/block2/openapi.yaml ; src/django/game/ai_api.py

## 24. Retrouver les preuves C6 à C13 — 0 s

Les chemins des cartes sont abrégés pour projection. Utiliser les notes et le dépôt pour ouvrir les fichiers exacts. Le référentiel local fourni est la base de ce support ; aucune affirmation n’est faite sur une éventuelle version plus récente de la certification.

Sources : Référentiel fourni, p. 6–16 ; docs/block2/traceability.md

## 25. Défendre les limites du dispositif — 0 s

Préparer aussi : confidentialité du contexte envoyé, timeout par appel versus tour complet, quota multi-instance, limite des schémas et stabilité des modèles hébergés. Rester précis sur l’absence d’entraînement ou de réentraînement dans ce projet.

Sources : docs/block2/evidence-checklist.md ; src/evaluation/runner.py
